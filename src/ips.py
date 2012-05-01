#!/usr/bin/env python
# vim: set fileencoding=utf-8
from django.utils import simplejson

# IPアドレス範囲を格納するクラス
# start : 数値化した開始IP
# end : 数値化した終了IP(実際の最後のIPはこの数値の-1)
# StartIP : 開始IP(文字列)を返すメソッド
# EndIP : 終了IP(文字列)を返すメソッド
class IP:
    # 初期化
    # xxx.xxx.xxx.xxx
    # ip1.ip2.ip3.ip4
    # value : 割当数
    def __init__(self, ip1, ip2, ip3, ip4, value):
        self.start = (int(ip1) << 24) + (int(ip2) << 16) + (int(ip3) << 8) + int(ip4)
        self.value = int(value)
        self.end = self.start + self.value 
    
    # 与えられた値をIPに変換
    def __convert__(self, value):
        return '%d.%d.%d.%d' % (
                (value & 0xFF000000) >> 24, (value & 0x00FF0000) >> 16,
                (value & 0x0000FF00) >> 8, (value & 0x000000FF))
    
    # 開始IPを文字列で返す
    def StartIP(self):
        return self.__convert__(self.start)

    # 終了IPを文字列で返す
    def EndIP(self):
        return self.__convert__(self.end - 1)

class IPEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, IP):
            return [obj.start, obj.value]
        return simplejson.JSONEncoder.default(self, obj)

def IPDecoder(dec):
    if isinstance(dec, list):
        ip = IP(0, 0, 0, 0, 0)
        ip.start = dec[0]
        ip.value = dec[1]
        ip.end = ip.start + ip.value
        return ip
    raise ValueError, "not list object."
