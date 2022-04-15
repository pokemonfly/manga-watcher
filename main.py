import json
import os
import schedule
from flask import Flask, render_template, request, jsonify,  send_from_directory, make_response
from werkzeug.routing import BaseConverter
from loguru import logger
from dbHelper import DBHelper
from task import Task
from timingTask import TimingTask
from utils import TimerCache,  save_file, SITE_CONFIG
import shutil
import datetime
import re
import sys

app = Flask(__name__)
timerCache = TimerCache()
task = None
timingTask = TimingTask()
logger.add('err.log', level="ERROR")


def get_task():
    if task is None:
        task = Task()
    return task


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.route('/<regex(".+\.(html|png)"):path>')
def send_cache_file(path):
    return send_from_directory('cache', path)


@app.route('/<regex(".+\.(js|css|gif)"):path>')
def send_static_file(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    sitelist = [{
        'name': SITE_CONFIG[site]['name'],
        'url': SITE_CONFIG[site]['origin']
    } for site in SITE_CONFIG if "search" in SITE_CONFIG[site]["action"]]
    with DBHelper() as db:
        readlist = db.query_comic()
    return render_template(
        'index.html', sitelist=sitelist, readlist=readlist)


@ app.route('/api/search')
def search():
    keyword = request.args.get('keyword')
    origin = request.args.get('origin')
    page_num = request.args.get('page_num') or 1
    cachekey = f'{keyword}:{page_num}'
    res = timerCache.get(cachekey)
    if res is None:
        cfg = SITE_CONFIG[origin]['action']['search']
        url = cfg['url'].format(keyword=keyword, page_num=page_num)
        get_task().set_task([{
            "url": url,
            "js_init": cfg['js_init'].format(page_num=page_num),
            "js_result": cfg['js_result'].format(page_num=page_num)
        }])
        res = task.get_result()[0]
        timerCache.add(cachekey, res)
    return render_template('search.html', data=json.dumps(res, ensure_ascii=False))


@ app.route('/api/comic_preview')
def preview():
    url = request.args.get('url')
    origin = re.findall(r'^https?://[^/]+', url)[0]
    if origin not in SITE_CONFIG:
        return jsonify({'msg': 'URL未支持', 'result': False})
    cfg = SITE_CONFIG[origin]['action']['comic']
    res = timerCache.get(url)
    if res is None:
        get_task().set_task([{
            'type': "preview",
            "url": url,
            "js_init": cfg['js_init'],
            "js_result": cfg['js_result']
        }])
        res = task.get_result()[0]
        timerCache.add(url, res)
    return render_template('preview.html', data=json.dumps(res, ensure_ascii=False))


# @ app.route('/bookmark')
# def bookmark():
#     chapter_id = request.args.get('chapter_id')
#     with DBHelper() as db:
#         db.update_by_id('chapter', chapter_id,
#                         last_access=datetime.datetime.now())

#     def sync():
#         timingTask.create_index_html()
#         return schedule.CancelJob
#     schedule.every(60).seconds.do(sync)
#     return jsonify({'msg': 'ok', 'result': True})


@ app.route('/api/sync_now')
def sync_now():
    def sync():
        timingTask.sync_chapter()
        return schedule.CancelJob
    schedule.every(0).seconds.do(sync)
    return jsonify({'msg': 'ok', 'result': True})


@ app.route('/api/subscribe', methods=['POST'])
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
            last_sync=datetime.datetime.now()
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

        timingTask.create_index_html()
        timingTask.create_comic_html(comic_id)
    sync_now()

    return jsonify({'msg': 'ok', 'result': True})


@ app.route('/api/subscribe_chapters', methods=['POST'])
def subscribe_chapters():
    formdata = request.form
    subscribe_list_str = formdata.get('subscribe_list')
    with DBHelper() as db:
        for i in subscribe_list_str.split(','):
            db.update_by_id('chapter',  int(i), sync_state=1)
        db.sync_task_by_chapter_id(formdata.get('id'))
    sync_now()
    return jsonify({'msg': 'ok', 'result': True})


@ app.route('/api/unsubscribe', methods=['POST'])
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


@ app.route('/api/freshHtml')
def freshHtml():
    timingTask.create_index_html()
    with DBHelper() as db:
        comic_list = db.query_comic()
        for comic in comic_list:
            timingTask.create_comic_html(comic['id'])
            chapter_list = db.query_chapter_by_id(comic['id'])
            for chapter in chapter_list:
                if chapter['sync_state'] == 2:
                    timingTask.create_chapter_html(chapter['id'])

    return jsonify({'msg': 'ok', 'result': True})


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1 and args[1] == 'daily':
        timingTask.daily_task()
        timingTask.join()
    else:
        # 如果存在证书 就开启https
        ssl_context = None
        if os.path.exists('cert.pem') and os.path.exists('key.pem'):
            ssl_context = ("cert.pem", "key.pem")
        app.run(host='0.0.0.0', debug=False,
                use_reloader=False, ssl_context=ssl_context)
