window._cache_ = { loaded: 0 };
window.comic_init = () => {
  if (!$) return false;
  let src = $("div.comic_i_img img").attr("src");
  if (src) {
    getBase64(src).then((str) => {
      window._cache_.cover = str;
    });
  }
  return !!window._cache_.cover;
};
window.comic_result = () => {
  return {
    title: $(".comic_deCon h1 a").text(),
    author: $(".comic_deCon_liO li:nth-child(1)").text().replace("作者：", ""),
    cover: window._cache_.cover,
    page_url: location.href,
    origin: location.origin,
    last_update: $(".zj_list_head_dat")
      .html()
      .replace("[ 更新时间：", "")
      .replace(" ]", ""),
    chapters: $(".tab-content-selected .list_con_li li a").map(function (id) {
      return {
        chapter_id: id,
        chapter_title: $(this).find(".list_con_zj").text(),
        chapter_url: this.href,
      };
    }),
  };
};
window.chapter_init = () => {
  if (!$) return false;
  let count = $("#page_select option").length;
  if (picArry && picArry.length) {
    picArry.forEach(function (src) {
      src = `https://images.dmzj.com/${src}`
      if (!window._cache_[src]) {
        window._cache_[src] = 1;
        getBase64(src).then((str) => {
          window._cache_[src] = str;
          window._cache_.loaded++;
        });
      }
    });
  }
  return window._cache_.loaded == count;
};
window.chapter_result = () => {
  if (window._cache_.loaded == 0) {
    return [];
  }
  return picArry.map(function (src) {
    src = `https://images.dmzj.com/${src}`
    return {
      id,
      data: window._cache_[src],
    };
  });
};
