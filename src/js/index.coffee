# 1ページに表示する数
view_count = 100

# ページネーションに表示するページ数
pagination_count = 5

# -------------------------------------------------------------

root = exports ? this

jsondata = []
pagination_length = 0
pager = NaN

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

# 更新処理
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
        else
            @MakeNavigator(@current_page)

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

# レジストリのチェックボックスの結果を有効
$('#registry_save').click ->
    checks = (num.value for num in $('#registry .rir:checked'))

    $(@).UpdateTable {'registry': checks.join(',')}

    $('#country_clear').click()

# 国名のチェックボックスの結果を有効
$('#country_save').click ->
    checks = (num.value for num in $('#country .cc:checked'))

    $(@).UpdateTable {'country': checks.join(',')}

    $('#registry_clear').click()

# -------------------------------------------------------------

# レジストリのチェックボックスを外した場合、
# ALLにチェックがあったらはずす
$('#registry .rir').click ->
    if $('#registry_all').attr 'checked'
        $('#registry_all').removeAttr 'checked'

# 国名のチェックボックスを外した場合、
# ALLにチェックがあったらはずす
$('#country .cc').click ->
    if $('#country_all').attr 'checked'
        $('#country_all').removeAttr 'checked'

# -------------------------------------------------------------

# レジストリを全てチェック
$('#registry_all').click ->
    if @.checked
        $('#registry input').attr 'checked', 'checked'
    else
        $('#registry input').removeAttr 'checked'

# 国名を全てチェック
$('#country_all').click ->
    if @.checked
        $('#country input').attr 'checked', 'checked'
    else
        $('#country input').removeAttr 'checked'

# -------------------------------------------------------------

# レジストリのチェックを全てクリア
$('#registry_clear').click ->
    $('#registry input').removeAttr 'checked'

# 国名のチェックを全てクリア
$('#country_clear').click ->
    $('#country input').removeAttr 'checked'
