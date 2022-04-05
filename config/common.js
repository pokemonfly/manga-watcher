window.getXpath = function (e) {
  var i = e;
  if (i && i.id) return '//*[@id="' + i.id + '"]';
  for (var n = []; i && Node.ELEMENT_NODE === i.nodeType; ) {
    for (var r = 0, o = !1, d = i.previousSibling; d; )
      d.nodeType !== Node.DOCUMENT_TYPE_NODE &&
        d.nodeName === i.nodeName &&
        r++,
        (d = d.previousSibling);
    for (d = i.nextSibling; d; ) {
      if (d.nodeName === i.nodeName) {
        o = !0;
        break;
      }
      d = d.nextSibling;
    }
    n.push(
      (i.prefix ? i.prefix + ":" : "") +
        i.localName +
        (r || o ? "[" + (r + 1) + "]" : "")
    ),
      (i = i.parentNode);
  }
  return n.length ? "/" + n.reverse().join("/") : "";
};

window.getBase64 = function (src) {
  return new Promise((res) => {
    let image = new Image();
    image.src = src;
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    image.onload = () => {
      canvas.width = image.width;
      canvas.height = image.height;
      context.drawImage(image, 0, 0);
      res(canvas.toDataURL().replace("data:image/png;base64,", ""));
    };
  });
};
