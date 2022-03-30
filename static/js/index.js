function renderForm() {
  return `
    <div class='index-form'>
      <form action="/comic_preview" method="get">
        <fieldset>
          <legend>预览URL</legend>
          <div class="row">
            <input type="text" name="url" id="url" />
            <button type="submit">确定</button>
          </div>
        </fieldset>
      </form>
    </div>
  
    <div class='index-form'>
      <form action="/search" method="get">
        <fieldset>
          <legend>检索</legend>
          <div class="row">
            <input type="text" name="keyword" id="keyword" />
            <button type="submit">确定</button>
          </div>
        </fieldset>
      </form>

    </div>
    <div class='btn-row'>
      <button id='syncNow'>恢复任务</button>
    </div>
  `;
}

function renderList(data) {
  return `<div class='comic-list'>
    <div class="comic-hint">已订阅章节</div>
    ${data
      .map((c) => {
        return `
        <div class='comic-item' data-id='${c.id}'>
          <img src="image/${c.cover}">
          <div>
            <div class="title">${c.title}</div>
            <div class="sub author">${c.author}</div>
            <div class="sub last_update">${c.last_update}</div>
            <a href='comic?id=${c.id}'>查看详情</a>
          </div>
        </div>
      `;
      })
      .join("")}
  </div>`;
}
$(function () {
  if (window.injectData) {
    $("#main").html([renderForm(), renderList(window.injectData)]);
    $("#syncNow").on("click", () => {
      $.ajax({
        url: "/sync_now",
      }).done(function (res) {
        showMsg("操作成功");
      });
    });
  }
});
