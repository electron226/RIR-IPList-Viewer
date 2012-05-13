// Generated by CoffeeScript 1.3.1
(function() {
  ﻿;

  var Pagination, ShowTable, UpdateTable, jsondata, pager, pagination_count, pagination_length, root, view_count;

  view_count = 100;

  pagination_count = 5;

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  jsondata = [];

  pagination_length = 0;

  pager = NaN;

  UpdateTable = function(data) {
    return $.getJSON('/json', data, function(json) {
      var params;
      jsondata = json;
      ShowTable(0, view_count);
      params = {
        view_record: view_count,
        total_record: json.length,
        nav_count: pagination_count
      };
      return pager = $("#view_pages").pagination(params);
    });
  };

  root.GetViewTable = function(point) {
    ShowTable((point - 1) * view_count, point * view_count);
    return pager.makeNavigator(point);
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
    this.initialized();
    return this;
  };

  Pagination.prototype = {
    initialized: function() {
      if (this.total_page < this.nav_count) {
        this.nav_count = this.total_page;
      }
      if (this.total_page <= 1 || this.total_page < this.current_page) {
        return;
      }
      return this.makeNavigator(this.current_page);
    },
    makeNavigator: function(current) {
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

  $('#registry_save').click(function() {
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
    return $('#country_clear').click();
  });

  $('#country_save').click(function() {
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
    return $('#registry_clear').click();
  });

  $('#registry .rir').click(function() {
    if ($('#registry_all').attr('checked')) {
      return $('#registry_all').removeAttr('checked');
    }
  });

  $('#country .cc').click(function() {
    if ($('#country_all').attr('checked')) {
      return $('#country_all').removeAttr('checked');
    }
  });

  $('#registry_all').click(function() {
    if (this.checked) {
      return $('#registry input').attr('checked', 'checked');
    } else {
      return $('#registry input').removeAttr('checked');
    }
  });

  $('#country_all').click(function() {
    if (this.checked) {
      return $('#country input').attr('checked', 'checked');
    } else {
      return $('#country input').removeAttr('checked');
    }
  });

  $('#registry_clear').click(function() {
    return $('#registry input').removeAttr('checked');
  });

  $('#country_clear').click(function() {
    return $('#country input').removeAttr('checked');
  });

}).call(this);
