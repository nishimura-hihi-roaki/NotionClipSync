#!/usr/bin/env python3
import rumps
import pyperclip
import sys
import os
from pathlib import Path
from pynput import keyboard
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

from notion_api import NotionAPI 

# .envファイルのパスをユーザーのホームディレクトリに設定
ENV_FILE_PATH = Path.home() / '.clip_to_notion' / '.env'

def ensure_env_directory():
    """環境設定ファイル用のディレクトリを作成"""
    ENV_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

def check_env_file():
    """環境変数ファイルの存在と内容をチェック"""
    if not ENV_FILE_PATH.exists():
        return False
    
    try:
        with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return False
                
            # 必須項目があるかチェック
            has_api_key = 'NOTION_API_KEY=' in content
            has_db_id = 'NOTION_DATABASE_ID=' in content
            
            # 環境変数を読み込み
            load_dotenv(ENV_FILE_PATH, override=True)
            
            return has_api_key and has_db_id
    except:
        return False


def run_setup():
    """セットアップをrumpsダイアログで実行"""
    print("\n" + "=" * 50)
    print("初回セットアップが必要です")
    print("=" * 50)
    
    ensure_env_directory()
    
    # 説明ダイアログ
    rumps.alert(
        "Clip to Notion - 初期設定",
        "Notionとの連携設定を行います。\n\n"
        "1. Notion API Key を入力\n"
        "2. Database ID を入力\n"
        "3. ショートカットキーを選択\n\n"
        "準備ができたら「OK」を押してください。",
        ok="OK"
    )
    
    # API Key入力
    window = rumps.Window(
        "Notion API Key を入力してください\n\n"
        "取得方法: https://www.notion.so/my-integrations",
        "Notion API Key",
        default_text="",
        ok="次へ",
        cancel="キャンセル",
        dimensions=(320, 24)
    )
    response = window.run()
    
    if not response.clicked:
        print("セットアップがキャンセルされました")
        sys.exit(1)
    
    api_key = response.text.strip()
    
    if not api_key:
        rumps.alert("エラー", "API Key を入力してください")
        sys.exit(1)
    
    # Database ID入力
    window = rumps.Window(
        "Database ID を入力してください\n\n"
        "NotionデータベースのURLから32文字の英数字をコピー",
        "Database ID",
        default_text="",
        ok="次へ",
        cancel="キャンセル",
        dimensions=(320, 24)
    )
    response = window.run()
    
    if not response.clicked:
        print("セットアップがキャンセルされました")
        sys.exit(1)
    
    db_id = response.text.strip()
    
    if not db_id:
        rumps.alert("エラー", "Database ID を入力してください")
        sys.exit(1)
    
    # 接続テスト
    print("Notion接続をテスト中...")
    try:
        client = Client(auth=api_key)
        database = client.databases.retrieve(database_id=db_id)
        db_name = database.get("title", [{}])[0].get("plain_text", "Unknown")
        print(f"✓ 接続成功: {db_name}")
    except Exception as e:
        print(f"✗ 接続失敗: {e}")
        rumps.alert("接続エラー", f"Notionへの接続に失敗しました。\n\n{str(e)}\n\n設定を確認してください。")
        sys.exit(1)
    
    # ショートカットキー選択
    response = rumps.alert(
        "ショートカットキーを選択",
        f"接続成功: {db_name}\n\n"
        "ショートカットキーを選択してください。\n\n"
        "⌘=Command, ⇧=Shift, ⌃=Control, ⌥=Option",
        ok="⌘⇧V (推奨)",
        cancel="⌘⇧N",
        other="⌘⌃⇧V"
    )
    
    if response == 1:  # OK
        hotkey = "⌘⇧V"
    elif response == 0:  # Cancel
        hotkey = "⌘⇧N"
    else:  # Other
        hotkey = "⌘⌃⇧V"
    
    # 設定を保存
    env_content = f"""NOTION_API_KEY={api_key}
NOTION_DATABASE_ID={db_id}
HOTKEY={hotkey}
"""
    
    try:
        with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✓ 設定を保存しました: {ENV_FILE_PATH}")
        rumps.alert("設定完了", f"設定を保存しました！\n\nデータベース: {db_name}\nショートカット: {hotkey}")
        
    except Exception as e:
        print(f"✗ 保存失敗: {e}")
        rumps.alert("保存エラー", f"設定の保存に失敗しました。\n\n{str(e)}")
        sys.exit(1)


