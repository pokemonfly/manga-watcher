import schedule
from threading import Thread
from flask import Flask, render_template, request, jsonify, g, send_from_directory
from loguru import logger
from dbHelper import DBHelper
from task import Task
from timingTask import TimingTask
from utils import TimerCache,  ranstr, save_file, SITE_CONFIG
import json

app = Flask(__name__)
task = Task()
timerCache = TimerCache()
timingTask = TimingTask()
logger.add('err.log', level="ERROR")


@app.route('/image/<path:path>')
def send_image_file(path):
    return send_from_directory('cache', path)


@app.route('/')
def index():
    return render_template('index.html', data=json.dumps(['a'], ensure_ascii=False))


@app.route('/search')
def search():
    keyword = request.args.get('keyword')
    page_num = request.args.get('page_num') or 1
    cachekey = f'{keyword}:{page_num}'
    res = timerCache.get(cachekey)
    if res is None:
        url = SITE_CONFIG['action']['search']['url'].format(keyword=keyword)
        task.set_task([{
            "url": url,
            "js_init": SITE_CONFIG['action']['search']['js_init'].format(page_num=page_num),
            "js_result": SITE_CONFIG['action']['search']['js_result'].format(page_num=page_num)
        }])
        res = task.get_result()[0]
        timerCache.add(cachekey, res)
    return render_template('search.html', data=json.dumps(res, ensure_ascii=False))


@app.route('/comic_preview')
def preview():
    url = request.args.get('url')
    res = timerCache.get(url)
    if res is None:
        task.set_task([{
            'type': "preview",
            "url": url,
            "js_init": SITE_CONFIG['action']['comic']['js_init'],
            "js_result": SITE_CONFIG['action']['comic']['js_result']
        }])
        res = task.get_result()[0]
        timerCache.add(url, res)
    return render_template('preview.html', data=json.dumps(res, ensure_ascii=False))


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

    cover_path = f'cover/{ranstr(6)}.png'
    save_file(cover_path, comic['cover'])
    ignore_index = int(formdata.get('ignore_index') or 0)
    with DBHelper() as db:
        comic_id = db.subscribe_comic(
            title=comic['title'],
            author=comic['author'],
            cover=cover_path,
            page_url=comic['page_url'],
            origin=comic['origin'],
            last_update=comic['last_update'],
            ignore_index=ignore_index
        )
        subscribe_list_str = formdata.get('subscribe_list')
        subscribe_list = []
        if subscribe_list_str is not None:
            subscribe_list = [int(i)
                              for i in subscribe_list_str.split(',')]
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


class WebServer(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.start()

    def run(self):
        app.run(debug=True, use_reloader=False)


if __name__ == "__main__":
    ws = WebServer()
    ws.join()
