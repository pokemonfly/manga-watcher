
from queue import Queue, Empty
from threading import Thread
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from loguru import logger
import schedule

from utils import ResultStore
logger.add('err.log', level="ERROR")

THREAD_LIMIT = 3
with open('inject.js', "r") as jsFile:
    injectJs = jsFile.read()


class Worker(Thread):
    def __init__(self, q, result):
        super().__init__(daemon=True)
        self.q = q
        self.result = result
        self.unmount_job = None
        self.shutdown = False
        self.mount()
        self.start()
        self.log('start')

    def do_task(self, task):
        try:
            self.driver.get(task['url'])
            self.log(f"open {task['url']}")
            self.driver.execute_script(injectJs)
            if 'js_init' in task:
                WebDriverWait(self.driver, 500, poll_frequency=3).until(
                    lambda _: self.driver.execute_script(task['js_init']))
            res = self.driver.execute_script(task['js_result'])
            if "callback" in task:
                task['callback'](res)
            else:
                self.result.add(res)
        except TimeoutException:
            if "callback" in task:
                task['callback'](None, 'Timeout')
            self.error()
        except Exception:
            self.error()

    def error(self):
        trace_txt = traceback.format_exc()
        logger.error(
            f'Worker[{self.native_id}]: {trace_txt}')

    def log(self, txt):
        logger.info(f'Worker [{self.native_id}]: {txt}')

    def mount(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-web-security')  # 允许图片跨域加载
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        try:
            self.driver = webdriver.Chrome(service=Service(
                ChromeDriverManager().install()), chrome_options=chrome_options)
        except Exception:
            self.error()

    def unmount(self):
        self.shutdown = True
        self.driver.quit()
        self.log('unmount')
        if self.unmount_job is not None:
            schedule.cancel_job(self.unmount_job)
            self.unmount_job = None
        return schedule.CancelJob

    def run(self):
        while not self.shutdown:
            try:
                task = self.q.get(block=False)
                schedule.cancel_job(self.unmount_job)
                self.unmount_job = None
                self.do_task(task)
                self.q.task_done()
            except Empty:
                if self.unmount_job is None:
                    self.unmount_job = schedule.every(
                        2).minutes.do(lambda: self.unmount())


class Task(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.pool = []
        self.q = Queue()
        self.result = ResultStore()
        self.closeFlag = False
        self.start()

    def set_task(self, arr, auto_close=False):
        for i in arr:
            self.q.put(i)
        self.q.join()
        if auto_close:
            self.closeFlag = True

    def get_result(self):
        return self.result.getAll()

    def run(self):
        while not self.closeFlag:
            qsize = self.q.qsize()
            poolsize = len(self.pool)
            while poolsize < THREAD_LIMIT and qsize > poolsize:
                self.pool.append(
                    Worker(q=self.q, result=self.result))
                poolsize += 1

            for worker in self.pool:
                if worker.is_alive() is not True:
                    self.pool.remove(worker)

        for worker in self.pool:
            worker.unmount()
