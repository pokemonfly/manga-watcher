function renderNav() {
  return `<div class='nav'>
    <a href="/">返回首页</a>
  </div>`;
}

function showMsg(str) {
  let id = "mb-" + Math.random().toString(16).substr(2);
  let html = `
  <div class="msg-bar" id='${id}'>
    ${str}
  </div>
  `;
  $("body").append(html);
  setTimeout(() => {
    $(`#${id}`).remove();
  }, 2000);
}
