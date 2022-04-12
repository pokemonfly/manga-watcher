from ftplib import FTP, error_perm
import yaml
from loguru import logger
import os

with open('config/ftp.yaml', 'rb') as file:
    cfg = yaml.safe_load(file)


class FtpHelper():
    def __init__(self):
        self.ftp = FTP(cfg['address'], cfg['username'], cfg['password'])
        logger.info(f'FTP connect')

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.ftp.close()
        logger.info(f'FTP connect close')

    def upload(self, path):
        files = os.listdir(path)
        os.chdir(path)
        for f in files:
            if os.path.isfile(f):
                with open(f, 'rb') as file:
                    self.ftp.storbinary(f'STOR {f}', file)
                    logger.info(f'Upload File: {f}')
            elif os.path.isdir(f):
                try:
                    self.ftp.mkd(f)
                except error_perm as e:
                    if not e.args[0].startswith('550'):
                        raise

                self.ftp.cwd(f)
                self.upload(f)
        self.ftp.cwd('..')
        os.chdir('..')

    def read_log(self, path):
        def analyze(line):
            logger.info(line)
        self.ftp.retrlines(f'RETR {path}', analyze)


if __name__ == "__main__":
    with FtpHelper() as ftp:
        ftp.upload('static')
        ftp.upload('cache')
        # ftp.read_log('5.html')
        pass
