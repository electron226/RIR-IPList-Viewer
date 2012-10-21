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

# Whoisの入手先
whois_url = "http://www.whoisxmlapi.com/whoisserver/WhoisService"

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
pager = null
jsondata = []

LoadCircle = $('#load_circle')

UpdateTable = (data) ->
    # 読み込みアニメーションなどの表示
    LoadCircle.css('display', 'inline')
    $this = $(@)
    $this.state('loading')

    $.ajax(
        url: '/json',
        data: data,
        type: 'GET',
        dataType: 'json',
        success: (json, type) ->
            try
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
            catch error
                console.log(error)
                alert(error)
        error: ->
            console.log('IP Search Error')
        complete: ->
            # 読み込みアニメーションなど終了
            $this.state('complete')
            LoadCircle.css('display', 'none')
    )

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
    view_count = num # 現在の値を変更

    $('#view_row .active').removeClass('active')
    $('#view_row li:eq(' + GetRowPoint(num) + ')').addClass('active')
    if pager?
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

# 項目のソート
before_selected = null
$('button.sort_item').click ->
    $this = $(@)
    name = @.name
    if before_selected != name
        # 前回ソートしたものと別の場合の初期値
        $this.attr('value', 'asc')

    state = $this.attr('value')
    try
        if state == 'asc'
            switch name
                when 'sort_registry'
                    jsondata.sort( (x, y) ->
                        if x.registry < y.registry
                            return -1
                        else
                            return 1
                    )
                when 'sort_country'
                    jsondata.sort( (x, y) ->
                        if x.country < y.country
                            return -1
                        else
                            return 1
                    )
                when 'sort_ip_start'
                    jsondata.sort( (x, y) ->
                        if x.start < y.start
                            return -1
                        else
                            return 1
                    )
                when 'sort_ip_end'
                    jsondata.sort( (x, y) ->
                        if x.end < y.end
                            return -1
                        else
                            return 1
                    )
                else
                    throw "sort asc error."
            $this.attr('value', 'desc')
        else
            switch name
                when 'sort_registry'
                    jsondata.sort( (x, y) ->
                        if x.registry < y.registry
                            return 1
                        else
                            return -1
                    )
                when 'sort_country'
                    jsondata.sort( (x, y) ->
                        if x.country < y.country
                            return 1
                        else
                            return -1
                    )
                when 'sort_ip_start'
                    jsondata.sort( (x, y) ->
                        if x.start < y.start
                            return 1
                        else
                            return -1
                    )
                when 'sort_ip_end'
                    jsondata.sort( (x, y) ->
                        if x.end < y.end
                            return 1
                        else
                            return -1
                    )
                else
                    throw "sort desc error."
            $this.attr('value', 'asc')

        root.ChangeRow(view_count)
        before_selected = name
    catch error
        console.log(error)

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

    @current_page = opts.current_page   # 現在のページ
    @view_record = opts.view_record     # 1ページに表示するレコード数
    @total_record = opts.total_record   # 全てのレコード数
    @total_page = Math.ceil(@total_record / @view_record) # 総ページ数
    @nav_count = opts.nav_count         # 表示するナビゲーション数
    @elements = opts.elements # 適用する要素

    @Initialized()
    return @

Pagination.prototype = {
    Initialized: ->
        # 全てのページ数が表示するナビゲーション数より小さい場合、
        # 総ページを表示するナビゲーション数にする
        if @total_page < @nav_count
            @nav_count = @total_page
        
        # トータルページ数が2以下または現在のページが
        # 総ページ数より大きい場合表示しない
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
        outstr += '<a href="#" onclick="GetViewTable(' \
                        + (current - 1) + ')">&lsaquo;</a></li>'

        for i in [first..last]
            if i == current
                outstr += '<li class="page active">'
            else
                outstr += '<li class="page">'
            outstr += '<a href="#" onclick="GetViewTable(' \
                            + i + ')">' + i + '</a></li>'
        
        # 「次へ」ボタン追加(最後のページ以前で有効)
        if current < @total_page
            outstr += '<li class="next">'
        else
            outstr += '<li class="next active">'
        outstr += '<a href="#" onclick="GetViewTable(' \
                        + (current + 1) + ')">&rsaquo;</a></li>'

        # 「最後へ」ボタン追加(最後のページの前ページ以前で有効)
        if current < @total_page - 1
            outstr += '<li class="last">'
        else
            outstr += '<li class="last active">'
        outstr += '<a href="#" onclick="GetViewTable(' \
                        + @total_page + ')">&raquo;</a></li>'

        outstr += '</ul>'
        @elements.append(outstr)
    }

# -------------------------------------------------------------
# フォームボタンなど
# -------------------------------------------------------------

# 文字列がIPアドレスで正しい数値かチェック
# address : IPアドレスの文字列
# 戻り値: 正常終了ならtrue, 不正な値ならfalse、IPアドレスではないならnull
IPCheck = (address) ->
    ipgroup = address.match(/(\d+).(\d+).(\d+).(\d+)/)
    if ipgroup?
        for ip in ipgroup[1..4]
            ip_int = parseInt(ip)
            if ip_int < 0 || 255 < ip_int
                return false
        return true
    return null

