#!/usr/bin/env python3
import rumps
import subprocess
import sys
import os
from pathlib import Path
from pynput import keyboard
from datetime import datetime
from dotenv import load_dotenv

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
    """セットアップGUIを表示"""
    print("\n" + "=" * 50)
    print("初回セットアップが必要です")
    print("=" * 50)
    print("設定画面を起動しています...\n")
    
    ensure_env_directory()
    
    try:
        from setup_gui import SetupGUI
        
        # ウィンドウを作成して表示
        setup = SetupGUI(ENV_FILE_PATH)
        setup.root.mainloop()
        
        # セットアップが完了したか再確認
        if not check_env_file():
            print("\n設定が保存されませんでした。アプリを終了します。")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nエラー: セットアップGUIの起動中に問題が発生しました: {e}")
        import traceback
        traceback.print_exc()
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
            rumps.MenuItem(f"選択テキストを登録 ({self.hotkey_display})", callback=self.save_selection),
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
        print("1. テキストを選択")
        print(f"2. {self.hotkey_display} を押す")
        print("3. Notionに保存されます")
        print("\n⚠️  アクセシビリティ権限が必要です:")
        print("    システム設定 → プライバシーとセキュリティ")
        print("    → アクセシビリティ → このアプリを許可")
        print(f"\n⚠️  ショートカットキーが動かない場合:")
        print(f"    上記の設定を確認し、アプリを再起動してください")
        print("\n終了: メニューバーアイコンから「終了」を選択")
        print("=" * 50 + "\n")
        
    def get_selected_text(self):
        """選択されたテキストを取得（AppleScript使用）"""
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
            
            selected_text = self.get_selected_text()
            
            if not selected_text:
                print("⚠️  選択テキストが取得できませんでした")
                print("    - テキストを選択していますか？")
                print("    - アクセシビリティ権限は付与されていますか？")
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
        """設定画面を別プロセスで起動"""
        print("\n設定画面を起動しています...")
        
        try:
            # setup_launcher.py のパスを取得
            if getattr(sys, 'frozen', False):
                # パッケージ化環境
                base_path = sys._MEIPASS
                launcher_script = os.path.join(base_path, 'setup_launcher.py')
            else:
                # 開発環境
                launcher_script = 'setup_launcher.py'
            
            # Python インタープリタのパスを取得
            if getattr(sys, 'frozen', False):
                # パッケージ化環境: sys.executable はアプリ本体なので使えない
                # 代わりに、システムの Python を使う
                python_executable = '/usr/bin/python3'
            else:
                python_executable = sys.executable
            
            # 別プロセスで起動（非同期）
            subprocess.Popen(
                [python_executable, launcher_script, str(ENV_FILE_PATH)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("設定画面を別ウィンドウで起動しました")
            print("設定を変更した場合は、アプリを再起動してください")
            
        except Exception as e:
            print(f"\n設定画面のエラー: {e}")
            import traceback
            traceback.print_exc()
            rumps.alert("エラー", f"設定画面の起動に失敗しました:\n{str(e)}")
            
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
