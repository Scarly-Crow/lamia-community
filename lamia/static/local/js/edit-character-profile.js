// Generated by CoffeeScript 1.12.7
(function() {
  $(function() {
    var other_editor;
    other_editor = new InlineEditor("#character-other");
    other_editor.noSaveButton();
    window.onbeforeunload = function() {
      if (!window.save) {
        return "You haven't saved your changes.";
      }
    };
    return $("form").submit(function(e) {
      window.save = true;
      $("#other").val(other_editor.getHTML());
      return true;
    });
  });

}).call(this);
