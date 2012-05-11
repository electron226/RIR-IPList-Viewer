# レジストリのチェックボックスの結果を有効
$('#registry_save').click ->
    checks = (num.value for num in $('#registry .reg:checked'))

    UpdateTable {'registry': checks.join(',')}

    $('.cc_clear').click()

# 国名のチェックボックスの結果を有効
$('#country_save').click ->
    checks = (num.value for num in $('#country .cc:checked'))

    UpdateTable {'country': checks.join(',')}

    $('.reg_clear').click()

# 更新処理
UpdateTable = (data) ->
    $.getJSON '/json', data, (json) ->
        # viewbarに設定
        str = ""
        for i in json
            str += "<tr>"
            str += "<td>" + escape(i.registry) + "</td>"
            str += "<td>" + escape(i.country) + "</td>"
            str += "<td>" + escape(i.StartIP)  + "</td>"
            str += "<td>" + escape(i.EndIP)  + "</td>"
            str += "</tr>"

        $("#viewbar tbody").html str

        # pagination設定
        count = Math.ceil json.length / 100.0
        str = ""
        for i in [1..count]
            str += '<li><a href="#">' + i + '</a></li>'

        $("#view_pages ul").html str

        # 最初のページ要素をアクティブに
        $('#view_pages li:first').attr 'class', 'active'

$('#country .cc').click ->
    if $('.cc_all').attr 'checked'
        $('.cc_all').removeAttr 'checked'

$('.reg_all').click ->
    if @.checked
        $('#registry input').attr 'checked', 'checked'
    else
        $('#registry input').removeAttr 'checked'

$('.cc_all').click ->
    if @.checked
        $('#country input').attr 'checked', 'checked'
    else
        $('#country input').removeAttr 'checked'

$('.reg_clear').click ->
    $('#registry input').removeAttr 'checked'

$('.cc_clear').click ->
    $('#country input').removeAttr 'checked'
