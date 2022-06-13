from ftplib import FTP, error_perm
import yaml
from loguru import logger
import os
import re
import io
with open('config/cfg.yaml', 'rb') as file:
    cfg = yaml.safe_load(file)


class FtpHelper():
    def __init__(self):
        self.ftp = FTP(cfg['address'], cfg['username'], cfg['password'])
        logger.info(f'FTP connect')
        self.ftp.cwd('sda1/ftp')

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.ftp.close()
        logger.info(f'FTP connect close')

    def remove(self, path):
        if '.' in path:
            self.ftp.delete(path)
            logger.info(f'Delete File: {path}')
        else:
            for p in self.ftp.nlst(path):
                self.remove(p)
            self.ftp.rmd(path)
            logger.info(f'Delete Dictionary: {path}')

    def upload(self, path, auto_remove=False):
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                p = re.sub(".*\/", "", path)
                self.ftp.storbinary(f'STOR {p}', file)
                logger.info(f'Upload File: {path}')
            if auto_remove:
                os.remove(path)
        elif os.path.isdir(path):
            files = os.listdir(path)
            os.chdir(path)
            for f in files:
                if os.path.isdir(f):
                    try:
                        self.ftp.mkd(f)
                    except error_perm as e:
                        if not e.args[0].startswith('550'):
                            raise
                    self.ftp.cwd(f)
                self.upload(f, auto_remove)
            self.ftp.cwd('..')
            os.chdir('..')
            if auto_remove:
                os.rmdir(path)

    def read_log(self):
        str_io = io.StringIO()
        self.ftp.retrlines(f'RETR access.log', lambda s: print(s, file=str_io))
        lines = str_io.getvalue().strip().split('\n')
        if lines[0] == cfg['access_log_first_row']:
            new_lines = lines[cfg['access_log_cursor']:]
        else:
            new_lines = lines
        str_io.close()
        with open('config/cfg.yaml', 'w') as file:
            cfg['access_log_cursor'] = len(lines)
            cfg['access_log_first_row'] = lines[0]
            file.write(yaml.safe_dump(cfg))
        return new_lines


if __name__ == "__main__":
    with FtpHelper() as ftp:
        ftp.upload('static')
        # ftp.upload('cache2', auto_remove=True)
        # ftp.upload('nginx.conf')

        # ftp.upload(f'static/access.log')
        # print('\n'.join(ftp.read_log()))
        pass
