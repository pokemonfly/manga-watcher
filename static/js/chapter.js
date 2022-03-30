function render(data) {
  let { comic_id, chapter_id, page_count } = data;
  return `
  <div class="comic-hint">
    共<span class="page_count">${page_count}</span>页
  </div>
  <div class="image-list">
    ${[...Array(page_count).keys()].map(
      (i) => `<div class='image-item'>
        <img src="image/${comic_id}/${chapter_id}/${i}.png" />
      </div>
    `
    )}
  </div>`;
}
$(function () {
  if (window.injectData) {
    $("#main").html([renderNav(), render(window.injectData)]);
  }
});
