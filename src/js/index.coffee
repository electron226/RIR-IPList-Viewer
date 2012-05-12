# 1ページに表示する数
view_count = 100

# UpdatePaginationで指定したページの中心から左右にいくつまでページを表示するか
# 偶数で指定
pagination_side = 6

# -------------------------------------------------------------
root = exports ? this

jsondata = []

pagination_length = 0

# レジストリのチェックボックスの結果を有効
$('#registry_save').click ->
    checks = (num.value for num in $('#registry .rir:checked'))

    UpdateTable {'registry': checks.join(',')}

    $('#country_clear').click()

# 国名のチェックボックスの結果を有効
$('#country_save').click ->
    checks = (num.value for num in $('#country .cc:checked'))

    UpdateTable {'country': checks.join(',')}

    $('#registry_clear').click()

# 更新処理
UpdateTable = (data) ->
    $.getJSON '/json', data, (json) ->
        # 他の関数でも使えるように代入
        jsondata = json

        # viewbarに設定
        ShowTable 0, view_count

        # paginationの設定
        pagination_length = Math.ceil json.length / view_count
        UpdatePagination 1 # 最初のページを選択

        # 最初のページ要素をアクティブに
        #$('#view_pages li:lt(2)').attr 'class', 'active'

# 指定したページを中心にページネーション表示
UpdatePagination = (point) ->
    GetFirstPosition = (pos, side, length = 1) ->
        if pos - side > length
            return pos - side
        return length
    GetLastPosition = (pos, side, length = pagination_length) ->
        if pos + side < length
            return pos + side
        return length

    # 指定したページ別の表示範囲設定
    if point <= 1
        first = 1
        last = GetLastPosition point, pagination_side

        edge = 'first'
    else if point >= pagination_length
        first = GetFirstPosition point, pagination_side
        last = pagination_length

        edge = 'last'
    else
        c_val = pagination_side / 2
        first = GetFirstPosition point, c_val
        last = GetLastPosition point, c_val

    # ページ一覧
    str = '<li><a href="#" onclick="GetViewTable(1)">&#171;</a></li>'
    for i in [first..last]
        str += '<li><a href="#" onclick="GetViewTable(' + i + ')">' + i + '</a></li>'
    str += '<li><a href="#" onclick="GetViewTable(' + pagination_length + ')">&#187;</a></li>'

    # 更新
    $("#view_pages ul").html str

    # 全てのボタンの有効無効リセット
    $("#view_pages li").removeClass('disabled')
    $("#view_pages li").addClass('enabled')

    # 指定されたページのボタンを無効
    $("#view_pages li:contains(" + point + ")").addClass('disabled')

    # 指定したページ別に左端、右端のボタンの有効無効判定
    if edge == 'first'
        $("#view_pages li:first").addClass('disabled')
    else if edge == 'last'
        $("#view_pages li:last").addClass('disabled')

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

        $("#viewbar tbody").html str

# 入力された値のぺージに更新
# point : ページ数
root.GetViewTable = (point) ->
    ShowTable (point - 1) * view_count, point * view_count
    UpdatePagination point

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

# レジストリのチェックを全てクリア
$('#registry_clear').click ->
    $('#registry input').removeAttr 'checked'

# 国名のチェックを全てクリア
$('#country_clear').click ->
    $('#country input').removeAttr 'checked'
