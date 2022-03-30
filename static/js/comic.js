function renderInfo(data) {
  let { title, author, cover, origin, last_update } = data;
  return `<div class="chapter-info">
    <img src="image/${cover}"/>
    <div class="title">${title}</div>
    <div class="sub">作者: ${author}</div>
    <div class="sub">源: ${origin}</div>
    <div class="sub">最近更新: ${last_update}</div>
  </div>`;
}
function renderChapter(data) {
  const { chapters } = data;
  return `
  <div class="chapter-list">
    ${chapters
      .map((i) => {
        let state = {
          0: "",
          1: "[下载中]",
          2: `[${i.page_count}页]`,
          3: "[已删除]",
        }[i.sync_state];
        return `
        <div class="chapter-item" data-id="${i.id}">
          ${i.chapter_title}${state}
        </div>
      `;
      })
      .join("")}
  </div>
  <div class="subscribe-row">
    <button id='subscribe'>下载所选章节</button>
    <button id='unsubscribe'>取消订阅</button>
  </div>
  <div class="subscribe-row">
    <button id='showOrigin'>显示原页面</button>
  </div>
  `;
}
$(function () {
  if (window.injectData) {
    $("#main").html([
      renderNav(),
      renderInfo(window.injectData),
      renderChapter(window.injectData),
    ]);

    $(".chapter-item").on("click", function () {
      let id = $(this).attr("data-id");
      let chapterData = window.injectData.chapters.filter(
        (i) => (i.id == id)
      )[0];
      if (chapterData.sync_state == 2) {
        location.href = `chapter?id=${id}`;
      } else if (chapterData.sync_state != 1) {
        $(this).toggleClass("select");
      }
    });

    $("#showOrigin").on("click", function () {
      window.location.href = window.injectData.page_url;
    });
    $("#unsubscribe").on("click", function () {
      $.ajax({
        url: "/unsubscribe",
        method: "POST",
        data: {
          id: window.injectData.id,
        },
      }).done(function (res) {
        if (res.result) {
          showMsg("取消成功");
          setTimeout(function () {
            window.location.href = "/";
          }, 1e3);
        } else {
          showMsg("Error:" + res.msg);
        }
      });
    });
    $("#subscribe").on("click", function () {
      let subscribe_list = [
        ...$(".chapter-item.select").map(function () {
          return $(this).attr("data-id");
        }),
      ];
      if (!subscribe_list.length) {
        showMsg("未选择");
        return;
      }
      $.ajax({
        url: "/subscribe_chapters",
        method: "POST",
        data: {
          id: window.injectData.id,
          subscribe_list: subscribe_list.join(","),
        },
      }).done(function (res) {
        if (res.result) {
          showMsg("订阅成功");
          setTimeout(function () {
            location.reload();
          }, 1e3);
        } else {
          showMsg("Error:" + res.msg);
        }
      });
    });
  }
});
