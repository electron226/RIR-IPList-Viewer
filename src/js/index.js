// Generated by CoffeeScript 1.3.1
(function() {
  ﻿;

  var ShowTable, UpdatePagination, UpdateTable, jsondata, pagination_length, pagination_side, root, view_count;

  view_count = 100;

  pagination_side = 6;

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  jsondata = [];

  pagination_length = 0;

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

  UpdateTable = function(data) {
    return $.getJSON('/json', data, function(json) {
      jsondata = json;
      ShowTable(0, view_count);
      pagination_length = Math.ceil(json.length / view_count);
      return UpdatePagination(1);
    });
  };

  UpdatePagination = function(point) {
    var GetFirstPosition, GetLastPosition, c_val, edge, first, i, last, str, _i;
    GetFirstPosition = function(pos, side, length) {
      if (length == null) {
        length = 1;
      }
      if (pos - side > length) {
        return pos - side;
      }
      return length;
    };
    GetLastPosition = function(pos, side, length) {
      if (length == null) {
        length = pagination_length;
      }
      if (pos + side < length) {
        return pos + side;
      }
      return length;
    };
    if (point <= 1) {
      first = 1;
      last = GetLastPosition(point, pagination_side);
      edge = 'first';
    } else if (point >= pagination_length) {
      first = GetFirstPosition(point, pagination_side);
      last = pagination_length;
      edge = 'last';
    } else {
      c_val = pagination_side / 2;
      first = GetFirstPosition(point, c_val);
      last = GetLastPosition(point, c_val);
    }
    str = '<li><a href="#" onclick="GetViewTable(1)">&#171;</a></li>';
    for (i = _i = first; first <= last ? _i <= last : _i >= last; i = first <= last ? ++_i : --_i) {
      str += '<li><a href="#" onclick="GetViewTable(' + i + ')">' + i + '</a></li>';
    }
    str += '<li><a href="#" onclick="GetViewTable(' + pagination_length + ')">&#187;</a></li>';
    $("#view_pages ul").html(str);
    $("#view_pages li").removeClass('disabled');
    $("#view_pages li").addClass('enabled');
    $("#view_pages li:contains(" + point + ")").addClass('disabled');
    if (edge === 'first') {
      return $("#view_pages li:first").addClass('disabled');
    } else if (edge === 'last') {
      return $("#view_pages li:last").addClass('disabled');
    }
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

  root.GetViewTable = function(point) {
    ShowTable((point - 1) * view_count, point * view_count);
    return UpdatePagination(point);
  };

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
