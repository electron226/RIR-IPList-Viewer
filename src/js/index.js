// Generated by CoffeeScript 1.6.3
(function() {
  var CClear, CReset, CTextReplace, CheckAllToggle, CheckBrowserIE, CustomTextPlus, FormCCClear, FormRegClear, GetInputIP, GetRowPoint, IPCheck, IPSearch, InputSearchIP, Less, LoadCircle, Pagination, SearchCircle, SearchCommonCloseBtnString, ShowTable, UpdateTable, WhoisSearch, before_selected, custom_area, default_custom_text, jsondata, pager, pagination_count, root, view_count, whois_url;

  view_count = 150;

  pagination_count = 5;

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  whois_url = "http://www.whoisxmlapi.com/whoisserver/WhoisService";

  $.fn.state = function(state) {
    var d;
    d = 'disabled';
    return this.each(function() {
      var $this;
      $this = $(this);
      $this.html($this.data()[state]);
      if (state === "loading") {
        return $this.addClass(d).prop(d, d);
      } else {
        return $this.removeClass(d).removeProp(d);
      }
    });
  };

  pager = null;

  jsondata = [];

  LoadCircle = $('#load_circle');

  UpdateTable = function(data) {
    var $this;
    LoadCircle.css('display', 'inline');
    $this = $(this);
    $this.state('loading');
    return $.ajax({
      url: '/json',
      data: data,
      type: 'GET',
      dataType: 'json',
      success: function(json, type) {
        var error, params;
        try {
          jsondata = json;
          ShowTable(0, view_count);
          params = {
            view_record: view_count,
            total_record: json.length,
            nav_count: pagination_count
          };
          return pager = $("#view_pages").pagination(params);
        } catch (_error) {
          error = _error;
          console.log(error);
          return alert(error);
        }
      },
      error: function() {
        return console.log('IP Search Error');
      },
      complete: function() {
        $this.state('complete');
        return LoadCircle.css('display', 'none');
      }
    });
  };

  root.GetViewTable = function(point) {
    ShowTable((point - 1) * view_count, point * view_count);
    return pager.MakeNavigator(point);
  };

  ShowTable = function(first, last) {
    var i, j, str, _i;
    str = "";
    j = 0;
    for (i = _i = first; first <= last ? _i < last : _i > last; i = first <= last ? ++_i : --_i) {
      if (jsondata[i] != null) {
        str += "<tr>";
        str += "<td>" + escape(jsondata[i].registry) + "</td>";
        str += "<td>" + escape(jsondata[i].country) + "</td>";
        str += "<td>" + escape(jsondata[i].StartIP) + "</td>";
        str += "<td>" + escape(jsondata[i].EndIP) + "</td>";
        str += "</tr>";
      }
    }
    return $("#viewbar tbody").html(str);
  };

  root.ChangeRow = function(num) {
    var params;
    view_count = num;
    $('#view_row .active').removeClass('active');
    $('#view_row li:eq(' + GetRowPoint(num) + ')').addClass('active');
    if (pager != null) {
      ShowTable(0, view_count);
      params = {
        view_record: view_count,
        total_record: pager.total_record,
        nav_count: pagination_count
      };
      return pager = $("#view_pages").pagination(params);
    }
  };

  GetRowPoint = function(num) {
    return (num / 50) - 1;
  };

  Less = function(x, y) {
    if (x < y) {
      return -1;
    }
    if (x > y) {
      return 1;
    }
    return 0;
  };

  before_selected = null;

  $('button.sort_item').click(function() {
    var $this, error, name, state;
    if (jsondata.length === 0) {
      return;
    }
    $this = $(this);
    name = this.name;
    if (before_selected !== name) {
      $this.prop('value', 'asc');
    }
    state = $this.prop('value');
    try {
      if (state === 'asc') {
        switch (name) {
          case 'sort_registry':
            jsondata.sort(function(x, y) {
              return Less(x.registry, y.registry);
            });
            break;
          case 'sort_country':
            jsondata.sort(function(x, y) {
              return Less(x.country, y.country);
            });
            break;
          case 'sort_ip_start':
            jsondata.sort(function(x, y) {
              return Less(x.start, y.start);
            });
            break;
          case 'sort_ip_end':
            jsondata.sort(function(x, y) {
              return Less(x.end, y.end);
            });
            break;
          default:
            throw "sort asc error.";
        }
        $this.prop('value', 'desc');
      } else {
        switch (name) {
          case 'sort_registry':
            jsondata.sort(function(x, y) {
              return Less(x.registry, y.registry) * -1;
            });
            break;
          case 'sort_country':
            jsondata.sort(function(x, y) {
              return Less(x.country, y.country) * -1;
            });
            break;
          case 'sort_ip_start':
            jsondata.sort(function(x, y) {
              return Less(x.start, y.start) * -1;
            });
            break;
          case 'sort_ip_end':
            jsondata.sort(function(x, y) {
              return Less(x.end, y.end) * -1;
            });
            break;
          default:
            throw "sort desc error.";
        }
        $this.prop('value', 'asc');
      }
      root.ChangeRow(view_count);
      return before_selected = name;
    } catch (_error) {
      error = _error;
      return console.log(error);
    }
  });

  $.fn.pagination = function(options) {
    options.elements = options.elements != null ? options.elements : $(this);
    return new Pagination(options);
  };

  $.fn.pagination.defaults = {
    current_page: 1,
    view_record: 10,
    total_record: 0,
    nav_count: 5
  };

  Pagination = function(options) {
    var opts;
    opts = $.extend({}, $.fn.pagination.defaults, options);
    this.current_page = opts.current_page;
    this.view_record = opts.view_record;
    this.total_record = opts.total_record;
    this.total_page = Math.ceil(this.total_record / this.view_record);
    this.nav_count = opts.nav_count;
    this.elements = opts.elements;
    this.Initialized();
    return this;
  };

  Pagination.prototype = {
    Initialized: function() {
      if (this.total_page < this.nav_count) {
        this.nav_count = this.total_page;
      }
      if (this.total_page <= 1 || this.total_page < this.current_page) {
        this.elements.empty();
        return this.elements.css('display', 'none');
      } else {
        this.MakeNavigator(this.current_page);
        return this.elements.css('display', 'block');
      }
    },
    MakeNavigator: function(current) {
      var first, i, last, nav_count_half, outstr, _i;
      this.elements.empty();
      nav_count_half = Math.floor(this.nav_count / 2);
      first = current - nav_count_half;
      last = current + nav_count_half;
      if (first <= 0) {
        first = 1;
        last = this.nav_count;
      }
      if (last > this.total_page) {
        first = this.total_page - this.nav_count + 1;
        last = this.total_page;
      }
      outstr = '<ul>';
      if (current > 2) {
        outstr += '<li class="first">';
      } else {
        outstr += '<li class="first active">';
      }
      outstr += '<a href="#" onclick="GetViewTable(1)">&laquo;</a></li>';
      if (current > 1) {
        outstr += '<li class="prev">';
      } else {
        outstr += '<li class="prev active">';
      }
      outstr += '<a href="#" onclick="GetViewTable(' + (current - 1) + ')">&lsaquo;</a></li>';
      for (i = _i = first; first <= last ? _i <= last : _i >= last; i = first <= last ? ++_i : --_i) {
        if (i === current) {
          outstr += '<li class="page active">';
        } else {
          outstr += '<li class="page">';
        }
        outstr += '<a href="#" onclick="GetViewTable(' + i + ')">' + i + '</a></li>';
      }
      if (current < this.total_page) {
        outstr += '<li class="next">';
      } else {
        outstr += '<li class="next active">';
      }
      outstr += '<a href="#" onclick="GetViewTable(' + (current + 1) + ')">&rsaquo;</a></li>';
      if (current < this.total_page - 1) {
        outstr += '<li class="last">';
      } else {
        outstr += '<li class="last active">';
      }
      outstr += '<a href="#" onclick="GetViewTable(' + this.total_page + ')">&raquo;</a></li>';
      outstr += '</ul>';
      return this.elements.append(outstr);
    }
  };

  IPCheck = function(address) {
    var ip, ip_int, ipgroup, _i, _len, _ref;
    ipgroup = address.match(/(\d+).(\d+).(\d+).(\d+)/);
    if (ipgroup != null) {
      _ref = ipgroup.slice(1, 5);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        ip = _ref[_i];
        ip_int = parseInt(ip);
        if (ip_int < 0 || 255 < ip_int) {
          return false;
        }
      }
      return true;
    }
    return null;
  };

  SearchCommonCloseBtnString = function(element) {
    return '\
            <div>\
                <button class="btn-primary"\
                               onclick="SearchCommonCloseBtnString_' + $(element).get(0).id + '_close()">閉じる</button>\
            </div>\
            <script type="text/javascript">\
                function SearchCommonCloseBtnString_' + $(element).get(0).id + '_close() {\
                        $("' + $(element).get(0).tagName + '#' + $(element).get(0).id + '").popover("hide")\
                }\
            </script>\
            ';
  };

  InputSearchIP = $('input#ip_search_box');

  GetInputIP = function() {
    return escape($.trim(InputSearchIP.prop('value')));
  };

  SearchCircle = $('#search_circle');

  IPSearch = $('a#ip_search');

  IPSearch.click(function() {
    var close_btn, search_ip;
    SearchCircle.css('display', 'inline');
    close_btn = SearchCommonCloseBtnString(this);
    IPSearch.prop('data-original-title', "検索エラー");
    IPSearch.prop('data-content', "<p>正しいIPアドレスを入力してください。</p>" + close_btn);
    search_ip = GetInputIP();
    if (!IPCheck(search_ip)) {
      SearchCircle.css('display', 'none');
      IPSearch.popover('show');
      return;
    }
    return $.ajax({
      url: '/search',
      data: {
        'search_ip': search_ip
      },
      type: 'GET',
      dataType: 'json',
      success: function(data, type) {
        var error, i, item, items, key, message, table_items, _i, _len;
        try {
          if (data.country.length > 0) {
            items = {
              '検索IP': search_ip,
              '国名コード': data.country,
              '国名': data.name
            };
            message = "<table class='table'>";
            table_items = (function() {
              var _results;
              _results = [];
              for (key in items) {
                item = items[key];
                _results.push("<tr>                                       <td>" + key + "</td>                                       <td>" + item + "</td>                                   </tr>");
              }
              return _results;
            })();
            for (_i = 0, _len = table_items.length; _i < _len; _i++) {
              i = table_items[_i];
              message += i;
            }
            message += "</table>";
            IPSearch.attr('data-original-title', "検索結果");
          } else {
            message = "<p>該当アドレス無し。</p>";
          }
        } catch (_error) {
          error = _error;
          message = error;
        }
        console.log(message);
        return IPSearch.attr('data-content', message + close_btn);
      },
      error: function() {
        return console.log('IP Search Error');
      },
      complete: function() {
        SearchCircle.css('display', 'none');
        return IPSearch.popover('show');
      }
    });
  });

  WhoisSearch = $('a#whois_search');

  WhoisSearch.click(function() {
    var close_btn, format, query, search_ip;
    SearchCircle.css('display', 'inline');
    close_btn = SearchCommonCloseBtnString(this);
    WhoisSearch.prop('data-original-title', "Whois検索エラー");
    WhoisSearch.prop('data-content', "<p>正しいIPアドレスを入力してください。</p>" + close_btn);
    search_ip = GetInputIP();
    if (!IPCheck(search_ip)) {
      SearchCircle.css('display', 'none');
      WhoisSearch.popover('show');
      return;
    }
    format = "JSON";
    query = {
      'domainName': search_ip,
      'outputFormat': format
    };
    return $.ajax({
      url: whois_url,
      data: query,
      type: 'GET',
      crossDomain: true,
      dataType: 'jsonp',
      success: function(data, type) {
        var error, i, j, message, rRawText, rawText, rawTextList, record, _i, _j, _len, _len1, _ref;
        try {
          record = data['WhoisRecord'];
          rawText = record['rawText'];
          if (rawText != null) {
            rawTextList = rawText.split('\u000a\u000a');
          } else {
            rRawText = record['registryData']['rawText'];
            if (rRawText != null) {
              rawTextList = rRawText.split('\u000a\u000a');
            } else {
              throw "レコードが存在しませんでした。";
            }
          }
          message = "";
          for (_i = 0, _len = rawTextList.length; _i < _len; _i++) {
            i = rawTextList[_i];
            message += '<div style="margin-bottom: 1em;">';
            _ref = i.split('\u000a');
            for (_j = 0, _len1 = _ref.length; _j < _len1; _j++) {
              j = _ref[_j];
              message += "<p>" + $.trim(j) + "</p>";
            }
            message += "</div>";
          }
        } catch (_error) {
          error = _error;
          message = error;
        }
        WhoisSearch.attr('data-original-title', "Whois検索結果");
        return WhoisSearch.attr('data-content', message + close_btn);
      },
      error: function() {
        return console.log('WhoisSearch Error');
      },
      complete: function() {
        SearchCircle.css('display', 'none');
        return WhoisSearch.popover('show');
      }
    });
  });

  $('#registry .save').click(function() {
    var checks, num;
    checks = (function() {
      var _i, _len, _ref, _results;
      _ref = $('#registry .rir:checked');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        num = _ref[_i];
        _results.push(num.value);
      }
      return _results;
    })();
    UpdateTable({
      'registry': checks.join(',')
    });
    return FormCCClear.click();
  });

  $('#country .save').click(function() {
    var checks, num;
    checks = (function() {
      var _i, _len, _ref, _results;
      _ref = $('#country .cc:checked');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        num = _ref[_i];
        _results.push(num.value);
      }
      return _results;
    })();
    UpdateTable({
      'country': checks.join(',')
    });
    return FormRegClear.click();
  });

  $('#registry .rir').click(function() {
    if ($('#registry_all').prop('checked')) {
      return $('#registry_all').removeProp('checked');
    }
  });

  $('#country .cc').click(function() {
    if ($('#country_all').prop('checked')) {
      return $('#country_all').removeProp('checked');
    }
  });

  CheckAllToggle = function(selector, state) {
    if (state) {
      return $(selector).prop({
        'checked': true
      });
    } else {
      return $(selector).prop({
        'checked': false
      });
    }
  };

  $('#registry .all').click(function() {
    return CheckAllToggle('#registry input', this.checked);
  });

  $('#country .all').click(function() {
    return CheckAllToggle('#country input', this.checked);
  });

  FormRegClear = $('#registry .clear').click(function() {
    return $('#registry input').prop({
      'checked': false
    });
  });

  FormCCClear = $('#country .clear').click(function() {
    return $('#country input').prop({
      'checked': false
    });
  });

  custom_area = $('#custom input');

  default_custom_text = "<CC>: <IPSTART>-<IPEND>";

  CustomTextPlus = function(value) {
    var setting_text;
    setting_text = custom_area.prop('value');
    setting_text += value;
    return custom_area.prop('value', setting_text);
  };

  $('#custom .set_registry').click(function() {
    CustomTextPlus("<REGISTRY>");
    return CTextReplace.keyup();
  });

  $('#custom .set_country').click(function() {
    CustomTextPlus("<CC>");
    return CTextReplace.keyup();
  });

  $('#custom .set_ipstart').click(function() {
    CustomTextPlus("<IPSTART>");
    return CTextReplace.keyup();
  });

  $('#custom .set_ipend').click(function() {
    CustomTextPlus("<IPEND>");
    return CTextReplace.keyup();
  });

  CReset = $('#custom .reset').click(function() {
    CClear.click();
    CustomTextPlus(default_custom_text);
    return CTextReplace.keyup();
  });

  CClear = $('#custom .clear').click(function() {
    custom_area.prop('value', '');
    return $("#custom .result").text("");
  });

  CTextReplace = custom_area.keyup(function() {
    var country_checks, list, num, output, registry_checks, replace_str, str, value;
    value = $(this).prop('value');
    str = $.trim(value);
    replace_str = str.replace(/<REGISTRY>/g, "APNIC");
    replace_str = replace_str.replace(/<CC>/g, "JP");
    replace_str = replace_str.replace(/<IPSTART>/g, "192.168.0.0");
    replace_str = replace_str.replace(/<IPEND>/g, "192.168.0.255");
    $("#custom .result").text(replace_str);
    registry_checks = (function() {
      var _i, _len, _ref, _results;
      _ref = $('#registry .rir:checked');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        num = _ref[_i];
        _results.push(num.value);
      }
      return _results;
    })();
    country_checks = (function() {
      var _i, _len, _ref, _results;
      _ref = $('#country .cc:checked');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        num = _ref[_i];
        _results.push(num.value);
      }
      return _results;
    })();
    if (registry_checks.length > 0 || country_checks.length > 0) {
      if (registry_checks.length > 0) {
        list = registry_checks.join(',');
        output = "?registry=" + list;
      } else {
        list = country_checks.join(',');
        output = "?country=" + list;
      }
      return $("#custom .result_url").text(encodeURI(location.protocol + "//" + location.host + "/jsoncustom" + output + "&settings=" + str));
    } else {
      return $("#custom .result_url").text("");
    }
  });

  $("#custom .download").click(function() {
    var country_checks, custom_text, custom_value, list, num, output, registry_checks;
    registry_checks = (function() {
      var _i, _len, _ref, _results;
      _ref = $('#registry .rir:checked');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        num = _ref[_i];
        _results.push(num.value);
      }
      return _results;
    })();
    country_checks = (function() {
      var _i, _len, _ref, _results;
      _ref = $('#country .cc:checked');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        num = _ref[_i];
        _results.push(num.value);
      }
      return _results;
    })();
    if (registry_checks.length > 0 && country_checks.length > 0) {
      return alert("レジストリ側、国名側の両方のチェックボックスに" + "チェックが入っています。\n" + "どちらか片方のチェックボックスをクリアして、" + "再度行ってください。");
    } else if (registry_checks.length === 0 && country_checks.length === 0) {
      return alert("レジストリ側、国名側の両方のチェックボックスに" + "チェックが入っていません。\n" + "どちらか片方の取得したいチェックボックスを選択して、" + "再度行ってください。");
    } else {
      custom_value = custom_area.prop('value');
      custom_text = $.trim(custom_value);
      if (registry_checks.length > 0) {
        list = registry_checks.join(',');
        output = "?registry=" + list;
      } else {
        list = country_checks.join(',');
        output = "?country=" + list;
      }
      return location.href = encodeURI("/jsoncustom" + output + "&settings=" + custom_text);
    }
  });

  $("#custom").ready(function() {
    return CReset.click();
  });

  $(".navbar [href=#custom]").click(function() {
    return CTextReplace.keyup();
  });

  CheckBrowserIE = function() {
    var msie;
    msie = navigator.appVersion.toLowerCase();
    if (msie.indexOf('msie') > -1) {
      return parseInt(msie.replace(/.*msie[ ]/, '').match(/^[0-9]+/));
    } else {
      return void 0;
    }
  };

  $(document).ready(function() {
    /* JavaScriptが有効だった場合、エラー表示を隠す*/

    var $pageUp, ie;
    $('#JavaScript_OFF').css('display', 'none');
    /* IE 8以下だった場合、警告を出す*/

    ie = CheckBrowserIE();
    if (ie < 9) {
      $('#NoBrowser').css('display', 'block');
    }
    /* IP検索ボタンのポップオーバー設定*/

    IPSearch.popover({
      trigger: 'manual',
      html: 'true',
      placement: 'bottom'
    });
    WhoisSearch.popover({
      trigger: 'manual',
      html: 'true',
      placement: 'bottom',
      template: '<div class="popover whois_popover">' + '<div class="arrow"></div>' + '<div class="popover-inner whois_popover">' + '<h3 class="popover-title"></h3>' + '<div class="popover-content"><p></p></div></div></div>'
    });
    /* 表示行数設定のドロップダウンメニューのデフォルトの値をアクティブ*/

    $('#view_row li:eq(' + GetRowPoint(view_count) + ')').addClass('active');
    /* ページアップ・ダウンボタンの表示・非表示のタイミング設定*/

    $pageUp = $("#movepage");
    $pageUp.hide();
    return $(function() {
      $(window).scroll(function() {
        var moveval;
        moveval = $(this).scrollTop();
        if (moveval > 100) {
          return $pageUp.fadeIn();
        } else {
          return $pageUp.fadeOut();
        }
      });
      return $pageUp.click(function() {
        $('body, html').animate({
          scrollTop: 0
        }, 600);
        return false;
      });
    });
  });

}).call(this);
