$(function () {
  $("#syncNow").on("click", () => {
    $.ajax({
      url: "/api/sync_now",
    }).done(function (res) {
      showMsg("操作成功");
    });
  });
  $("#freshHtml").on("click", () => {
    $.ajax({
      url: "/api/freshHtml",
    }).done(function (res) {
      showMsg("操作成功");
    });
  });
  $("#openUrl").on("click", () => {
    window.location.href = $("#origin").val();
  });
});
