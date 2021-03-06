// Generated by CoffeeScript 1.12.7
(function() {
  $(function() {
    var inline_editor;
    if ($("#new-comment-box").length > 0) {
      inline_editor = new InlineEditor("#new-comment-box", "", false, false, 150);
      return inline_editor.onSave(function(html, text) {
        inline_editor.disableSaveButton();
        return $.post("/admin/report/new-comment/" + $("#new-comment-box").attr("data-id"), JSON.stringify({
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
              return location.reload()();
            } else {
              return inline_editor.enableSaveButton();
            }
          };
        })(this));
      });
    }
  });

}).call(this);
