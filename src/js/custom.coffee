$ ->
    custom_area = $('#custom input[name="custom_string"]')
    default_custom_text = "<CC>: <IPSTART>-<IPEND>"

    CustomTextPlus = (value) ->
        setting_text = custom_area.val()
        setting_text += value
        custom_area.val(setting_text)

    $('#custom .registry').click ->
        CustomTextPlus("<REGISTRY>")
        CTextReplace.keyup()

    $('#custom .button .country').click ->
        CustomTextPlus("<CC>")
        CTextReplace.keyup()

    $('#custom .button .ipstart').click ->
        CustomTextPlus("<IPSTART>")
        CTextReplace.keyup()

    $('#custom .button .ipend').click ->
        CustomTextPlus("<IPEND>")
        CTextReplace.keyup()

    CReset = $('#custom .reset').click ->
        custom_area.val(default_custom_text)
        CTextReplace.keyup()

    CClear = $('#custom .button .clear').click ->
        custom_area.val('')
        $("#custom .result").text("")

    DownloadShow = ->
        value = custom_area.val()
        str = $.trim(value)

        ## 直接ダウンロードURL ##
        registry_checks = (num.value for num in $('#registry .element .rir:checked'))
        country_checks = (num.value for num in $('#country .element .cc:checked'))

        if registry_checks.length > 0 or country_checks.length > 0
            if registry_checks.length > 0
                list = registry_checks.join(',')
                output = "?registry=" + list
            else
                list = country_checks.join(',')
                output = "?country=" + list

            download_url =
                encodeURI(location.protocol + "//" + location.host \
                + "/jsoncustom" + output + "&settings=" + str)
            $("#custom .result_url").html('<a href="' + download_url + '">' + download_url + '</a>')
        else
            $("#custom .result_url").text("取得したい対象が未指定")

    CTextReplace = custom_area.keyup ->
        value = custom_area.val()
        str = $.trim(value)

        ## 出力例 ##
        # 指定文字列の置き換え
        replace_str = str.replace(/<REGISTRY>/g, "APNIC")
        replace_str = replace_str.replace(/<CC>/g, "JP")
        replace_str = replace_str.replace(/<IPSTART>/g, "192.168.0.0")
        replace_str = replace_str.replace(/<IPEND>/g, "192.168.0.255")

        $("#custom .result").text(replace_str)

        DownloadShow()

    $("#custom .download").click ->
        registry_checks = (num.value for num in $('#registry .element .rir:checked'))
        country_checks = (num.value for num in $('#country .element .cc:checked'))
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
            custom_value = custom_area.val()
            custom_text = $.trim(custom_value)

            if registry_checks.length > 0
                list = registry_checks.join(',')
                output = "?registry=" + list
            else
                list = country_checks.join(',')
                output = "?country=" + list
            location.href = encodeURI(
                "/jsoncustom" + output + "&settings=" + custom_text)

    # -------------------------------------------------------------

    registry_all = $('#registry .all')
    country_all = $('#country .all')
    registries_selector = '#registry .element input'
    country_selector = '#country .element input'

    # レジストリのチェックボックスを外した場合、ALLにチェックがあったらはずす
    $('#registry .element .rir').click ->
        if not @.checked
            registry_all.prop {'checked': false}

    # 国名のチェックボックスを外した場合、ALLにチェックがあったらはずす
    $('#country .element .cc').click ->
        if not @.checked
            country_all.prop {'checked': false}

    CheckAllToggle = (selector, state) ->
        if state
            $(selector).prop {'checked': true}
        else
            $(selector).prop {'checked': false}

    # レジストリを全てチェック
    registry_all.click ->
        CheckAllToggle registries_selector, @.checked
        DownloadShow()

    # 国名を全てチェック
    country_all.click ->
        CheckAllToggle country_selector, @.checked
        DownloadShow()

    $(registries_selector).click ->
        DownloadShow()

    $(country_selector).click ->
        DownloadShow()

    # -------------------------------------------------------------

    CReset.click()
