window._cache_ = { loaded: 0 };

window.search_init = (page) => {
  if (!$) return false;
  if (serchArry.length == 0) return true;
  return $(".itemBox").length > 0;
};
window.search_result = (page) => {
  return {
    page_num: page,
    page_count: 1,
    list: $(".itemBox")
      .map(function () {
        let $t = $(this);
        let $img = $t.find("img");
        return {
          cover: $img.attr("src"),
          title: $t.find(".title").html(),
          author: $t.find(".txtItme").eq(0).text(),
          page_url: $t.find("a").get(0).href,
        };
      })
      .toArray(),
  };
};
window.comic_init = () => {
  // 版权ban
  if (document.body.childNodes.length == 1) return true;
  if (!$) return false;
  sort.asc(jsonData)
  sort.expand(null,0)
  let src = $("#Cover img").attr("src");
  if (src) {
    getBase64(src).then((str) => {
      window._cache_.cover = str;
    });
  }
  return !!window._cache_.cover;
};
window.comic_result = () => {
  if (document.body.childNodes.length == 1) return {};
  return {
    title: $("#comicName").text(),
    author: $(".introName").text(),
    cover: window._cache_.cover,
    page_url: location.href,
    origin: location.origin,
    last_update: $(".date").text().split(" ")[0],
    chapters: $(".Drama li a")
      .map(function (id) {
        return {
          chapter_id: id,
          chapter_title: $(this).find("span").text(),
          chapter_url: this.href,
        };
      })
      .toArray(),
  };
};
window.chapter_init = () => {
  if (!$) return false;
  let $img = $(".comic_img");
  let count = $img.length;
  if (count) {
    $img.map(function () {
      let src = this.src;
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
  return $(".comic_img")
    .map(function (id) {
      return {
        id,
        data: window._cache_[this.src],
      };
    })
    .toArray();
};
