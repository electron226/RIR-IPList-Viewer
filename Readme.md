# RIR IP Viewer
GAE専用

RIPE, ARIN, APNIC, LACNIC, AFRINICからIPの割当一覧を取得し、表示するWebアプリケーション。現状はIPv4にしか対応していない。
GAE上で動作するためある程度、制限がかかる。

### 主な使用方法
- TOPページで取得したいリポジトリと国名を設定・確認後、カスタマイズページでダウンロードする。  
もしくは、カスタマイズページに表示されたダウンロードURLをwgetなどで直接アクセスしてダウンロードする。  
[カスタマイズ専用ページ](http://8risky-hrd.appspot.com/custom)もある。
- 日本のみ取得する場合の例  
wget -O "jp.zip" "http://8risky-hrd.appspot.com/jsoncustom?country=JP&settings=%3CCC%3E:%20%3CIPSTART%3E-%3CIPEND%3E"
