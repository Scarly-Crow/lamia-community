$ ->
  window.RegisterAttachmentContainer = (selector) ->
    imgModalHTML = () ->
      return """
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title">Full Image?</h4>
          </div>
          <div class="modal-body">
            Would you like to view the full image? It is about <span id="img-click-modal-size"></span>KB in size.
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" id="show-full-image">Yes</button>
            <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
      """
      
    gifModalHTML = () ->
      return """
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title">Play GIF?</h4>
          </div>
          <div class="modal-body">
            Would you like to play this gif image? It is about <span id="img-click-modal-size"></span>KB in size.
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" id="show-full-image">Play</button>
            <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
          </div>
        </div>
      </div>
      """
    
    $(selector).delegate ".attachment-image", "click", (e) ->
      e.preventDefault()
      element = $(this)
      if element.data("first_click") == "yes"
        element.attr("original_src", element.attr("src"))
        element.data("first_click", "no")
      element.attr("src", element.attr("original_src"))
      if element.data("show_box") == "no"
        return false
      url = element.data("url")
      extension = url.split(".")[url.split(".").length-1]
      size = element.data("size")
      $("#img-click-modal").modal('hide')
      if extension == "gif" and parseInt(size) > 1024
        $("#img-click-modal").html gifModalHTML()
        $("#img-click-modal").data("biggif", true)
        $("#img-click-modal").data("original_element", element)
        $("#img-click-modal-size").html(element.data("size"))
        $("#img-click-modal").modal('show')
      else
        $("#img-click-modal").html imgModalHTML()
        $("#img-click-modal").data("full_url", element.data("url"))
        $("#img-click-modal-size").html(element.data("size"))
        $("#img-click-modal").data("original_element", element)
        $("#img-click-modal").modal('show')
        $("#img-click-modal").data("biggif", false)
      
    $("#img-click-modal").delegate "#show-full-image", "click", (e) ->
      e.preventDefault()
      unless $("#img-click-modal").data("biggif")
        window.open($("#img-click-modal").data("full_url"), "_blank")
        $("#img-click-modal").modal('hide')
      else
        element = $("#img-click-modal").data("original_element")
        element.attr("src", element.attr("src").replace(".gif", ".animated.gif"))
        $("#img-click-modal").modal('hide')
        
      