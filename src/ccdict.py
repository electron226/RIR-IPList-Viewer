﻿#!/usr/bin/env python
# vim: set fileencoding=utf-8

#2012/5/20 更新
countries_dict = {
        'AD': 'アンドラ',
        'AE': 'アラブ首長国連邦',
        'AF': 'アフガニスタン',
        'AG': 'アンティグア・バーブーダ',
        'AI': 'アンギラ',
        'AL': 'アルバニア',
        'AM': 'アルメニア',
        'AN': 'オランダ領アンティル',
        'AO': 'アンゴラ',
        'AP': 'アジア太平洋連合',
        'AQ': '南極',
        'AR': 'アルゼンチン',
        'AS': 'アメリカ領サモア',
        'AT': 'オーストリア',
        'AU': 'オーストラリア',
        'AW': 'アルバ',
        'AX': 'オーランド諸島',
        'AZ': 'アゼルバイジャン',
        'BA': 'ボスニア・ヘルツェゴビナ',
        'BB': 'バルバドス',
        'BD': 'バングラデシュ',
        'BE': 'ベルギー',
        'BF': 'ブルキナファソ',
        'BG': 'ブルガリア',
        'BH': 'バーレーン',
        'BI': 'ブルンジ',
        'BJ': 'ベナン',
        'BL': 'サン・バルテルミー島',
        'BM': 'バミューダ諸島',
        'BN': 'ブルネイ',
        'BO': 'ボリビア',
        'BR': 'ブラジル',
        'BS': 'バハマ',
        'BT': 'ブータン',
        'BV': 'ブーベ島',
        'BW': 'ボツワナ',
        'BY': 'ベラルーシ',
        'BZ': 'ベリーズ',
        'CA': 'カナダ',
        'CC': 'ココス諸島',
        'CD': 'コンゴ民主共和国',
        'CF': '中央アフリカ',
        'CG': 'コンゴ共和国',
        'CH': 'スイス',
        'CI': 'コートジボワール',
        'CK': 'クック諸島',
        'CL': 'チリ',
        'CM': 'カメルーン',
        'CN': '中国',
        'CO': 'コロンビア',
        'CR': 'コスタリカ',
        'CU': 'キューバ',
        'CV': 'カボベルデ',
        'CX': 'クリスマス島',
        'CY': 'キプロス',
        'CZ': 'チェコ',
        'DE': 'ドイツ',
        'DJ': 'ジブチ',
        'DK': 'デンマーク',
        'DM': 'ドミニカ',
        'DO': 'ドミニカ共和国',
        'DZ': 'アルジェリア',
        'EC': 'エクアドル',
        'EE': 'エストニア',
        'EG': 'エジプト',
        'EH': '西サハラ',
        'ER': 'エリトリア',
        'ES': 'スペイン',
        'ET': 'エチオピア',
        'EU': '欧州連合',
        'FI': 'フィンランド',
        'FJ': 'フィジー',
        'FK': 'フォークランド諸島',
        'FM': 'ミクロネシア連邦',
        'FO': 'フェロー諸島',
        'FR': 'フランス',
        'GA': 'ガボン',
        'GB': 'イギリス',
        'GD': 'グレナダ',
        'GE': 'グルジア',
        'GF': 'フランス領ギアナ',
        'GG': 'ガーンジー島',
        'GH': 'ガーナ',
        'GI': 'ジブラルタル',
        'GL': 'グリーンランド',
        'GM': 'ガンビア',
        'GN': 'ギニア',
        'GP': 'グアドループ島',
        'GQ': '赤道ギニア',
        'GR': 'ギリシャ',
        'GS': '南ジョージア島・南サンドイッチ諸島',
        'GT': 'グアテマラ',
        'GU': 'グアム',
        'GW': 'ギニアビサウ',
        'GY': 'ガイアナ',
        'HK': '香港',
        'HM': 'ヘアド島・マクドナルド諸島',
        'HN': 'ホンジュラス',
        'HR': 'クロアチア',
        'HT': 'ハイチ',
        'HU': 'ハンガリー',
        'ID': 'インドネシア',
        'IE': 'アイルランド',
        'IL': 'イスラエル',
        'IM': 'マン島',
        'IN': 'インド',
        'IO': 'イギリス領インド洋地域',
        'IQ': 'イラク',
        'IR': 'イラン',
        'IS': 'アイスランド',
        'IT': 'イタリア',
        'JE': 'ジャージー島',
        'JM': 'ジャマイカ',
        'JO': 'ヨルダン',
        'JP': '日本',
        'KE': 'ケニア',
        'KG': 'キルギス',
        'KH': 'カンボジア',
        'KI': 'キリバス',
        'KM': 'コモロ',
        'KN': 'セントクリストファー・ネビス',
        'KP': '北朝鮮',
        'KR': '韓国',
        'KW': 'クウェート',
        'KY': 'ケイマン諸島',
        'KZ': 'カザフスタン',
        'LA': 'ラオス',
        'LB': 'レバノン',
        'LC': 'セントルシア',
        'LI': 'リヒテンシュタイン',
        'LK': 'スリランカ',
        'LR': 'リベリア',
        'LS': 'レソト',
        'LT': 'リトアニア',
        'LU': 'ルクセンブルク',
        'LV': 'ラトビア',
        'LY': 'リビア  Libyan Arab',
        'MA': 'モロッコ',
        'MC': 'モナコ',
        'MD': 'モルドバ',
        'ME': 'モンテネグロ',
        'MF': 'サン・マルタン島',
        'MG': 'マダガスカル',
        'MH': 'マーシャル諸島',
        'MK': 'マケドニア',
        'ML': 'マリ',
        'MM': 'ミャンマー',
        'MN': 'モンゴル',
        'MO': 'マカオ',
        'MP': '北マリアナ諸島',
        'MQ': 'マルティニク',
        'MR': 'モーリタニア',
        'MS': 'モントセラト',
        'MT': 'マルタ',
        'MU': 'モーリシャス',
        'MV': 'モルディブ',
        'MW': 'マラウイ',
        'MX': 'メキシコ',
        'MY': 'マレーシア',
        'MZ': 'モザンビーク',
        'NA': 'ナミビア',
        'NC': 'ニューカレドニア',
        'NE': 'ニジェール',
        'NF': 'ノーフォーク島',
        'NG': 'ナイジェリア',
        'NI': 'ニカラグア',
        'NL': 'オランダ',
        'NO': 'ノルウェー',
        'NP': 'ネパール',
        'NR': 'ナウル',
        'NU': 'ニウエ',
        'NZ': 'ニュージーランド',
        'OM': 'オマーン',
        'PA': 'パナマ',
        'PE': 'ペルー',
        'PF': 'フランス領ポリネシア',
        'PG': 'パプアニューギニア',
        'PH': 'フィリピン',
        'PK': 'パキスタン',
        'PL': 'ポーランド',
        'PM': 'サンピエール・ミクロン島',
        'PN': 'ピトケアン',
        'PR': 'プエルトリコ',
        'PS': 'パレスチナ',
        'PT': 'ポルトガル',
        'PW': 'パラオ',
        'PY': 'パラグアイ',
        'QA': 'カタール',
        'RE': 'レユニオン',
        'RO': 'ルーマニア',
        'RS': 'セルビア',
        'RU': 'ロシア',
        'RW': 'ルワンダ',
        'SA': 'サウジアラビア',
        'SB': 'ソロモン諸島',
        'SC': 'セーシェル',
        'SD': 'スーダン',
        'SE': 'スウェーデン',
        'SG': 'シンガポール',
        'SH': 'セントヘレナ島',
        'SI': 'スロベニア',
        'SJ': 'スバールバル諸島・ヤンマイエン島',
        'SK': 'スロバキア',
        'SL': 'シエラレオネ',
        'SM': 'サンマリノ',
        'SN': 'セネガル',
        'SO': 'ソマリア',
        'SR': 'スリナム',
        'SS': '南スーダン',
        'ST': 'サントメ・プリンシペ',
        'SV': 'エルサルバドル',
        'SY': 'シリア',
        'SZ': 'スワジランド',
        'TC': 'タークスカイコス諸島',
        'TD': 'チャド',
        'TF': 'フランス領南方・南極地域',
        'TG': 'トーゴ',
        'TH': 'タイ',
        'TJ': 'タジキスタン',
        'TK': 'トケラウ諸島',
        'TL': '東ティモール',
        'TM': 'トルクメニスタン',
        'TN': 'チュニジア',
        'TO': 'トンガ',
        'TR': 'トルコ',
        'TT': 'トリニダード・トバゴ',
        'TV': 'ツバル',
        'TW': '台湾',
        'TZ': 'タンザニア',
        'UA': 'ウクライナ',
        'UG': 'ウガンダ',
        'UM': 'アメリカ領太平洋諸島',
        'US': 'アメリカ合衆国',
        'UY': 'ウルグアイ',
        'UZ': 'ウズベキスタン',
        'VA': 'バチカン',
        'VC': 'セントビンセント・グレナディーン',
        'VE': 'ベネズエラ',
        'VG': 'イギリス領バージン諸島',
        'VI': 'アメリカ領バージン諸島',
        'VN': 'ベトナム',
        'VU': 'バヌアツ',
        'WF': 'ワリスフュチュナ',
        'WS': 'サモア',
        'YE': 'イエメン',
        'YT': 'マヨット島',
        'ZA': '南アフリカ共和国',
        'ZM': 'ザンビア',
        'ZW': 'ジンバブエ',
    }

if __name__ == '__main__':
    for k, v in sorted(countries_dict.iteritems()):
        print "'" + k + "': '" + v + "',"
