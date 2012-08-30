# -------------------------------------------------------------
# 自由に設定
# -------------------------------------------------------------

# 1ページに表示する数
view_count = 150

# ページネーションに表示するページ数
pagination_count = 5

# -------------------------------------------------------------
# スクリプト内で使用する直接設定しない変数など
# -------------------------------------------------------------

root = exports ? this

# -------------------------------------------------------------
# Save Changesボタンが押されたら、Loadingと表示させるのに使う
# -------------------------------------------------------------

$.fn.state = (state) ->
    d = 'disabled'
    return @.each ->
        $this = $(@)
        $this.html( $this.data()[state] )
        if state == "loading"
            $this.addClass(d).attr(d, d)
        else
            $this.removeClass(d).removeAttr(d)

# -------------------------------------------------------------
# IP一覧の更新処理
# -------------------------------------------------------------
pager = NaN
jsondata = []

$.fn.UpdateTable = (data) ->
    # 読み込みアニメーションなどの表示
    $("#load_circle").css('display', 'inline')
    $this = $(@)
    $this.state('loading')

    $.getJSON '/json', data, (json) ->
        # 他の関数でも使えるように代入
        jsondata = json

        # viewbarに設定
        ShowTable 0, view_count

        # paginationの設定
        params =
            view_record: view_count
            total_record: json.length
            nav_count: pagination_count
        pager = $("#view_pages").pagination(params)

        # 読み込みアニメーションなど終了
        $this.state('complete')
        $("#load_circle").css('display', 'none')

# 入力された値のぺージに更新
# point : ページ数
root.GetViewTable = (point) ->
    ShowTable((point - 1) * view_count, point * view_count)
    pager.MakeNavigator(point)

# viewbarの更新
# グローバル変数 jsondataにjsonのデータが入っている必要がある
# first : 開始位置の数値
# last : 終了位置の数値
# 範囲 : first < last
ShowTable = (first, last) ->
        str = ""
        j = 0
        for i in [first...last]
            if jsondata[i]?
                str += "<tr>"
                str += "<td>" + escape(jsondata[i].registry) + "</td>"
                str += "<td>" + escape(jsondata[i].country) + "</td>"
                str += "<td>" + escape(jsondata[i].StartIP)  + "</td>"
                str += "<td>" + escape(jsondata[i].EndIP)  + "</td>"
                str += "</tr>"

        $("#viewbar tbody").html(str)

# 指定された行数に変更
root.ChangeRow = (num) ->
    view_count = num
    $('#view_row .active').removeClass('active')
    $('#view_row li:eq(' + GetRowPoint(num) + ')').addClass('active')
    if pager
        # viewbarの更新
        ShowTable 0, view_count

        # ページネーションの更新
        params =
            view_record: view_count
            total_record: pager.total_record
            nav_count: pagination_count
        pager = $("#view_pages").pagination(params)

GetRowPoint = (num) ->
    return (num / 50) - 1

# -------------------------------------------------------------
# ページネーション
# -------------------------------------------------------------

$.fn.pagination = (options) ->
    options.elements = if options.elements? then options.elements else $(@)
    new Pagination(options)

$.fn.pagination.defaults =
    current_page: 1
    view_record: 10
    total_record: 0
    nav_count: 5
        
Pagination = (options) ->
    opts = $.extend({}, $.fn.pagination.defaults, options)

    @current_page = opts.current_page                     # 現在のページ
    @view_record = opts.view_record                       # 1ページに表示するレコード数
    @total_record = opts.total_record                     # 全てのレコード数
    @total_page = Math.ceil(@total_record / @view_record) # 総ページ数
    @nav_count = opts.nav_count                           # 表示するナビゲーション数
    @elements = opts.elements # 適用する要素

    @Initialized()
    return @

