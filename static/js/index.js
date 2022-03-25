function render() {
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
  `;
}
$(function () {
  if (window.injectData) {
    $("#main").html(render());
  }
});
