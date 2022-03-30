function renderInfo(data) {
  let { title, author, cover, origin, last_update } = data;
  cover = "data:image/png;base64," + cover;
  return `<div class="chapter-info">
    <img src="${cover}"/>
    <div class="title">${title}</div>
    <div class="sub">作者: ${author}</div>
    <div class="sub">源: ${origin}</div>
    <div class="sub">最近更新: ${last_update}</div>
  </div>`;
}
function renderChapter(data) {
  const { chapters } = data;
  return `
  <div class="row chapter-hint">
    <div>点击勾选需要下载的章节</div>
    <button id='checkAll'>全选</button>
  </div>
  <div class="chapter-list">
    ${chapters
      .map((i) => {
        return `
        <div class="chapter-item" data-id="${i.chapter_id}">
          ${i.chapter_title}
        </div>
      `;
      })
      .join("")}
  </div>
  <div class="row">
      <label>忽略章节索引: </label>
      <input type="number" id='ignore_index'/>
  </div>
  <div class="subscribe-row">
  <button id='subscribe'>订阅</button>
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
      $(this).toggleClass("select");
    });
    $("#checkAll").on("click", function () {
      $(".chapter-item").toggleClass("select");
    });
    $("#ignore_index").on("change", function () {
      var ind = +$(this).val();
      $(".chapter-item").map(function () {
        let $t = $(this);
        if (+$t.attr("data-id") < ind) {
          $t.addClass("disable");
        } else {
          $t.removeClass("disable");
        }
      });
    });
    $("#subscribe").on("click", function () {
      let subscribe_list = [
        ...$(".chapter-item.select").map(function () {
          return $(this).attr("data-id");
        }),
      ];
      let data = {
        url: window.injectData.page_url,
        ignore_index: +$("#ignore_index").val(),
      };
      if (subscribe_list.length) {
        data.subscribe_list = subscribe_list.join(",");
      }
      $.ajax({
        url: "/subscribe",
        method: "POST",
        data: data,
      }).done(function (res) {
        if (res.result) {
          showMsg("订阅成功");
        } else {
          showMsg("Error:" + res.msg);
        }
      });
    });
  }
});
