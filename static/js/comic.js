$(function () {
  $(".chapter-item").on("click", function () {
    let state = $(this).attr("data-state");
    let url = $(this).attr("data-url");
    if (state == 2) {
      location.href = url;
    } else if (state != 1) {
      $(this).toggleClass("select");
    }
  });

  $("#unsubscribe").on("click", function () {
    $.ajax({
      url: "/unsubscribe",
      method: "POST",
      data: {
        id: $("#id").val(),
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
        id: $("#id").val(),
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
});
