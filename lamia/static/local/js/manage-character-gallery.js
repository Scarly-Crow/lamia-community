// Generated by CoffeeScript 1.12.7
(function() {
  $(function() {
    Dropzone.autoDiscover = false;
    $(".add-dropzone").append("<div class=\"dropzone\"></div>");
    $(".dropzone").dropzone({
      url: window.location + "/attach",
      dictDefaultMessage: "Click here or drop a file in to upload (image files only).",
      acceptedFiles: "image/jpeg,image/jpg,image/png,image/gif",
      maxFilesize: 30,
      init: function() {
        return this.on("success", function(file, response) {
          return window.location = window.location;
        });
      }
    });
    $(".save-button").click(function(e) {
      var data, element, pk;
      element = $(this);
      element.addClass("disabled");
      pk = element.parent().parent().data("image");
      data = {
        pk: pk,
        caption: element.parent().parent().find(".caption-for").val(),
        source: element.parent().parent().find(".source-of").val(),
        author: element.parent().parent().find(".created-by").val()
      };
      return $.post(window.location + "/edit-image", JSON.stringify(data), function(data) {
        element.addClass("btn-success");
        element.text("Saved!");
        return setTimeout(function() {
          element.removeClass("btn-success");
          element.removeClass("disabled");
          return element.text("Save");
        }, 1000);
      });
    });
    $(".toggle-default-avatar-button").click(function(e) {
      var data, element;
      element = $(this);
      $(".toggle-default-avatar-button").removeClass("btn-success");
      $(".toggle-default-avatar-button").removeClass("disabled");
      $(".toggle-default-avatar-button").text("Make Default Avatar");
      element.addClass("btn-success");
      element.addClass("disabled");
      element.text("Default Avatar");
      data = {
        pk: element.parent().parent().data("image")
      };
      return $.post(window.location + "/make-default-avatar", JSON.stringify(data), function(data) {});
    });
    $(".toggle-emote-button").click(function(e) {
      var data, element;
      element = $(this);
      if (element.data("status") === "yes") {
        element.text("Add to Avatars");
        element.removeClass("btn-success");
        element.addClass("btn-default");
        element.data("status", "no");
      } else {
        element.text("Remove from Avatars");
        element.removeClass("btn-default");
        element.addClass("btn-success");
        element.data("status", "yes");
      }
      data = {
        pk: element.parent().parent().data("image")
      };
      return $.post(window.location + "/toggle-emote", JSON.stringify(data), function(data) {});
    });
    $(".delete-button").click(function(e) {
      var element;
      element = $(this);
      element.addClass("disabled");
      return element.next(".confirm-delete").show();
    });
    $(".confirm-delete").click(function(e) {
      var data, element;
      element = $(this);
      data = {
        pk: element.parent().parent().data("image")
      };
      return $.post(window.location + "/remove-image", JSON.stringify(data), function(data) {
        return window.location = window.location;
      });
    });
    return $(".toggle-default-profile-button").click(function(e) {
      var data, element;
      element = $(this);
      $(".toggle-default-profile-button").removeClass("btn-success");
      $(".toggle-default-profile-button").removeClass("disabled");
      $(".toggle-default-profile-button").text("Make Default Profile Image");
      element.addClass("btn-success");
      element.addClass("disabled");
      element.text("Default Profile Image");
      data = {
        pk: element.parent().parent().data("image")
      };
      return $.post(window.location + "/make-default-profile", JSON.stringify(data), function(data) {});
    });
  });

}).call(this);