Pagination.prototype = {
    Initialized: ->
        # 全てのページ数が表示するナビゲーション数より小さい場合、
        # 総ページを表示するナビゲーション数にする
        if @total_page < @nav_count
            @nav_count = @total_page
        
        # トータルページ数が2以下または現在のページが総ページ数より大きい場合表示しない
        if @total_page <= 1 || @total_page < @current_page
            # 前回の結果が残っている場合があるため、表示されている要素をクリア
            @elements.empty()
            @elements.css('display', 'none')
        else
            @MakeNavigator(@current_page)
            @elements.css('display', 'block')

    MakeNavigator: (current) ->
        # 現在、表示している要素を削除
        @elements.empty()

        # 現在のページがナビゲーションの中央にくるようにする
        nav_count_half = Math.floor(@nav_count / 2)
        first = current - nav_count_half
        last = current + nav_count_half
        if first <= 0
            first = 1
            last = @nav_count
        if last > @total_page
            first = @total_page - @nav_count + 1
            last = @total_page

        outstr = '<ul>'

        # 「最初へ」ボタン追加(2ページ以降で有効)
        if current > 2
            outstr += '<li class="first">'
        else
            outstr += '<li class="first active">'
        outstr += '<a href="#" onclick="GetViewTable(1)">&laquo;</a></li>'

        # 「前へ」ボタン追加(最初のページ以降で有効)
        if current > 1
            outstr += '<li class="prev">'
        else
            outstr += '<li class="prev active">'
        outstr += '<a href="#" onclick="GetViewTable(' + (current - 1) + ')">&lsaquo;</a></li>'

        for i in [first..last]
            if i == current
                outstr += '<li class="page active">'
            else
                outstr += '<li class="page">'
            outstr += '<a href="#" onclick="GetViewTable(' + i + ')">' + i + '</a></li>'
        
        # 「次へ」ボタン追加(最後のページ以前で有効)
        if current < @total_page
            outstr += '<li class="next">'
        else
            outstr += '<li class="next active">'
        outstr += '<a href="#" onclick="GetViewTable(' + (current + 1) + ')">&rsaquo;</a></li>'

        # 「最後へ」ボタン追加(最後のページの前ページ以前で有効)
        if current < @total_page - 1
            outstr += '<li class="last">'
        else
            outstr += '<li class="last active">'
        outstr += '<a href="#" onclick="GetViewTable(' + @total_page + ')">&raquo;</a></li>'

        outstr += '</ul>'
        @elements.append(outstr)
    }

# -------------------------------------------------------------
# フォームボタンなど
# -------------------------------------------------------------

# レジストリのチェックボックスの結果を有効
$('#registry .save').click ->
    checks = (num.value for num in $('#registry .rir:checked'))

    $(@).UpdateTable {'registry': checks.join(',')}

    FormCCClear.click()

# 国名のチェックボックスの結果を有効
$('#country .save').click ->
    checks = (num.value for num in $('#country .cc:checked'))

    $(@).UpdateTable {'country': checks.join(',')}

    FormRegClear.click()

# -------------------------------------------------------------

# レジストリのチェックボックスを外した場合、ALLにチェックがあったらはずす
$('#registry .rir').click ->
    if $('#registry_all').attr 'checked'
        $('#registry_all').removeAttr 'checked'

# 国名のチェックボックスを外した場合、ALLにチェックがあったらはずす
$('#country .cc').click ->
    if $('#country_all').attr 'checked'
        $('#country_all').removeAttr 'checked'

# -------------------------------------------------------------

# レジストリを全てチェック
$('#registry .all').click ->
    if @.checked
        $('#registry input').attr 'checked', 'checked'
    else
        $('#registry input').removeAttr 'checked'

# 国名を全てチェック
$('#country .all').click ->
    if @.checked
        $('#country input').attr 'checked', 'checked'
    else
        $('#country input').removeAttr 'checked'

# -------------------------------------------------------------

# レジストリのチェックを全てクリア
FormRegClear = $('#registry .clear').click ->
    $('#registry input').removeAttr 'checked'

# 国名のチェックを全てクリア
FormCCClear = $('#country .clear').click ->
    $('#country input').removeAttr 'checked'

# -------------------------------------------------------------
# モーダルウィンドウ(カスタマイズ)
# -------------------------------------------------------------
custom_area = $('#custom input')
default_custom_text = "<CC>: <IPSTART>-<IPEND>"

CustomTextPlus = (value) ->
    setting_text = custom_area.attr('value')
    setting_text += value
    custom_area.attr('value', setting_text)

$('#custom .set_registry').click ->
    CustomTextPlus("<REGISTRY>")
    CTextReplace.keyup()

$('#custom .set_country').click ->
    CustomTextPlus("<CC>")
    CTextReplace.keyup()

