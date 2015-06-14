// Generated by CoffeeScript 1.9.3
(function() {
  $(function() {
    return window.RegisterAttachmentContainer = function(selector) {
      var gifModalHTML, imgModalHTML;
      imgModalHTML = function() {
        return "<div class=\"modal-dialog\">\n  <div class=\"modal-content\">\n    <div class=\"modal-header\">\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n      <h4 class=\"modal-title\">Full Image?</h4>\n    </div>\n    <div class=\"modal-body\">\n      Would you like to view the full image? It is about <span id=\"img-click-modal-size\"></span>KB in size.\n    </div>\n    <div class=\"modal-footer\">\n      <button type=\"button\" class=\"btn btn-primary\" id=\"show-full-image\">Yes</button>\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n    </div>\n  </div>\n</div>";
      };
      gifModalHTML = function() {
        return "<div class=\"modal-dialog\">\n  <div class=\"modal-content\">\n    <div class=\"modal-header\">\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>\n      <h4 class=\"modal-title\">Play GIF?</h4>\n    </div>\n    <div class=\"modal-body\">\n      Would you like to play this gif image? It is about <span id=\"img-click-modal-size\"></span>KB in size.\n    </div>\n    <div class=\"modal-footer\">\n      <button type=\"button\" class=\"btn btn-primary\" id=\"show-full-image\">Play</button>\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Cancel</button>\n    </div>\n  </div>\n</div>";
      };
      $(selector).delegate(".attachment-image", "click", function(e) {
        var element, extension, size, url;
        e.preventDefault();
        element = $(this);
        if (element.data("first_click") === "yes") {
          element.attr("original_src", element.attr("src"));
          element.data("first_click", "no");
        }
        element.attr("src", element.attr("original_src"));
        if (element.data("show_box") === "no") {
          return false;
        }
        url = element.data("url");
        extension = url.split(".")[url.split(".").length - 1];
        size = element.data("size");
        $("#img-click-modal").modal('hide');
        if (extension === "gif" && parseInt(size) > 1024) {
          $("#img-click-modal").html(gifModalHTML());
          $("#img-click-modal").data("biggif", true);
          $("#img-click-modal").data("original_element", element);
          $("#img-click-modal-size").html(element.data("size"));
          return $("#img-click-modal").modal('show');
        } else {
          $("#img-click-modal").html(imgModalHTML());
          $("#img-click-modal").data("full_url", element.data("url"));
          $("#img-click-modal-size").html(element.data("size"));
          $("#img-click-modal").data("original_element", element);
          $("#img-click-modal").modal('show');
          return $("#img-click-modal").data("biggif", false);
        }
      });
      return $("#img-click-modal").delegate("#show-full-image", "click", function(e) {
        var element;
        e.preventDefault();
        if (!$("#img-click-modal").data("biggif")) {
          window.open($("#img-click-modal").data("full_url"), "_blank");
          return $("#img-click-modal").modal('hide');
        } else {
          element = $("#img-click-modal").data("original_element");
          element.attr("src", element.attr("src").replace(".gif", ".animated.gif"));
          return $("#img-click-modal").modal('hide');
        }
      });
    };
  });

}).call(this);
