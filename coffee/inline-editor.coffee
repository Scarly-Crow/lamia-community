$ ->
  class InlineEditor
    constructor: (element, url = "", fullpage_option=false) ->
      @quillID = do @getQuillID  
      @element = $(element)
      if @element.data("editor_is_active")
        return false
      @element.data("editor_is_active", true)
      
      if url != ""
        $.get url, (data) =>
          @element.data("editor_initial_html", data.content)
          @setupEditor fullpage_option
      else
        @element.data("editor_initial_html", @element.html())
        @setupEditor fullpage_option
        
    
    setupEditor: (fullpage_option=false) =>
      @element.html(@editordivHTML())
      
      @element.before @toolbarHTML
      @element.after @submitButtonHTML fullpage_option
      
      quill = new Quill "#post-editor-#{@quillID}", 
        modules:
          'link-tooltip': true
          'image-tooltip': true
          'toolbar': { container: "#toolbar-#{@quillID}" }
        theme: 'snow'
        
      quill.setHTML @element.data("editor_initial_html")
      
      @element.data("editor", quill)
      
      $("#save-text-#{@quillID}").click (e) =>
        e.preventDefault()
        if @saveFunction?
          @saveFunction @element.data("editor").getHTML()
        
      $("#cancel-edit-#{@quillID}").click (e) =>
        e.preventDefault()
        if @cancelFunction?
          @cancelFunction @element.data("editor").getHTML()
    
    getQuillID: () ->
      return Quill.editors.length+1
    
    resetElementHtml: () ->
      @element.html(@element.data("editor_initial_html"))
    
    onSave: (saveFunction) ->
      @saveFunction = saveFunction
    
    onCancel: (cancelFunction) ->
      @cancelFunction = cancelFunction
    
    onFullPage: (fullPageFunction) ->
      @fullPageFunction = fullPageFunction
    
    destroyEditor: () ->
      @element.data("editor_is_active", false)
      do $("#inline-editor-buttons-#{@quillID}").remove
      do $("#toolbar-#{@quillID}").remove
      do $("#post-editor-#{@quillID}").remove
    
    submitButtonHTML: (fullpage_option=False) =>
      if fullpage_option == true
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default post-post" id="save-text-#{@quillID}">Save</button>
            <button type="button" class="btn btn-default" id="cancel-edit-#{@quillID}">Cancel</button>
            <button type="button" class="btn btn-default" id="fullpage-edit-#{@quillID}">Full Page Editor</button>
          </div>
        """
      else
        return """
          <div id="inline-editor-buttons-#{@quillID}" class="inline-editor-buttons">
            <button type="button" class="btn btn-default" id="save-text-#{@quillID}">Save</button>
            <button type="button" class="btn btn-default" id="cancel-edit-#{@quillID}">Cancel</button>
          </div>
        """
    
    editordivHTML: () =>
      return """
        <div id="post-editor-#{@quillID}" class="editor-box" data-placeholder=""></div>
      """
    
    toolbarHTML: () =>
      return """
        <div id="toolbar-#{@quillID}" class="toolbar">
          <span class="ql-format-group">
            <select title="Font" class="ql-font">
              <option value="sans-serif" selected>Sans Serif</option>
              <option value="serif">Serif</option>
              <option value="monospace">Monospace</option>
            </select>
            <select title="Size" class="ql-size">
              <option value="8px">Micro</option>
              <option value="10px">Small</option>
              <option value="14px" selected>Normal</option>
              <option value="18px">Large</option>
              <option value="24px">Larger</option>
              <option value="32px">Huge</option>
            </select>
          </span>
          <span class="ql-format-group">
            <span title="Bold" class="ql-format-button ql-bold"></span>
            <span class="ql-format-separator"></span>
            <span title="Italic" class="ql-format-button ql-italic"></span>
            <span class="ql-format-separator"></span>
            <span title="Underline" class="ql-format-button ql-underline"></span>
            <span class="ql-format-separator"></span>
            <span title="Strikethrough" class="ql-format-button ql-strike"></span>
          </span>
          <span class="ql-format-group">
            <select title="Text Color" class="ql-color">
              <option value="rgb(0, 0, 0)" label="rgb(0, 0, 0)" selected></option>
              <option value="rgb(230, 0, 0)" label="rgb(230, 0, 0)"></option>
              <option value="rgb(255, 153, 0)" label="rgb(255, 153, 0)"></option>
              <option value="rgb(255, 255, 0)" label="rgb(255, 255, 0)"></option>
              <option value="rgb(0, 138, 0)" label="rgb(0, 138, 0)"></option>
              <option value="rgb(0, 102, 204)" label="rgb(0, 102, 204)"></option>
              <option value="rgb(153, 51, 255)" label="rgb(153, 51, 255)"></option>
              <option value="rgb(255, 255, 255)" label="rgb(255, 255, 255)"></option>
              <option value="rgb(250, 204, 204)" label="rgb(250, 204, 204)"></option>
              <option value="rgb(255, 235, 204)" label="rgb(255, 235, 204)"></option>
              <option value="rgb(255, 255, 204)" label="rgb(255, 255, 204)"></option>
              <option value="rgb(204, 232, 204)" label="rgb(204, 232, 204)"></option>
              <option value="rgb(204, 224, 245)" label="rgb(204, 224, 245)"></option>
              <option value="rgb(235, 214, 255)" label="rgb(235, 214, 255)"></option>
              <option value="rgb(187, 187, 187)" label="rgb(187, 187, 187)"></option>
              <option value="rgb(240, 102, 102)" label="rgb(240, 102, 102)"></option>
              <option value="rgb(255, 194, 102)" label="rgb(255, 194, 102)"></option>
              <option value="rgb(255, 255, 102)" label="rgb(255, 255, 102)"></option>
              <option value="rgb(102, 185, 102)" label="rgb(102, 185, 102)"></option>
              <option value="rgb(102, 163, 224)" label="rgb(102, 163, 224)"></option>
              <option value="rgb(194, 133, 255)" label="rgb(194, 133, 255)"></option>
              <option value="rgb(136, 136, 136)" label="rgb(136, 136, 136)"></option>
              <option value="rgb(161, 0, 0)" label="rgb(161, 0, 0)"></option>
              <option value="rgb(178, 107, 0)" label="rgb(178, 107, 0)"></option>
              <option value="rgb(178, 178, 0)" label="rgb(178, 178, 0)"></option>
              <option value="rgb(0, 97, 0)" label="rgb(0, 97, 0)"></option>
              <option value="rgb(0, 71, 178)" label="rgb(0, 71, 178)"></option>
              <option value="rgb(107, 36, 178)" label="rgb(107, 36, 178)"></option>
              <option value="rgb(68, 68, 68)" label="rgb(68, 68, 68)"></option>
              <option value="rgb(92, 0, 0)" label="rgb(92, 0, 0)"></option>
              <option value="rgb(102, 61, 0)" label="rgb(102, 61, 0)"></option>
              <option value="rgb(102, 102, 0)" label="rgb(102, 102, 0)"></option>
              <option value="rgb(0, 55, 0)" label="rgb(0, 55, 0)"></option>
              <option value="rgb(0, 41, 102)" label="rgb(0, 41, 102)"></option>
              <option value="rgb(61, 20, 102)" label="rgb(61, 20, 102)"></option>
            </select>
            <span class="ql-format-separator"></span>
            <select title="Background Color" class="ql-background">
              <option value="rgb(0, 0, 0)" label="rgb(0, 0, 0)"></option>
              <option value="rgb(230, 0, 0)" label="rgb(230, 0, 0)"></option>
              <option value="rgb(255, 153, 0)" label="rgb(255, 153, 0)"></option>
              <option value="rgb(255, 255, 0)" label="rgb(255, 255, 0)"></option>
              <option value="rgb(0, 138, 0)" label="rgb(0, 138, 0)"></option>
              <option value="rgb(0, 102, 204)" label="rgb(0, 102, 204)"></option>
              <option value="rgb(153, 51, 255)" label="rgb(153, 51, 255)"></option>
              <option value="rgb(255, 255, 255)" label="rgb(255, 255, 255)" selected></option>
              <option value="rgb(250, 204, 204)" label="rgb(250, 204, 204)"></option>
              <option value="rgb(255, 235, 204)" label="rgb(255, 235, 204)"></option>
              <option value="rgb(255, 255, 204)" label="rgb(255, 255, 204)"></option>
              <option value="rgb(204, 232, 204)" label="rgb(204, 232, 204)"></option>
              <option value="rgb(204, 224, 245)" label="rgb(204, 224, 245)"></option>
              <option value="rgb(235, 214, 255)" label="rgb(235, 214, 255)"></option>
              <option value="rgb(187, 187, 187)" label="rgb(187, 187, 187)"></option>
              <option value="rgb(240, 102, 102)" label="rgb(240, 102, 102)"></option>
              <option value="rgb(255, 194, 102)" label="rgb(255, 194, 102)"></option>
              <option value="rgb(255, 255, 102)" label="rgb(255, 255, 102)"></option>
              <option value="rgb(102, 185, 102)" label="rgb(102, 185, 102)"></option>
              <option value="rgb(102, 163, 224)" label="rgb(102, 163, 224)"></option>
              <option value="rgb(194, 133, 255)" label="rgb(194, 133, 255)"></option>
              <option value="rgb(136, 136, 136)" label="rgb(136, 136, 136)"></option>
              <option value="rgb(161, 0, 0)" label="rgb(161, 0, 0)"></option>
              <option value="rgb(178, 107, 0)" label="rgb(178, 107, 0)"></option>
              <option value="rgb(178, 178, 0)" label="rgb(178, 178, 0)"></option>
              <option value="rgb(0, 97, 0)" label="rgb(0, 97, 0)"></option>
              <option value="rgb(0, 71, 178)" label="rgb(0, 71, 178)"></option>
              <option value="rgb(107, 36, 178)" label="rgb(107, 36, 178)"></option>
              <option value="rgb(68, 68, 68)" label="rgb(68, 68, 68)"></option>
              <option value="rgb(92, 0, 0)" label="rgb(92, 0, 0)"></option>
              <option value="rgb(102, 61, 0)" label="rgb(102, 61, 0)"></option>
              <option value="rgb(102, 102, 0)" label="rgb(102, 102, 0)"></option>
              <option value="rgb(0, 55, 0)" label="rgb(0, 55, 0)"></option>
              <option value="rgb(0, 41, 102)" label="rgb(0, 41, 102)"></option>
              <option value="rgb(61, 20, 102)" label="rgb(61, 20, 102)"></option>
            </select>
          </span>
          <span class="ql-format-group">
            <span title="List" class="ql-format-button ql-list"></span>
            <span class="ql-format-separator"></span>
            <span title="Bullet" class="ql-format-button ql-bullet"></span>
            <span class="ql-format-separator"></span>
            <select title="Text Alignment" class="ql-align">
              <option value="left" label="Left" selected></option>
              <option value="center" label="Center"></option>
              <option value="right" label="Right"></option>
              <option value="justify" label="Justify"></option>
            </select>
          </span>
          <span class="ql-format-group">
            <span title="Link" class="ql-format-button ql-link"></span>
            <span class="ql-format-separator"></span>
            <span title="Image" class="ql-format-button ql-image"></span>
          </span>
        </div>
      """
      
  window.InlineEditor = InlineEditor