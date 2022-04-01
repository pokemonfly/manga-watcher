function render(data) {
  const { page_num, page_count, list } = data;
  let page_limit = page_count;
  let usp = new URLSearchParams(location.search);
  usp.set("page_num", page_num + 1);
  let page_info = `<div class="page-info">
    第${page_num}页, 共${page_limit}页
    ${
      page_num < page_limit
        ? `<a href="${`/search?${usp.toString()}`}">下一页</a>`
        : ""
    }
    </div>`;
  return `<div>
    ${page_info}
    <div class="search-list">
      ${list
        .map((item) => {
          return `<div class="search-item">
            <img src='${item.cover}'/>
            <div>
              <div class="title">${item.title}</div>
              <div class="author">${item.author}</div>
              <a href=${`/comic_preview?url=${encodeURIComponent(
                item.page_url
              )}`}>预览</a>
            </div>
          </div>`;
        })
        .join("")}
    </div>
    ${page_info}
  </div>`;
}
$(function () {
  if (window.injectData) {
    $("#main").html([renderNav(), render(window.injectData)]);
  }
});
