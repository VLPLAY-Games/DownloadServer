# VL_PLAY Gamesのダウンロードマネージャー

- [Read in Russian](README.ru.md)
- [Read in English](README.md)

リアルタイムの進行状況トラッキングと使いやすいインターフェースを備えた最新のWebベースのダウンロードマネージャー。

![バージョン](https://img.shields.io/badge/version-0.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.1+-lightgrey.svg)
![Requests](https://img.shields.io/badge/requests-2.32+-lightgrey.svg)

## 🌟 特徴

- 🚀 **高速ダウンロード**とリアルタイム進行状況追跡
- 📊 **ライブ統計情報**（ダウンロード速度、進行度％、ファイルサイズ）
- ⏸️ **一時停止/再開**機能（アクティブなダウンロード用）
- 🔄 **最初からの再ダウンロード**
- 🗑️ **タスクの削除とファイルクリーンアップ**
- 🌐 **多言語対応**（英語、ロシア語）
- 🔐 **ユーザー認証システム**
- 📱 **レスポンシブデザイン**（全てのデバイスで動作）
- 💾 **ローカルファイル管理**、整理されたダウンロードフォルダ
- 📈 **プログレスバー**と速度インジケータ

## 🚀 クイックスタート

### 必要条件
- Python 3.11 以上
- pip パッケージマネージャー

### インストール
```bash
# リポジトリのクローン
git clone https://github.com/VLPLAY-Games/DownloadServer.git
cd DownloadServer

# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの実行
python app.py
```
### 設定項目
- サーバーポート（デフォルト：8100）
- ダウンロードディレクトリ（デフォルト：./downloads）