def load_hotkey_config():
    """ホットキー設定を読み込み"""
    default_display = "⌘⇧V"
    default_pynput = '<cmd>+<shift>+v'
    
    if not ENV_FILE_PATH.exists():
        return default_display, default_pynput
    
    try:
        with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('HOTKEY='):
                    hotkey = line.split('=', 1)[1].strip().strip('"\'')
                    
                    hotkey_map = {
                        "⌘⇧V": '<cmd>+<shift>+v',
                        "⌘⌃⇧V": '<cmd>+<ctrl>+<shift>+v',
                        "⌘⌥V": '<cmd>+<alt>+v',
                        "⌘⇧N": '<cmd>+<shift>+n'
                    }
                    
                    return hotkey, hotkey_map.get(hotkey, default_pynput)
    except:
        pass
    
    return default_display, default_pynput


class ClipToNotion(rumps.App):
    def __init__(self):
        super(ClipToNotion, self).__init__("📋", quit_button=None)
        
        # ホットキー設定を読み込み
        self.hotkey_display, self.hotkey_pynput = load_hotkey_config()
        
        self.menu = [
            rumps.MenuItem(f"クリップボードを登録 ({self.hotkey_display})", callback=self.save_selection),
            None,
            rumps.MenuItem("設定を変更", callback=self.open_settings),
            None,
            rumps.MenuItem("終了", callback=self.quit_app)
        ]
        
        # Notion API初期化
        try:
            self.notion_api = NotionAPI()
            test_result = self.notion_api.test_connection()
            if test_result['success']:
                print(f"✓ Notion接続成功: {test_result.get('database_name', 'Unknown')}")
            else:
                print(f"✗ Notion接続失敗: {test_result['error']}")
                rumps.alert("Notion接続エラー", test_result['error'])
        except Exception as e:
            print(f"✗ 初期化エラー: {e}")
            rumps.alert("初期化エラー", str(e))
            
        # グローバルホットキーの設定
        self.hotkey_listener = keyboard.GlobalHotKeys({
            self.hotkey_pynput: self.save_selection
        })
        self.hotkey_listener.start()
        
        # 起動メッセージ
        print("\n" + "=" * 50)
        print("Clip to Notion - 起動完了")
        print("=" * 50)
        print("使い方:")
        print("1. テキストを選択して ⌘+C でコピー")
        print(f"2. {self.hotkey_display} を押す")
        print("3. Notionに保存されます")
        print("\n終了: メニューバーアイコンから「終了」を選択")
        print("=" * 50 + "\n")
        
    def get_selected_text(self):
        """クリップボードから直接テキストを取得"""
        try:
            text = pyperclip.paste()
            return text if text else None
        except Exception as e:
            print(f"✗ クリップボード取得エラー: {e}")
            return None
    
    def save_selection(self, _=None):
        """クリップボードのテキストをNotionに保存"""
        try:
            print("\nクリップボードからテキストを取得中...")
            
            selected_text = self.get_selected_text()
            
            if not selected_text:
                print("⚠️  クリップボードが空です")
                print("    テキストをコピー(⌘+C)してから実行してください")
                return
            
            if not selected_text.strip():
                print("⚠️  空のテキストです")
                return
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"保存中: {len(selected_text)}文字")
            
            result = self.notion_api.create_page(
                title=timestamp,
                content=selected_text
            )
            
            if result['success']:
                print(f"✓ 保存成功: {timestamp}")
                print(f"  URL: {result['url']}\n")
            else:
                print(f"✗ 保存失敗: {result['error']}\n")
        
        except Exception as e:
            print(f"✗ エラー: {e}\n")
    
    def open_settings(self, _):
        """設定画面を開く（rumps ダイアログ版）"""
        print("\n設定画面を起動しています...")
        
        # 現在の設定を読み込み
        current_api_key = os.environ.get('NOTION_API_KEY', '')
        current_db_id = os.environ.get('NOTION_DATABASE_ID', '')
        
        # API Key入力
        window = rumps.Window(
            "Notion API Key を入力してください\n\n"
            "取得方法: https://www.notion.so/my-integrations",
            "Notion API Key",
            default_text=current_api_key,
            ok="次へ",
            cancel="キャンセル",
            dimensions=(320, 24)
        )
        response = window.run()
        
        if not response.clicked:
            print("設定変更がキャンセルされました")
            return
        
        api_key = response.text.strip()
        
        if not api_key:
            rumps.alert("エラー", "API Key を入力してください")
            return
        
        # Database ID入力
        window = rumps.Window(
            "Database ID を入力してください\n\n"
            "NotionデータベースのURLから32文字の英数字をコピー",
            "Database ID",
            default_text=current_db_id,
            ok="次へ",
            cancel="キャンセル",
            dimensions=(320, 24)
        )
        response = window.run()
        
        if not response.clicked:
            print("設定変更がキャンセルされました")
            return
        
        db_id = response.text.strip()
        
        if not db_id:
            rumps.alert("エラー", "Database ID を入力してください")
            return
        
        # 接続テスト
        print("Notion接続をテスト中...")
        try:
            client = Client(auth=api_key)
            database = client.databases.retrieve(database_id=db_id)
            db_name = database.get("title", [{}])[0].get("plain_text", "Unknown")
            print(f"✓ 接続成功: {db_name}")
        except Exception as e:
            print(f"✗ 接続失敗: {e}")
            rumps.alert("接続エラー", f"Notionへの接続に失敗しました。\n\n{str(e)}")
            return
        
        # ショートカットキー選択
        response = rumps.alert(
            "ショートカットキーを選択",
            f"接続成功: {db_name}\n\n"
            "ショートカットキーを選択してください。",
            ok="⌘⇧V (推奨)",
            cancel="⌘⇧N",
            other="⌘⌃⇧V"
        )
        
        if response == 1:  # OK
            hotkey = "⌘⇧V"
        elif response == 0:  # Cancel
            hotkey = "⌘⇧N"
        else:  # Other
            hotkey = "⌘⌃⇧V"
        
        # 設定を保存
        env_content = f"""NOTION_API_KEY={api_key}
NOTION_DATABASE_ID={db_id}
HOTKEY={hotkey}
"""
        
        try:
            with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print(f"✓ 設定を保存しました: {ENV_FILE_PATH}")
            
            response = rumps.alert(
                "設定を更新しました",
                f"設定を保存しました！\n\n"
                f"データベース: {db_name}\n"
                f"ショートカット: {hotkey}\n\n"
                "変更を反映するにはアプリを再起動してください。\n"
                "今すぐ再起動しますか？",
                ok="再起動する",
                cancel="後で"
            )
            
            if response == 1:
                self.quit_app(None)
            
        except Exception as e:
            print(f"✗ 保存失敗: {e}")
            rumps.alert("保存エラー", f"設定の保存に失敗しました。\n\n{str(e)}")
            
    def quit_app(self, _):
        """アプリケーションを終了"""
        print("\nアプリケーションを終了します...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        rumps.quit_application()


if __name__ == "__main__":
    # ディレクトリを確保
    ensure_env_directory()
    
    # .envファイルを読み込み
    load_dotenv(ENV_FILE_PATH)
    
    # 初回起動時のセットアップチェック
    if not check_env_file():
        run_setup()
    
    # メインアプリを起動
    app = ClipToNotion()
    app.run()