# ポップオーバーの内容用に表示する閉じるボタンをHTML文字列で返す
# element : 作成する要素のDOM要素自身(thisを受け取る)
# 戻り値: HTML文字列
SearchCommonCloseBtnString = (element) ->
    return '
            <div>
                <button class="btn-primary"
                               onclick="SearchCommonCloseBtnString_' \
                           + $(element).get(0).id + '_close()">閉じる</button>
            </div>
            <script type="text/javascript">
                function SearchCommonCloseBtnString_' \
                    + $(element).get(0).id + '_close() {
                        $("' + $(element).get(0).tagName \
                        + '#' + $(element).get(0).id + '").popover("hide")
                }
            </script>
            '

# IPアドレス入力欄の要素を加工して返す
InputSearchIP = $('input#ip_search_box')
GetInputIP = ->
    return escape($.trim(InputSearchIP.attr('value')))

# 検索読み込みサークル
SearchCircle = $('#search_circle')

# IPアドレスの検索ボタン
IPSearch = $('a#ip_search')
IPSearch.click ->
    # 読み込みサークル表示
    SearchCircle.css('display', 'inline')

    # 検索結果の閉じるボタン
    close_btn = SearchCommonCloseBtnString(@)

    # デフォルトの表示メッセージ
    IPSearch.attr('data-original-title', "検索エラー")
    IPSearch.attr(
        'data-content',
        "<p>正しいIPアドレスを入力してください。</p>" + close_btn)

    # アドレスの取得と確認
    search_ip = GetInputIP()
    if not IPCheck(search_ip)
        # マッチしないならそのまま終了
        SearchCircle.css('display', 'none')
        IPSearch.popover('show')
        return

    # JSONデータの取得
    $.ajax(
        url: '/search',
        data: { 'search_ip': search_ip },
        type: 'GET',
        dataType: 'json',
        success: (data, type) ->
            try
                if data.country.length > 0
                    # データがある場合
                    items =
                        '検索IP': search_ip
                        '国名コード': data.country
                        '国名': data.name

                    message = "<table class='table'>"
                    table_items = for key, item of items
                                   "<tr>
                                       <td>#{key}</td>
                                       <td>#{item}</td>
                                   </tr>"
                    message += i for i in table_items
                    message += "</table>"
                    IPSearch.attr('data-original-title', "検索結果")
                else
                    # 該当データがない
                    message = "<p>該当アドレス無し。</p>"
            catch error
                message = error

            IPSearch.attr('data-content', message + close_btn)
        error: ->
            console.log('IP Search Error')
        complete: ->
            # 読み込みサークルの非表示と結果の表示
            SearchCircle.css('display', 'none')
            IPSearch.popover('show')
    )

# Whois
WhoisSearch = $('a#whois_search')
WhoisSearch.click ->
    # 読み込みサークル表示
    SearchCircle.css('display', 'inline')

    # 検索結果の閉じるボタン
    close_btn = SearchCommonCloseBtnString(@)

    # デフォルトのメッセージ
    WhoisSearch.attr('data-original-title', "Whois検索エラー")
    WhoisSearch.attr(
        'data-content',
        "<p>正しいIPアドレスを入力してください。</p>" + close_btn)

    # アドレスの取得と確認
    search_ip = GetInputIP()
    if not IPCheck(search_ip)
        # マッチしないならそのまま終了
        SearchCircle.css('display', 'none')
        WhoisSearch.popover('show')
        return

    # Whois取得
    format = "JSON"
    query =
        'domainName': search_ip
        'outputFormat': format
    $.ajax(
        url: whois_url,
        data: query,
        type: 'GET',
        crossDomain: true,
        dataType: 'jsonp',
        success: (data, type) ->
            try
                # データの取得・加工
                record = data['WhoisRecord']
                rawText = record['rawText']
                if rawText?
                    # 個別のものを取得
                    rawTextList = rawText.split('\u000a\u000a')
                else
                    # 個別のものがなければレジストリから取得する
                    rRawText = record['registryData']['rawText']
                    if rRawText?
                        rawTextList = rRawText.split('\u000a\u000a')
                    else
                        # レジストリ側も存在しない場合
                        throw "レコードが存在しませんでした。"

                # 表示形式設定
                message = ""
                for i in rawTextList
                    message += '<div style="margin-bottom: 1em;">'
                    for j in i.split('\u000a')
                        message += "<p>" + $.trim(j) + "</p>"
                    message += "</div>"
            catch error
                message = error

            # 出力
            WhoisSearch.attr('data-original-title', "Whois検索結果")
            WhoisSearch.attr('data-content', message + close_btn)
        error: ->
            console.log('WhoisSearch Error')
        complete: ->
            # 読み込みサークルの非表示と結果の表示
            SearchCircle.css('display', 'none')
            WhoisSearch.popover('show')
    )

# -------------------------------------------------------------

# レジストリのチェックボックスの結果を有効化
$('#registry .save').click ->
    checks = (num.value for num in $('#registry .rir:checked'))

    UpdateTable {'registry': checks.join(',')}

    FormCCClear.click()

# 国名のチェックボックスの結果を有効化
$('#country .save').click ->
    checks = (num.value for num in $('#country .cc:checked'))

    UpdateTable {'country': checks.join(',')}

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

    ### IP検索ボタンのポップオーバー設定 ###
    IPSearch.popover({
        trigger: 'manual',
        html: 'true',
        placement: 'bottom',
    })
    WhoisSearch.popover({
        trigger: 'manual',
        html: 'true',
        placement: 'bottom',
        template: '<div class="popover whois_popover">' \
                    + '<div class="arrow"></div>' \
                    + '<div class="popover-inner whois_popover">' \
                    + '<h3 class="popover-title"></h3>' \
                    + '<div class="popover-content"><p></p></div></div></div>'
    })

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
