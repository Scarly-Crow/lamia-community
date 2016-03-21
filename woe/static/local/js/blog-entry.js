// Generated by CoffeeScript 1.10.0
(function() {
  $(function() {
    var inline_editor;
    $(".boop-link").click(function(e) {
      var count, current_status, element;
      e.preventDefault();
      element = $(this);
      current_status = element.data("status");
      count = parseInt(element.data("count"));
      return $.post(element.attr("href"), JSON.stringify({}), function(data) {
        if (current_status === "notbooped") {
          element.children(".boop-text").html("<img src=\"/static/emoticons/brohoof_by_angelishi-d6wk2et.gif\">");
          element.children(".badge").text("");
          element.data("status", "booped");
          return element.data("count", count + 1);
        } else {
          element.children(".boop-text").html("");
          element.data("status", "notbooped");
          element.children(".boop-text").text(" Boop!");
          element.data("count", count - 1);
          element.children(".badge").text(element.data("count"));
          return element.children(".badge").css("background-color", "#555");
        }
      });
    });
    if ($("#new-post-box").length > 0) {
      inline_editor = new InlineEditor("#new-post-box", "", false, false, 150);
      return inline_editor.onSave(function(html, text) {
        inline_editor.disableSaveButton();
        return $.post($("#entry-url").attr("href") + "/new-comment", JSON.stringify({
          post: html,
          text: text
        }), (function(_this) {
          return function(data) {
            if (data.no_content != null) {
              inline_editor.flashError("You forgot to write something.");
            }
            if (data.error != null) {
              inline_editor.flashError(data.error);
            }
            if (data.success != null) {
              inline_editor.clearEditor();
              return window.location = data.url;
            } else {
              return inline_editor.enableSaveButton();
            }
          };
        })(this));
      });
    }
  });

}).call(this);