$('#custom .set_ipstart').click ->
    CustomTextPlus("<IPSTART>")
    CTextReplace.keyup()

$('#custom .set_ipend').click ->
    CustomTextPlus("<IPEND>")
    CTextReplace.keyup()

CReset = $('#custom .reset').click ->
    CClear.click()

    CustomTextPlus(default_custom_text)
    CTextReplace.keyup()

CClear = $('#custom .clear').click ->
    custom_area.attr('value', '')
    $("#custom .result").text("")

CTextReplace = custom_area.keyup ->
    value = $(@).attr('value')
    str = $.trim(value)

    ## 出力例 ##
    # 指定文字列の置き換え
    replace_str = str.replace(/<REGISTRY>/g, "APNIC")
    replace_str = replace_str.replace(/<CC>/g, "JP")
    replace_str = replace_str.replace(/<IPSTART>/g, "192.168.0.0")
    replace_str = replace_str.replace(/<IPEND>/g, "192.168.0.255")

    $("#custom .result").text(replace_str)

    ## 直接ダウンロードURL ##
    registry_checks = (num.value for num in $('#registry .rir:checked'))
    country_checks = (num.value for num in $('#country .cc:checked'))

    if registry_checks.length > 0 or country_checks.length > 0
        if registry_checks.length > 0
            list = registry_checks.join(',')
            output = "?registry=" + list
        else
            list = country_checks.join(',')
            output = "?country=" + list

        $("#custom .result_url").text(
            encodeURI(location.protocol + "//" + location.host \
                      + "/jsoncustom" + output + "&settings=" + str))
    else
        $("#custom .result_url").text("")

$("#custom .download").click ->
    registry_checks = (num.value for num in $('#registry .rir:checked'))
    country_checks = (num.value for num in $('#country .cc:checked'))
    if registry_checks.length > 0 and country_checks.length > 0
        alert "レジストリ側、国名側の両方のチェックボックスに" \
              + "チェックが入っています。\n" \
              + "どちらか片方のチェックボックスをクリアして、" \
              + "再度行ってください。"
    else if registry_checks.length == 0 and country_checks.length == 0
        alert "レジストリ側、国名側の両方のチェックボックスに" \
              + "チェックが入っていません。\n" \
              + "どちらか片方の取得したいチェックボックスを選択して、" \
              + "再度行ってください。"
    else
        custom_value = custom_area.attr('value')
        custom_text = $.trim(custom_value)

        if registry_checks.length > 0
            list = registry_checks.join(',')
            output = "?registry=" + list
        else
            list = country_checks.join(',')
            output = "?country=" + list
        location.href = encodeURI(
            "/jsoncustom" + output + "&settings=" + custom_text)

$("#custom").ready ->
    CReset.click()

$(".navbar [href=#custom]").click ->
    CTextReplace.keyup()

# -------------------------------------------------------------
# ブラウザ判定
# -------------------------------------------------------------
CheckBrowserIE = ->
    msie = navigator.appVersion.toLowerCase()
    return if msie.indexOf('msie') > -1 \
           then parseInt(msie.replace(/.*msie[ ]/,'').match(/^[0-9]+/)) \
           else undefined

# -------------------------------------------------------------
# ページ表示時に実行
# -------------------------------------------------------------
$(document).ready ->
    ### JavaScriptが有効だった場合、エラー表示を隠す ###
    $('#JavaScript_OFF').css('display', 'none')

    ### IE 8以下だった場合、警告を出す ###
    ie = CheckBrowserIE()
    if ie < 9
        $('#NoBrowser').css('display', 'block')

    ### 表示行数設定のドロップダウンメニューのデフォルトの値をアクティブ ###
    $('#view_row li:eq(' + GetRowPoint(view_count) + ')').addClass('active')

    ### ページアップ・ダウンボタンの表示・非表示のタイミング設定 ###
    $pageUp = $("#movepage")
    $pageUp.hide()

    $(->
        $(window).scroll(->
            moveval = $(@).scrollTop()
            if moveval > 100
                $pageUp.fadeIn()
            else
                $pageUp.fadeOut()
        )

        $pageUp.click(->
            $('body, html').animate({ scrollTop: 0 }, 600)
            return false
        )
    )
