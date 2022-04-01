from functools import partial
import re
from loguru import logger
import schedule
from threading import Thread, Lock
from dbHelper import DBHelper
from task import Task
from utils import SITE_CONFIG, save_file
import shutil
logger.add('err.log', level="ERROR")


class TimingTask(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sync_comic_lock = Lock()
        self.sync_chapter_lock = Lock()
        self.start()
        schedule.every(6).hours.do(self.sync_comic)
        schedule.every(7).days.do(self.del_old_file)

    def run(self):
        while True:
            schedule.run_pending()

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
                url = comic['page_url']
                origin = re.findall(r'^https?://[^/]+', url)[0]
                task_list.append({
                    "url": url,
                    "js_init": SITE_CONFIG[origin]['action']['comic']['js_init'],
                    "js_result": SITE_CONFIG[origin]['action']['comic']['js_result'],
                    "callback":  partial(self.sync_comic_callback, comic)
                })

            task.set_task(task_list, auto_close=True)

    def sync_comic_callback(self, info, comic, error=None):
        with DBHelper() as db:
            id = info['id']
            if error is not None:
                logger.error(
                    f"[{info['title']}] 同步发生错误 {error}")
                db.upd_task_error(1, id, error)
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
                    last_update=comic['last_update']
                )
                self.sync_chapter()
            else:
                logger.info(f"[{comic['title']}] 无更新")

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

            task.set_task(task_list, auto_close=True)

    def sync_chapter_callback(self, info, chapter, error=None):
        with DBHelper() as db:
            if error is not None:
                logger.error(
                    f"[{info['comic_title']}][{info['chapter_title']}] 发生错误 {error}")
                db.upd_task_error(2, info['task_id'], error)
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
