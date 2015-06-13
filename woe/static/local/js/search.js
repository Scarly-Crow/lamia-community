// Generated by CoffeeScript 1.9.3
(function() {
  $(function() {
    var max_pages, page, paginationHTMLTemplate, paginationTemplate, resultTemplate, resultTemplateHTML, updateSearch;
    $(".variable-option").hide();
    $(".posts-option").show();
    page = 1;
    max_pages = 1;
    $("#start-date").datepicker({
      format: "m/d/yy",
      clearBtn: true
    });
    $("#end-date").datepicker({
      format: "m/d/yy",
      clearBtn: true
    });
    $("#content-search").change(function(e) {
      var content_type;
      content_type = $(this).val();
      if (content_type === "posts") {
        $(".variable-option").hide();
        return $(".posts-option").show();
      } else if (content_type === "topics") {
        $(".variable-option").hide();
        return $(".topics-option").show();
      } else if (content_type === "status") {
        return $(".variable-option").hide();
      } else if (content_type === "messages") {
        $(".variable-option").hide();
        return $(".messages-option").show();
      }
    });
    $("#author-select").select2({
      ajax: {
        url: "/user-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#topic-select").select2({
      ajax: {
        url: "/topic-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#category-select").select2({
      ajax: {
        url: "/category-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    $("#pm-topic-select").select2({
      ajax: {
        url: "/pm-topic-list-api",
        dataType: 'json',
        delay: 250,
        data: function(params) {
          return {
            q: params.term
          };
        },
        processResults: function(data, page) {
          console.log({
            results: data.results
          });
          return {
            results: data.results
          };
        },
        cache: true
      },
      minimumInputLength: 2
    });
    resultTemplateHTML = function() {
      return "<ul class=\"list-group\">\n  <li class=\"list-group-item\">\n    <p>\n      <b>\n        <a href=\"{{url}}\" class=\"search-result-title\">{{{title}}}</a>\n      </b>\n    </p>\n    <div class=\"search-result-content\">\n        {{{description}}}\n        {{#if readmore}}\n        <a href=\"{{url}}\" class=\"readmore\">\n          <br><b>Read more »</b><br>\n        </a>\n        {{/if}}\n    </div>\n    <p class=\"text-muted\">by <a href=\"{{author_profile_link}}\">{{author_name}}</a> - {{time}}\n    </p>\n  </li>\n</ul>";
    };
    resultTemplate = Handlebars.compile(resultTemplateHTML());
    paginationHTMLTemplate = function() {
      return "<ul class=\"pagination\">\n  <li>\n    <a href=\"#\" aria-label=\"Start\" id=\"go-to-start\">\n      <span aria-hidden=\"true\">Go to Start</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"#\" aria-label=\"Previous\" id=\"previous-page\">\n      <span aria-hidden=\"true\">&laquo;</span>\n    </a>\n  </li>\n  {{#each pages}}\n  <li><a href=\"#\" class=\"change-page page-link-{{this}}\">{{this}}</a></li>\n  {{/each}}\n  <li>\n    <a href=\"#\" aria-label=\"Next\" id=\"next-page\">\n      <span aria-hidden=\"true\">&raquo;</span>\n    </a>\n  </li>\n  <li>\n    <a href=\"#\" aria-label=\"End\" id=\"go-to-end\">\n      <span aria-hidden=\"true\">Go to End</span>\n    </a>\n  </li>\n</ul>";
    };
    paginationTemplate = Handlebars.compile(paginationHTMLTemplate());
    updateSearch = function() {
      var content_type, data;
      content_type = $("#content-search").val();
      data = {
        q: $("#search-for").val(),
        content_type: content_type,
        page: page
      };
      if ($("#start-date").val() !== "") {
        data["start_date"] = $("#start-date").val();
      }
      if ($("#end-date").val() !== "") {
        data["end_date"] = $("#end-date").val();
      }
      if (content_type === "messages") {
        data["topics"] = $("#pm-topic-select").val();
      }
      if (content_type === "posts") {
        data["topics"] = $("#topic-select").val();
      }
      if (content_type === "topics") {
        data["categories"] = $("#category-select").val();
      }
      return $.post("/search", JSON.stringify(data), function(data) {
        var _html, i, j, k, l, len, len1, m, n, pages, pagination_html, ref, ref1, ref2, ref3, ref4, ref5, result, results, results1, results2, results3, term, term_re, terms;
        _html = "";
        ref = data.results;
        for (i = 0, len = ref.length; i < len; i++) {
          result = ref[i];
          _html = _html + resultTemplate(result).replace("img", "i");
        }
        $("#search-results-buffer").html(_html);
        $("#search-results-buffer").find("br").remove();
        $("#search-results").html($("#search-results-buffer").html());
        $("#search-results-buffer").html("");
        $(".search-result-content").dotdotdot({
          height: 200,
          after: ".readmore"
        });
        terms = $("#search-for").val().split(" ");
        for (j = 0, len1 = terms.length; j < len1; j++) {
          term = terms[j];
          term = term.trim();
          if (term === "") {
            continue;
          }
          term_re = new RegExp("(.*?>?.*)(" + term + "?)(.*<?.*?)", "gi");
          $(".search-result-title").each(function() {
            return $(this).html($(this).html().replace(term_re, "$1<span style=\"background-color: yellow\">" + "$2" + "</span>$3"));
          });
          $(".search-result-content p").each(function() {
            return $(this).html($(this).html().replace(term_re, "$1<span style=\"background-color: yellow\">" + "$2" + "</span>$3"));
          });
          $(".search-result-content blockquote").each(function() {
            return $(this).html($(this).html().replace(term_re, "$1<span style=\"background-color: yellow\">" + "$2" + "</span>$3"));
          });
        }
        pages = [];
        max_pages = Math.ceil(data.count / data.pagination);
        if (max_pages > 5) {
          if (page > 3 && page < max_pages - 5) {
            pages = (function() {
              results = [];
              for (var k = ref1 = page - 2, ref2 = page + 5; ref1 <= ref2 ? k <= ref2 : k >= ref2; ref1 <= ref2 ? k++ : k--){ results.push(k); }
              return results;
            }).apply(this);
          } else if (page > 3) {
            pages = (function() {
              results1 = [];
              for (var l = ref3 = page - 2; ref3 <= max_pages ? l <= max_pages : l >= max_pages; ref3 <= max_pages ? l++ : l--){ results1.push(l); }
              return results1;
            }).apply(this);
          } else if (page <= 3) {
            pages = (function() {
              results2 = [];
              for (var m = 1, ref4 = page + 5; 1 <= ref4 ? m <= ref4 : m >= ref4; 1 <= ref4 ? m++ : m--){ results2.push(m); }
              return results2;
            }).apply(this);
          }
        } else {
          pages = (function() {
            results3 = [];
            for (var n = 1, ref5 = Math.ceil(data.count / data.pagination); 1 <= ref5 ? n <= ref5 : n >= ref5; 1 <= ref5 ? n++ : n--){ results3.push(n); }
            return results3;
          }).apply(this);
        }
        pagination_html = paginationTemplate({
          pages: pages
        });
        $(".search-pagination").html(pagination_html);
        $("#results-header").text(data.count + " Search Results");
        return $(".page-link-" + page).parent().addClass("active");
      });
    };
    $("#search").click(function(e) {
      e.preventDefault();
      page = 1;
      return updateSearch();
    });
    $("form").submit(function(e) {
      e.preventDefault();
      return $("#search").click();
    });
    $(".search-pagination").delegate("#next-page", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      if (page !== max_pages) {
        $(".change-page").parent().removeClass("active");
        page++;
        return updateSearch();
      }
    });
    $(".search-pagination").delegate("#previous-page", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      if (page !== 1) {
        $(".change-page").parent().removeClass("active");
        page--;
        return updateSearch();
      }
    });
    $(".search-pagination").delegate("#go-to-end", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      page = parseInt(max_pages);
      return updateSearch();
    });
    $(".search-pagination").delegate(".change-page", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      page = parseInt(element.text());
      return updateSearch();
    });
    return $(".search-pagination").delegate("#go-to-start", "click", function(e) {
      var element;
      e.preventDefault();
      element = $(this);
      page = 1;
      return updateSearch();
    });
  });

}).call(this);