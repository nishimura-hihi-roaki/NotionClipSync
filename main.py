#!/usr/bin/env python3
import rumps
import subprocess
import time
from pynput import keyboard
from datetime import datetime
from notion_api import NotionAPI


# 🚀 変更後のショートカット
# NEW_HOTKEY_DISPLAY = "⌘⌃⇧V" # 変更前
NEW_HOTKEY_DISPLAY = "⌘⇧V" # MacでControlは⌃、Optionは⌥、Shiftは⇧、Commandは⌘
# NEW_HOTKEY_PINPUT = '<cmd>+<ctrl>+<shift>+v' # 変更前
NEW_HOTKEY_PINPUT = '<cmd>+<shift>+v' # pynputのキーコード


class ClipToNotion(rumps.App):
    def __init__(self):
        super(ClipToNotion, self).__init__("📋", quit_button=None)
        self.menu = [
            # 🚀 変更点 1: メニューバーの表示テキストを更新
            rumps.MenuItem(f"選択テキストを登録 ({NEW_HOTKEY_DISPLAY})", callback=self.save_selection),
            None,
            rumps.MenuItem("終了", callback=self.quit_app)
        ]
        
        # Notion API初期化 (変更なし)
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
            
        # 🚀 変更点 2: グローバルホットキーの設定を更新
        self.hotkey_listener = keyboard.GlobalHotKeys({
            NEW_HOTKEY_PINPUT: self.save_selection
        })
        self.hotkey_listener.start()
        
        # 🚀 変更点 3: 起動時の説明文を更新
        print("\n" + "=" * 50)
        print("Clip to Notion - 起動完了")
        print("=" * 50)
        print("使い方:")
        print("1. テキストを選択")
        print(f"2. {NEW_HOTKEY_DISPLAY} を押す") # 更新
        print("3. Notionに保存されます")
        print("\n⚠️  アクセシビリティ権限が必要です:")
        print("    システム設定 → プライバシーとセキュリティ")
        print("    → アクセシビリティ → ターミナルを許可")
        print("\n終了: メニューバーアイコンから「終了」を選択")
        print("=" * 50 + "\n")
        
    def get_selected_text(self):
        """AppleScriptを使って選択テキストを取得"""
        # (変更なし)
        applescript = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            keystroke "c" using command down
            delay 0.1
        end tell
        
        set the clipboard to (the clipboard as text)
        return the clipboard
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"AppleScript エラー: {result.stderr}")
                return None
        
        except subprocess.TimeoutExpired:
            print("✗ タイムアウト: 選択テキストの取得に時間がかかりすぎました")
            return None
        except Exception as e:
            print(f"✗ エラー: {e}")
            return None
    
    def save_selection(self, _=None):
        """選択テキストをNotionに保存"""
        try:
            print("\n選択テキストを取得中...")
            
            # 選択テキストを取得 (変更なし)
            selected_text = self.get_selected_text()
            
            if not selected_text:
                print("⚠️  選択テキストが取得できませんでした")
                print("    - テキストを選択していますか？")
                print("    - アクセシビリティ権限は付与されていますか？")
                return
            
            # 空白のみの場合 (変更なし)
            if not selected_text.strip():
                print("⚠️  空のテキストです")
                return
            
            # タイムスタンプをタイトルとして使用 (変更なし)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"保存中: {len(selected_text)}文字")
            
            # Notionに保存 (変更なし)
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
    
    def quit_app(self, _):
        """アプリを終了"""
        print("\nアプリケーションを終了します...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        rumps.quit_application()


if __name__ == "__main__":
    app = ClipToNotion()
    app.run()
