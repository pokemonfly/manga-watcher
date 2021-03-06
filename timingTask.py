from functools import partial
import os
import re
from flask import render_template
from loguru import logger
import schedule
from threading import Thread, Lock
from dbHelper import DBHelper
from ftpHelper import FtpHelper
from task import Task
from utils import SITE_CONFIG, save_file
import shutil
from datetime import datetime
import jinja2
import time

logger.add('err.log', level="ERROR")


def render_template(template, ** context):
    return jinja2.Environment(loader=jinja2.FileSystemLoader(
        'templates/')).get_template(template).render(context)


class TimingTask(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sync_comic_lock = Lock()
        self.sync_chapter_lock = Lock()
        self.last_sync_time = None
        self.ref = 0
        self.is_run = True
        self.html_set = set()
        self.start()
        # schedule.every(6).hours.do(self.sync_comic)
        # schedule.every(7).days.do(self.del_old_file)

    def run(self):
        while self.is_run:
            schedule.run_pending()
            time.sleep(1)

    def del_old_file(self):
        with DBHelper() as db:
            chapter_list = db.query_old_chapter()
            if len(chapter_list) == 0:
                return
            for chapter in chapter_list:
                shutil.rmtree(
                    f"cache/{chapter['comic_id']}/{chapter['chapter_id']}", ignore_errors=True)
            db.after_delete_old_chapter()
            logger.info('阅读后超过30天的章节已经清理')

    def sync_comic(self):
        with self.sync_comic_lock, DBHelper() as db:
            comic_list = db.query_comic()
            if len(comic_list) == 0:
                return
            task = Task()
            task_list = []
            for comic in comic_list:
                if comic['last_sync'] is not None and (datetime.now() - datetime.fromisoformat(comic['last_sync'])) .total_seconds() < 60 * 60 * 24:
                    continue
                url = comic['page_url']
                origin = re.findall(r'^https?://[^/]+', url)[0]
                task_list.append({
                    "url": url,
                    "js_init": SITE_CONFIG[origin]['action']['comic']['js_init'],
                    "js_result": SITE_CONFIG[origin]['action']['comic']['js_result'],
                    "callback":  partial(self.sync_comic_callback, comic)
                })
            self.ref += len(task_list)
            task.set_task(task_list, auto_close=True)

    def sync_comic_callback(self, info, comic, error=None):
        with DBHelper() as db:
            id = info['id']
            if error is not None:
                logger.error(
                    f"[{info['title']}] 同步发生错误 {error}")
                db.upd_task_error(1, id, error)
                self.ref -= 1
                return
            ignore_index = info['ignore_index']
            chapter_list = db.query_chapter_by_id(id)
            old_list = [(i['chapter_id'], i['chapter_title'])
                        for i in chapter_list]
            old_id_list = [i[0] for i in old_list]
            new_list = [(i['chapter_id'], i['chapter_title'])
                        for i in comic['chapters']][ignore_index:]
            diff_list = list(set(new_list) - set(old_list))
            if (diff_len := len(diff_list)) > 0:
                if len(err_list := [i for i in diff_list if i[0] in old_id_list]) > 0:
                    logger.info(
                        f"[{info['title']}] 章节顺序 {str(err_list)} 发生变化, 需要手动处理")
                    self.ref -= 1
                    return
                logger.info(f"[{info['title']}] 发现更新 {diff_len} 章")
                diff_id_list = [i[0] for i in diff_list]
                insert_list = [i for i in comic['chapters']
                               if i['chapter_id'] in diff_id_list]
                for i in insert_list:
                    i['comic_id'] = id
                    i['sync_state'] = 1

                db.subscribe_chapters(insert_list)
                db.sync_task_by_chapter_id(id)
                db.update_by_id(
                    'comic', id,
                    last_update=comic['last_update'],
                    last_sync=datetime.now()
                )
                self.html_set.add((1, id))
                self.sync_chapter()
            else:
                db.update_by_id(
                    'comic', id,
                    last_sync=datetime.now()
                )
                logger.info(f"[{comic['title']}] 无更新")
        self.ref -= 1

    def sync_chapter(self):
        with self.sync_chapter_lock, DBHelper() as db:
            todo_list = db.query_task()
            if len(todo_list) == 0:
                return
            task = Task()
            task_list = []
            for item in todo_list:
                url = item['chapter_url']
                origin = re.findall(r'^https?://[^/]+', url)[0]
                task_list.append({
                    "url": url,
                    "js_init": SITE_CONFIG[origin]['action']['chapter']['js_init'],
                    "js_result": SITE_CONFIG[origin]['action']['chapter']['js_result'],
                    "callback":  partial(self.sync_chapter_callback, item)
                })
            self.ref += len(task_list)
            task.set_task(task_list, auto_close=True)

    def sync_chapter_callback(self, info, chapter, error=None):
        with DBHelper() as db:
            if error is not None:
                logger.error(
                    f"[{info['comic_title']}][{info['chapter_title']}] 发生错误 {error}")
                # db.upd_task_error(2, info['task_id'], error)
                self.ref -= 1
                return
            page_count = len(chapter)
            for c in chapter:
                save_file(
                    f"{info['comic_id']}/{info['chapter_id']}/{c['id']}.png", c['data'])
            db.update_by_id(
                'chapter', info['chapter_row_id'],
                page_count=page_count,
                sync_state=2
            )
            db.delete_by_id('task', info['task_id'])
        self.html_set.add((1, info['comic_id']))
        self.html_set.add((2, info['chapter_row_id']))
        self.ref -= 1

    def create_index_html(self):
        if self.last_sync_time is None:
            self.last_sync_time = datetime.now()
        elif (datetime.now() - self.last_sync_time) .total_seconds() > 300:
            return schedule.CancelJob
        sitelist = [{
            'name': SITE_CONFIG[site]['name'],
            'url': SITE_CONFIG[site]['origin']
        } for site in SITE_CONFIG if "search" in SITE_CONFIG[site]["action"]]
        with DBHelper() as db:
            readlist = db.query_comic()
        str = render_template(
            'index.html', sitelist=sitelist, readlist=readlist)
        os.makedirs(os.path.dirname('cache/index.html'), exist_ok=True)
        with open('cache/index.html', 'w') as f:
            f.write(str)
        return schedule.CancelJob

    def create_comic_html(self, id):
        with DBHelper() as db:
            comic = db.query_by_id('comic', id)[0]
            chapterlist = db.query_chapter_by_id(id)

        str = render_template('comic.html',
                              comic=comic,
                              chapterlist=chapterlist)
        os.makedirs(os.path.dirname(f'cache/{id}.html'), exist_ok=True)
        with open(f'cache/{id}.html', 'w') as f:
            f.write(str)

    def create_chapter_html(self, id):
        with DBHelper() as db:
            chapter = db.query_by_id('chapter', id)[0]

        str = render_template('chapter.html', chapter=chapter)
        os.makedirs(os.path.dirname(
            f"cache/{chapter['comic_id']}/{chapter['chapter_id']}.html"), exist_ok=True)
        with open(f"cache/{chapter['comic_id']}/{chapter['chapter_id']}.html", 'w') as f:
            f.write(str)

    def daily_task(self):
        logger.info('Start daily task')
        with FtpHelper() as ftp:
            ftp.read_log(self.sync_access_log)
        self.sync_comic()
        schedule.every(1).seconds.do(self.daily_task_watch)

    def daily_task_watch(self):
        if self.ref == 0:
            logger.info('Daily task finished')
            logger.info('Create Cache File')
            self.create_index_html()
            if len(self.html_set) > 0:
                for i in self.html_set:
                    if i[0] == 1:
                        self.create_comic_html(i[1])
                    else:
                        self.create_chapter_html(i[1])
            logger.info('Sync Ftp Server')
            try:
                with FtpHelper() as ftp:
                    ftp.upload('cache', auto_remove=True)
            except:
                logger.error('Sync Error')
            self.is_run = False
            logger.info('Down')

    def sync_access_log(self, lines):
        list = []
        for row in lines:
            res = re.findall(r'\[(.*?)\].*log\.js\?id=(\d+)', row)
            if len(res) > 0:
                list.append(res[0])
        with DBHelper() as db:
            for (date, id) in list:
                db.update_by_id(
                    'chapter', id, last_access=datetime.fromisoformat(date))


if __name__ == "__main__":
    tt = TimingTask()
    # tt.daily_task()
    # tt.join()
    with open('./access.log', 'r') as f:
        arr = f.readlines()
    tt.sync_access_log(arr)
