#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file ips.py
# @brief IPアドレス関係
# @author electron226

import json

# IPアドレス範囲を格納するクラス
##
# @brief IPアドレス範囲を格納するクラス
#
#        変数
#        start : 数値化した開始IP
#        end : 数値化した終了IP(実際の最後のIPはこの数値の-1)
#        StartIP : 開始IP(文字列)を返すメソッド
#        EndIP : 終了IP(文字列)を返すメソッド
class IP:
    ##
    # @brief 初期化
    #
    #        xxx.xxx.xxx.xxx
    #        ip1.ip2.ip3.ip4
    # 
    # @param ip1 数値(0~255)
    # @param ip2 数値(0~255)
    # @param ip3 数値(0~255)
    # @param ip4 数値(0~255)
    # @param value 割当数
    #
    # @return なし
    def __init__(self, ip1, ip2, ip3, ip4, value):
        self.start = (int(ip1) << 24) + (int(ip2) << 16) + (int(ip3) << 8) + int(ip4)
        self.value = int(value)
        self.end = self.start + self.value 
    
    ##
    # @brief IPに変換
    #
    # @param value 変換する値
    #
    # @return IPv4の形式の文字列
    def __convert__(self, value):
        return '%d.%d.%d.%d' % (
                (value & 0xFF000000) >> 24, (value & 0x00FF0000) >> 16,
                (value & 0x0000FF00) >> 8, (value & 0x000000FF))
    
    ##
    # @brief 開始IPを文字列で返す
    #
    # @return IPv4の形式の文字列
    def StartIP(self):
        return self.__convert__(self.start)

    ##
    # @brief 終了IPを文字列で返す
    #
    # @return IPv4の形式の文字列
    def EndIP(self):
        return self.__convert__(self.end - 1)

##
# @brief JSON形式のデータに変換
class IPEncoder(json.JSONEncoder):
    ##
    # @brief JSON形式のデータに変換。
    #
    #        引数がIPクラスのオブジェクトじゃない場合、
    #        デフォルトの処理が行われる。
    #
    # @param obj IPクラスのオブジェクト
    #
    # @return 変換されたJSON形式のデータ
    def default(self, obj):
        if isinstance(obj, IP):
            return [obj.start, obj.value]
        return json.JSONEncoder.default(self, obj)

##
# @brief IPクラスのオブジェクトに変換
#
# @param dec JSON形式のデータ
#
# @return IPクラスのオブジェクト
def IPDecoder(dec):
    if isinstance(dec, list):
        ip = IP(0, 0, 0, 0, 0)
        ip.start = dec[0]
        ip.value = dec[1]
        ip.end = ip.start + ip.value
        return ip
    raise ValueError, "not list object."
