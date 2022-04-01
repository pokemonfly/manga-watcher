window._cache_ = { loaded: 0 };

window.search_init = (page) => {
  if (!$) return false;
  return $("#loading").is(":visible") == false;
};
window.search_result = (page) => {
  return {
    page_num: page,
    page_count: +$(".pages .pselected").eq(-2).html(),
    list: $(".tcaricature_block ul")
      .map(function () {
        let $t = $(this);
        let $img = $t.find("img");
        return {
          cover: $img.attr("src"),
          title: $img.attr("alt"),
          author: $t.find(".adiv2hidden").eq(0).html().replace("作者:", ""),
          page_url: $t.find("a").get(0).href,
        };
      })
      .toArray(),
  };
};
window.comic_init = () => {
  if (!$) return false;
  let src = $("div.anim_intro_ptext img").attr("src");
  if (src) {
    getBase64(src).then((str) => {
      window._cache_.cover = str;
    });
  }
  return !!window._cache_.cover;
};
window.comic_result = () => {
  return {
    title: $(".anim_title_text h1").text(),
    author: $(".anim-main_list tr:nth-child(3) a").text(),
    cover: window._cache_.cover,
    page_url: location.href,
    origin: location.origin,
    last_update: $(".update2").html(),
    chapters: $(".cartoon_online_border li a")
      .map(function (id) {
        return {
          chapter_id: id,
          chapter_title: this.title,
          chapter_url: this.href,
        };
      })
      .toArray(),
  };
};
window.chapter_init = () => {
  if (!$) return false;
  let count = $("#page_select option").length;
  if (arr_pages && arr_pages.length) {
    arr_pages.forEach(function (src) {
      src = `https://images.dmzj.com/${src}`;
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
  return arr_pages.map(function (src) {
    src = `https://images.dmzj.com/${src}`;
    return {
      id,
      data: window._cache_[src],
    };
  });
};
