$(function () {
  $(".image-item").on("click", function () {
    let $t = $(this);
    let url = $t.attr("data-src");
    $t.html(`<img src='${url}'/>`);
  });

  setTimeout(() => {
    $(".image-item").eq(0).click();
    $.ajax({
      url: "/bookmark",
      data: {
        chapter_id: $("#chapter_id").val(),
        comic_id: $("#comic_id").val(),
      },
    });
  }, 500);
});
