from os import path
import sqlite3

from loguru import logger

DB_FILE = 'data.db'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DBHelper():
    def __init__(self):
        if self.check_db():
            self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = dict_factory

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def check_db(self):
        if path.exists(DB_FILE) is False:
            self.conn = sqlite3.connect(DB_FILE)
            # init db
            with open('dump.sql', 'rb') as sql:
                self.conn.executescript(sql.read().decode('utf-8'))
                self.conn.commit()
            return False
        else:
            return True

    def close(self):
        self.conn.close()

    def query_by_id(self, table, id):
        sql = f"""
            select * from {table} 
            where id = {id};
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def update_by_id(self, table, id, **dict):
        keys = dict.keys()
        sql = f"""
            update {table} set {', '.join([ k + '=?' for k in keys])}
            where id = {id};
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, [dict[k] for k in keys])
        self.conn.commit()

    def delete_by_id(self, table, id):
        sql = f"""
            delete from {table} 
            where id = {id};
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()

    def subscribe_comic(self, **dict):
        sql = f"""
			insert into comic ({','.join(dict.keys())})
			values ( { ','.join([f"{v!r}" for v in dict.values()]) } );
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.lastrowid

    def subscribe_chapters(self, list):
        keys = list[0].keys()
        sql = f"""
            insert into chapter ({','.join(keys)}) 
            values ({','.join( ["?" for _ in keys] )})
        """
        cursor = self.conn.cursor()
        cursor.executemany(
            sql, [[i[k] for k in keys] for i in list])

        self.conn.commit()

    # id: type=1 id=comic_id  type=2 id=task_id
    def upd_task_error(self, type, id, log):
        if type == 2:
            self.update_by_id('task', id, fail_log=log)
            return
        else:
            sql = f"""
                insert into task (task_type, link_id, fail_log)
                values (1, {id}, '{log}')
            """
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()

    def sync_task_by_chapter_id(self, id):
        sql = f"""
            insert into task (task_type, link_id)
            select 2, chapter.id from chapter
            left join task
            on task.task_type = 2 and task.link_id = chapter.id
            where comic_id = {id} and sync_state = 1
            and task.id is null
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()

    def unsubscribe(self, id):
        sql = f"""
			delete from task where task_type = 2 and link_id in (
				select id from chapter where comic_id = {id}
			);
			delete from task where task_type = 1 and link_id = {id};
			delete from chapter where comic_id = {id};
			delete from comic where id = {id};
        """
        self.conn.executescript(sql)
        self.conn.commit()

    def query_comic(self, uid):
        condition = f"where comic.uid = '{uid}'" if uid is not None else '' 
        sql = f"""
            select count(chapter.comic_id) as unread, comic.* 
            from comic
            left join chapter
            on chapter.comic_id = comic.id
                and chapter.sync_state=2
                and chapter.last_access is NULL
            {condition}
            group by comic.id
            order by unread desc, comic.last_update desc
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def query_comic_by_id(self, id):
        sql = f"""
            select * from comic
            where id = {id}
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def query_chapter_by_id(self, id):
        sql = f"""
            select * from chapter
            where comic_id = {id}
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def query_old_chapter(self):
        sql = """
            select * from chapter 
            where sync_state=2 and last_access < date('now', '-30 days');
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def after_delete_old_chapter(self):
        sql = f"""
            update chapter set sync_state=3
            where sync_state=2 and last_access < date('now', '-30 days');
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()

    def query_task(self):
        sql = """
            select task.id as task_id, comic_id, chapter_id, chapter_url, 
            chapter_title, comic.title as comic_title, chapter.id as chapter_row_id
            from task
            left join chapter on chapter.id = task.link_id
            left join comic on comic.id = chapter.comic_id
            where task.task_type = 2
            and task.fail_log is null;
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
