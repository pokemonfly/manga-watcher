$(function () {
  $("#syncNow").on("click", () => {
    $.ajax({
      url: "/sync_now",
    }).done(function (res) {
      showMsg("操作成功");
    });
  });
});
