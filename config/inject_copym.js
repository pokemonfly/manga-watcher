window._cache_ = { loaded: 0};
window.search_init = function (page) {
  if (!$) return false;
  page = page || 1;
  setTimeout(function () {
    if ($(".comicNumAll").html() == "0") {
      window._is_no_data = true;
    }
  }, 5000);
  if (page != 1) {
    $(".page-all-item")[page - 1].click();
  }
  try {
    return searchData.comic[page].length > 0 || window._is_no_data;
  } catch (e) {
    return false;
  }
};
window.search_result = function (page) {
  page = page || 1;
  return {
    page_num: page,
    page_count: Math.round(
      +$(".comicNumAll").html() / searchData.comic[1].length
    ),
    list: searchData.comic[page].map((i) => ({
      cover: i.cover,
      title: i.name,
      author: i.author[0]?.name,
      page_url: `${location.origin}/comic/${i.path_word}`,
    })),
  };
};
window.comic_init = function () {
  if (!$) return false;
  let src = $("div.container.comicParticulars-title img.lazyloaded").attr(
    "src"
  );
  if (src) {
    getBase64(src).then((str) => {
      window._cache_.cover = str;
    });
  }
  return $("#default全部 a[title]").length > 0 && !!window._cache_.cover;
};
window.comic_result = function () {
  return {
    title: $("div.container.comicParticulars-title h6[title]").text(),
    author: $(
      "div.container.comicParticulars-title li:nth-child(3) > span.comicParticulars-right-txt > a"
    ).text(),
    cover: window._cache_.cover,
    page_url: location.href,
    origin: location.origin,
    last_update: $(
      "div.container.comicParticulars-title  li:nth-child(5) > span.comicParticulars-right-txt"
    ).text(),
    chapters: $("#default全部 a[title]").map(function (id) {
      return {
        chapter_id: id,
        chapter_title: this.title,
        chapter_url: this.href,
      };
    }),
  };
};
window.chapter_init = function () {
  if (!$) return false;
  let count = +$(".comicCount").text();
  let index = +$(".comicIndex").text();
  if (index > count) {
    // 页面bug 偶尔显示成0
    count = index;
  }
  let loaded = $(".comicContent-list > li").length;
  let arr = $(".lazyload");
  clearTimeout(window._t || 0);
  if (count > loaded) {
    let st = document.documentElement.scrollTop;
    let sh =
      document.documentElement.scrollHeight -
      document.documentElement.clientHeight;
    window.scrollTo(0, st < sh ? st + 50 : 0);
    window._t = setTimeout(() => {
      chapter_init();
    }, 50);
    return false;
  } else if (arr.length) {
    arr[0].scrollIntoView();
    window._t = setTimeout(() => {
      chapter_init();
    }, 200);
    return false;
  }
  $(".comicContent-list img").each(function () {
    if (!window._cache_[this.src]) {
      window._cache_[this.src] = 1;
      getBase64(this.src).then((str) => {
        window._cache_[this.src] = str;
        window._cache_.loaded++;
      });
    }
  });

  return window._cache_.loaded == count;
};
window.chapter_result = function () {
  if (window._cache_.loaded == 0) {
    return [];
  }
  return $(".comicContent-list img").map(function (id) {
    return {
      id,
      data: window._cache_[this.src],
    };
  });
};
