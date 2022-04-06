BEGIN TRANSACTION;

CREATE TABLE comic (
  id integer primary key,
  title text,
  author text,
  page_url text,
  -- 网站源
  origin text,
  -- 针对巨长章节 无视掉前面的一部分章节
  ignore_index int,
  last_update datetime
);

create table chapter (
  id integer primary key,
  comic_id int,
  -- 章节序号 排序用
  chapter_id int,
  chapter_title text,
  chapter_url text,
  --  0:未处理 1:待处理 2:已完成 3:已删除 
  sync_state int,
  page_count int,
  -- 最后访问时间
  last_access datetime
);

create table task (
  id integer primary key,
  -- 同步类型: 1:同步章节 2: 同步页面
  task_type int,
  -- 等于task_type=1:comic.id   task_type=2:chapter.id
  link_id int,
  -- 分页场景 页码
  last_sync_index int,
  -- 分页场景 链接
  last_sync_link int,
  fail_log text
);

COMMIT;

