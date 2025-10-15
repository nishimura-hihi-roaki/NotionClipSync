#!/usr/bin/env python3
import rumps
import subprocess
import sys
import os
from pathlib import Path
from pynput import keyboard
from datetime import datetime
from dotenv import load_dotenv

# ⚠️ 注意: notion_api.py (NotionAPIクラス) は同じディレクトリにあると仮定します。
# 実際には、ビルド時に notion_api.py もデータファイルとして組み込む必要があります。
from notion_api import NotionAPI 

# .envファイルを読み込み
load_dotenv()


def check_env_file():
    """環境変数ファイルの存在と内容をチェック"""
    env_path = Path('.env')
    
    if not env_path.exists():
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return False
                
            # 必須項目があるかチェック
            has_api_key = 'NOTION_API_KEY=' in content
            has_db_id = 'NOTION_DATABASE_ID=' in content
            
            # 設定ファイルが更新された場合を考慮し、環境変数を再読み込み
            load_dotenv(override=True) 
            
            return has_api_key and has_db_id
    except:
        return False


def run_setup():
    """セットアップGUIを起動（修正版：Resourcesフォルダのパスに対応）"""
    print("\n" + "=" * 50)
    print("初回セットアップが必要です")
    print("=" * 50)
    print("設定画面を起動しています...\n")
    
    # 🚨 【修正ポイント】 setup_gui.py のパスを取得するロジックを更新
    if getattr(sys, 'frozen', False):
        # バンドル環境: setup_gui.pyは Contents/Resources に組み込まれている
        try:
            # PyInstallerで --onefile を使った場合、sys._MEIPASS は一時展開ディレクトリを指す
            # setup_gui.py が 'Resources/' の中にあると仮定してパスを構築
            base_path = sys._MEIPASS
        except AttributeError:
            # sys._MEIPASS が使えない場合のフォールバック（通常は実行ファイルのあるディレクトリ）
            base_path = os.path.dirname(os.path.abspath(sys.executable))
            
        # ⚠️ Resourcesフォルダ内に配置されている場合、そのパスを明示的に指定する必要があります。
        # PyInstallerの組み込み方法によってパスは変わりますが、多くは sys._MEIPASS/setup_gui.py または
        # 実行ファイルのパスが Contents/MacOS/ の場合、実行ファイルの親ディレクトリ（Contents/MacOS）
        # の隣にある Resources フォルダを参照する必要があります。
        
        # 🚨 最も一般的な PyInstaller/onefile の組み込みを想定したパス
        setup_script_path = os.path.join(base_path, 'setup_gui.py') 
        
        # もし上記のパスで失敗する場合、代わりに .app/Contents/Resources/ の絶対パスを構築する
        # (ただしこれは複雑で、ビルド環境に依存しすぎるため、まずは上記を試すべきです)
    
    else:
        # 通常のPython実行環境
        setup_script_path = 'setup_gui.py'

    # 🚨 【デバッグポイント】ターミナルから実行してパスを確認するためのログ
    print(f"DEBUG: 実行しようとしているパス: {setup_script_path}")

    if not os.path.exists(setup_script_path):
        # 実行ファイルが見つからない場合は、ループを防ぐためここで終了
        print(f"FATAL ERROR: セットアップスクリプトが見つかりません! {setup_script_path}")
        sys.exit(1)

    try:
        # 解決されたパスでサブプロセスを起動
        result = subprocess.run([sys.executable, setup_script_path], check=True)
        
        # セットアップが完了したか再確認
        if not check_env_file():
            print("\n設定が保存されませんでした。アプリを終了します。")
            sys.exit(1)
            
    except subprocess.CalledProcessError:
        print("\nセットアップがキャンセルされました。アプリを終了します。")
        sys.exit(1)
    except Exception as e:
        print(f"\nエラー: セットアップGUIの起動中に問題が発生しました: {e}")
        sys.exit(1)


def load_hotkey_config():
    # ... (変更なし) ...
    default_display = "⌘⇧V"
    default_pynput = '<cmd>+<shift>+v'
    
    env_path = Path('.env')
    if not env_path.exists():
        return default_display, default_pynput
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
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
        
        # 起動メッセージ (変更なし)
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
        print("\n終了: メニューバーアイコンから「終了」を選択")
        print("=" * 50 + "\n")
        
    def get_selected_text(self):
        # ... (変更なし) ...
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
        # ... (変更なし) ...
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
        """設定画面を開いて再起動を促す（修正版：パス問題を解消）"""
        print("\n設定画面を起動しています...")
        
        # 🚨 【修正ポイント】run_setupと同じロジックでsetup_gui.pyのパスを取得
        if getattr(sys, 'frozen', False):
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.dirname(os.path.abspath(sys.executable))
                
            setup_script_path = os.path.join(base_path, 'setup_gui.py')
        else:
            setup_script_path = 'setup_gui.py'

        try:
            # setup_gui.pyを起動
            subprocess.run([sys.executable, setup_script_path], check=True)
            
            # 設定が更新されたので再起動を促す
            print("\n設定が更新されました。")
            response = rumps.alert(
                "設定を更新しました",
                "変更を反映するにはアプリを再起動してください。\n今すぐ再起動しますか？",
                ok="再起動する",
                cancel="後で"
            )
            
            if response == 1:  # OKボタンが押された
                print("アプリを終了します。再度アプリを起動してください。")
                self.quit_app(None)
            
        except subprocess.CalledProcessError:
            print("\n設定変更がキャンセルされました。")
        except FileNotFoundError:
            rumps.alert("エラー", f"setup_gui.py が見つかりません: {setup_script_path}")
            
    def quit_app(self, _):
        # ... (変更なし) ...
        print("\nアプリケーションを終了します...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        rumps.quit_application()


if __name__ == "__main__":
    # 初回起動時のセットアップチェック
    if not check_env_file():
        run_setup()
    
    # メインアプリを起動
    app = ClipToNotion()
    app.run()
