import json
import os
import schedule
from threading import Thread
from flask import Flask, render_template, request, jsonify, g, send_from_directory, make_response
from loguru import logger
from dbHelper import DBHelper
from task import Task
from timingTask import TimingTask
from utils import TimerCache, ranstr, save_file, SITE_CONFIG
import shutil
import datetime
import re
app = Flask(__name__)
task = Task()
timerCache = TimerCache()
timingTask = TimingTask()
logger.add('err.log', level="ERROR")


@app.route('/image/<path:path>')
def send_image_file(path):
    return send_from_directory('cache', path, mimetype='image/png')


@app.route('/')
def index():
    uid = request.args.get('uid')
    cuid = request.cookies['uid'] if 'uid' in request.cookies else None
    res = {
        "site": SITE_CONFIG
    }
    with DBHelper() as db:
        res['list'] = db.query_comic(uid or cuid or 'admin')
    resp = make_response(render_template(
        'index.html', data=json.dumps(res, ensure_ascii=False)))
    if (cuid is None):
        resp.set_cookie("uid", uid or 'admin', max_age=30 * 60 * 60 * 24)
    return resp


@app.route('/search')
def search():
    keyword = request.args.get('keyword')
    origin = request.args.get('origin')
    page_num = request.args.get('page_num') or 1
    cachekey = f'{keyword}:{page_num}'
    res = timerCache.get(cachekey)
    if res is None:
        cfg = SITE_CONFIG[origin]['action']['search']
        url = cfg['url'].format(keyword=keyword, page_num=page_num)
        task.set_task([{
            "url": url,
            "js_init": cfg['js_init'].format(page_num=page_num),
            "js_result": cfg['js_result'].format(page_num=page_num)
        }])
        res = task.get_result()[0]
        timerCache.add(cachekey, res)
    return render_template('search.html', data=json.dumps(res, ensure_ascii=False))


@app.route('/comic_preview')
def preview():
    url = request.args.get('url')
    origin = re.findall(r'^https?://[^/]+', url)[0]
    if origin not in SITE_CONFIG:
        return jsonify({'msg': 'URL未支持', 'result': False}) 
    cfg = SITE_CONFIG[origin]['action']['comic']
    res = timerCache.get(url)
    if res is None:
        task.set_task([{
            'type': "preview",
            "url": url,
            "js_init": cfg['js_init'],
            "js_result": cfg['js_result']
        }])
        res = task.get_result()[0]
        timerCache.add(url, res)
    return render_template('preview.html', data=json.dumps(res, ensure_ascii=False))


@app.route('/comic')
def comic():
    id = request.args.get('id')
    with DBHelper() as db:
        res = db.query_by_id('comic', id)[0]
        res['chapters'] = db.query_chapter_by_id(res['id'])
    return render_template('comic.html', data=json.dumps(res, ensure_ascii=False))


@app.route('/chapter')
def chapter():
    id = request.args.get('id')
    with DBHelper() as db:
        res = db.query_by_id('chapter', id)[0]
        db.update_by_id('chapter', id, last_access=datetime.datetime.now())
    return render_template('chapter.html', data=json.dumps(res, ensure_ascii=False))


@app.route('/sync_now')
def sync_now():
    def sync():
        timingTask.sync_chapter()
        return schedule.CancelJob
    schedule.every(0).seconds.do(sync)
    return jsonify({'msg': 'ok', 'result': True})


@app.route('/subscribe', methods=['POST'])
def subscribe():
    formdata = request.form
    comic = timerCache.get(formdata.get('url'))
    if comic is None:
        return jsonify({'msg': 'cache timeout', 'result': False})

    ignore_index = int(formdata.get('ignore_index') or 0)
    with DBHelper() as db:
        comic_id = db.subscribe_comic(
            title=comic['title'],
            author=comic['author'],
            page_url=comic['page_url'],
            origin=comic['origin'],
            last_update=comic['last_update'],
            ignore_index=ignore_index,
            uid=request.cookies['uid']
        )
        save_file(f'cover/{comic_id}.png', comic['cover'])
        subscribe_list_str = formdata.get('subscribe_list')
        subscribe_list = []
        if subscribe_list_str is not None:
            subscribe_list = [int(i) for i in subscribe_list_str.split(',')]
        chapter_list = []

        for i in comic['chapters']:
            i['comic_id'] = comic_id
            i['sync_state'] = 1 if i['chapter_id'] in subscribe_list else 0
            chapter_list.append(i)

        db.subscribe_chapters(chapter_list[ignore_index:])

        if len(subscribe_list) > 0:
            db.sync_task_by_chapter_id(comic_id)

    sync_now()

    return jsonify({'msg': 'ok', 'result': True})


@app.route('/subscribe_chapters', methods=['POST'])
def subscribe_chapters():
    formdata = request.form
    subscribe_list_str = formdata.get('subscribe_list')
    with DBHelper() as db:
        for i in subscribe_list_str.split(','):
            db.update_by_id('chapter',  int(i), sync_state=1)
        db.sync_task_by_chapter_id(formdata.get('id'))
    sync_now()
    return jsonify({'msg': 'ok', 'result': True})


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    formdata = request.form
    id = formdata.get('id')
    with DBHelper() as db:
        db.unsubscribe(id)
    cover_file = f"cache/cover/{id}.png"
    if os.path.exists(cover_file):
        os.remove(cover_file)
    shutil.rmtree(f'cache/{id}', ignore_errors=True)

    return jsonify({'msg': 'ok', 'result': True})


class WebServer(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.start()

    def run(self):
        app.run(host='0.0.0.0', debug=False, use_reloader=False)


if __name__ == "__main__":
    ws = WebServer()
    ws.join()
