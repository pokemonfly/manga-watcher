window.getXpath = function (e) {
  var i = e;
  if (i && i.id) return '//*[@id="' + i.id + '"]';
  for (var n = []; i && Node.ELEMENT_NODE === i.nodeType; ) {
    for (var r = 0, o = !1, d = i.previousSibling; d; )
      d.nodeType !== Node.DOCUMENT_TYPE_NODE &&
        d.nodeName === i.nodeName &&
        r++,
        (d = d.previousSibling);
    for (d = i.nextSibling; d; ) {
      if (d.nodeName === i.nodeName) {
        o = !0;
        break;
      }
      d = d.nextSibling;
    }
    n.push(
      (i.prefix ? i.prefix + ":" : "") +
        i.localName +
        (r || o ? "[" + (r + 1) + "]" : "")
    ),
      (i = i.parentNode);
  }
  return n.length ? "/" + n.reverse().join("/") : "";
};

window.getBase64 = function (src) {
  return new Promise((res) => {
    let image = new Image();
    image.src = src;
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    image.onload = () => {
      canvas.width = image.width;
      canvas.height = image.height;
      context.drawImage(image, 0, 0);
      res(canvas.toDataURL().replace("data:image/png;base64,", ""));
    };
  });
};
window._0_search_init = function (page) {
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
window._0_search_result = function (page) {
  page = page || 1;
  return {
    page_num: page,
    page_all: +$(".comicNumAll").html(),
    page_size: searchData.comic[1].length,
    list: searchData.comic[page].map((i) => ({
      cover: i.cover,
      title: i.name,
      author: i.author[0]?.name,
      page_url: `${location.origin}/comic/${i.path_word}`,
    })),
  };
};
window._0_comic_init = function () {
  if (!$) return false;
  window._cache_ = window._cache_ || {};
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
window._0_comic_result = function () {
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
window._0_chapter_init = function () {
  if (!$) return false;
  window._img_ = window._img_ || { loaded: 0 };
  let count = +$(".comicCount").text();
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
      _0_chapter_init();
    }, 50);
    return false;
  } else if (arr.length) {
    arr[0].scrollIntoView();
    window._t = setTimeout(() => {
      _0_chapter_init();
    }, 200);
    return false;
  }
  $(".comicContent-list img").each(function () {
    if (!window._img_[this.src]) {
      window._img_[this.src] = 1;
      getBase64(this.src).then((str) => {
        window._img_[this.src] = str;
        window._img_.loaded++;
      });
    }
  });

  return window._img_.loaded == count;
};
window._0_chapter_result = function () {
  return $(".comicContent-list img").map(function (id) {
    return {
      id,
      data: window._img_[this.src],
    };
  });
};
