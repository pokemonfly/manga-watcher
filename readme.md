# 简介

路由器部署 nginx 静态服务器，使用局域网内电脑执行每日同步定时任务并用 ftp 同步到路由器的外接磁盘。
电脑开启时，也可以转发来使用 api 服务。
阅读端使用 yealico

# 安装

```
pip install -r requirements.txt
```

# 运行

```
# api服务 用于添加订阅管理订阅 需要时手动启动
python -X utf8 main.py

# 每日同步任务 配合windows的任务计划执行
python -X utf8 main.py daily
```

# js template

```
window._cache_ = { loaded: 0};
window.search_init = (page) => {};
window.search_result = (page) => {};
window.comic_init = () => {};
window.comic_result = () => {};
window.chapter_init = () => {};
window.chapter_result = () => {};
```

# 路由器部署

-   接好外接硬盘。

-   安装 Entware Nginx

```
amtm
opkg install nginx
```

-   编辑 nginx.conf

```
/tmp/mnt/sda1/entware/etc/nginx
```

-   从路由器导出 Let's Encrypt 证书 （ cert.pem , key.pem ）并放到/tmp/mnt/sda1/cert 目录下

-   启动 Nginx

```
/opt/etc/init.d/S80nginx start
```

# todo list

* auth-basic
https://blog.csdn.net/DavidWed/article/details/91881287
