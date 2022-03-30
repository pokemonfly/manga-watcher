function render(data) {
  let { comic_id, chapter_id, page_count } = data;
  return `<div class="image-list">
    ${[...Array(page_count).keys()].map(
      (i) => `
      <img src="image/${comic_id}/${chapter_id}/${i}.png" />
    `
    )}
  </div>`;
}
$(function () {
  if (window.injectData) {
    $("#main").html([renderNav(), render(window.injectData)]);
  }
});
