# 1ページに表示する数
view_count = 100

# -------------------------------------------------------------
root = exports ? this

jsondata = []

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
        ShowTable(0, view_count)

        # pagination設定
        central = true
        count = Math.ceil json.length / view_count
        str = '<li><a href="#">&lt;&lt;</a></li>'
        for i in [1..count]
            if i > 2 && i + 1 < count
                if central
                    str += '<li class="disabled"><a href="#">...</a></li>'
                    central = false
            else
                str += '<li><a href="#" onclick="GetViewTable(' + i + ')">' + i + '</a></li>'
        str += '<li><a href="#">&gt;&gt;</a></li>'

        $("#view_pages ul").html str

        # 最初のページ要素をアクティブに
        $('#view_pages li:lt(2)').attr 'class', 'active'

# viewbarの更新
# グローバル変数 jsondataにjsonのデータが入っている必要がある
# first : 開始位置の数値
# last : 終了位置の数値
# 範囲 : first < last
ShowTable = (first, last) ->
        str = ""
        j = 0
        for i in [first..last]
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
