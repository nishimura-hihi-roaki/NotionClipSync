#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from pathlib import Path
from notion_client import Client


class SetupGUI:
    def __init__(self, env_file_path=None):
        """
        env_file_path: .envファイルの保存先パス（Pathオブジェクト）
        """
        self.env_file_path = env_file_path or Path.home() / '.clip_to_notion' / '.env'

        self.root = tk.Tk()
        self.root.title("Clip to Notion - 初期設定")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # 現在の設定を読み込み
        self.load_current_settings()

        # UI構築
        self.create_widgets()

    def load_current_settings(self):
        """既存の.envファイルから設定を読み込み"""
        self.current_api_key = ''
        self.current_database_id = ''
        self.current_hotkey = '⌘⇧V'  # デフォルト値

        # .envファイルが存在する場合、そこから読み込む
        if self.env_file_path.exists():
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('NOTION_API_KEY='):
                        self.current_api_key = line.split('=', 1)[1].strip('"\'')
                    elif line.startswith('NOTION_DATABASE_ID='):
                        self.current_database_id = line.split('=', 1)[1].strip('"\'')
                    elif line.startswith('HOTKEY='):
                        self.current_hotkey = line.split('=', 1)[1].strip('"\'')

    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(
            main_frame, 
            text="📋 Clip to Notion 初期設定", 
            font=("Helvetica", 18, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 説明文
        desc_label = ttk.Label(
            main_frame,
            text="Notionとの連携設定を行います。\n各項目を入力後、「接続テスト」で確認してください。",
            justify=tk.LEFT
        )
        desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)

        # 1. Notion API Key
        ttk.Label(main_frame, text="1. Notion API Key:", font=("Helvetica", 11, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=(10, 5)
        )
        self.api_key_entry = ttk.Entry(main_frame, width=60, show="*")
        self.api_key_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.api_key_entry.insert(0, self.current_api_key)

        ttk.Label(
            main_frame, 
            text="https://www.notion.so/my-integrations から取得",
            foreground="gray",
            font=("Helvetica", 9)
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 2. Database ID
        ttk.Label(main_frame, text="2. Database ID:", font=("Helvetica", 11, "bold")).grid(
            row=5, column=0, sticky=tk.W, pady=(10, 5)
        )
        self.db_id_entry = ttk.Entry(main_frame, width=60)
        self.db_id_entry.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.db_id_entry.insert(0, self.current_database_id)

        ttk.Label(
            main_frame,
            text="NotionデータベースのURLから32文字の英数字をコピー",
            foreground="gray",
            font=("Helvetica", 9)
        ).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 3. ショートカットキー
        ttk.Label(main_frame, text="3. ショートカットキー:", font=("Helvetica", 11, "bold")).grid(
            row=8, column=0, sticky=tk.W, pady=(10, 5)
        )

        hotkey_frame = ttk.Frame(main_frame)
        hotkey_frame.grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        self.hotkey_var = tk.StringVar(value=self.current_hotkey)
        hotkey_options = ["⌘⇧V", "⌘⌃⇧V", "⌘⌥V", "⌘⇧N"]
        self.hotkey_combo = ttk.Combobox(
            hotkey_frame, 
            textvariable=self.hotkey_var,
            values=hotkey_options,
            width=15,
            state="readonly"
        )
        self.hotkey_combo.pack(side=tk.LEFT)

        ttk.Label(
            main_frame,
            text="⌘=Command, ⌃=Control, ⌥=Option, ⇧=Shift",
            foreground="gray",
            font=("Helvetica", 9)
        ).grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=(20, 0))

        # 接続テストボタン
        self.test_button = ttk.Button(
            button_frame,
            text="接続テスト",
            command=self.test_connection
        )
        self.test_button.pack(side=tk.LEFT, padx=5)

        # 保存して終了ボタン
        self.save_button = ttk.Button(
            button_frame,
            text="保存して起動",
            command=self.save_and_exit,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        # キャンセルボタン
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=self.root.destroy
        ).pack(side=tk.LEFT, padx=5)

        # ステータス表示
        self.status_label = ttk.Label(
            main_frame,
            text="",
            foreground="blue",
            font=("Helvetica", 10)
        )
        self.status_label.grid(row=12, column=0, columnspan=2, pady=(20, 0))

    def test_connection(self):
        """Notion接続をテスト"""
        api_key = self.api_key_entry.get().strip()
        db_id = self.db_id_entry.get().strip()

        # 入力チェック
        if not api_key:
            messagebox.showerror("エラー", "Notion API Keyを入力してください")
            return

        if not db_id:
            messagebox.showerror("エラー", "Database IDを入力してください")
            return

        # 接続テスト
        self.status_label.config(text="接続テスト中...", foreground="blue")
        self.root.update()

        try:
            client = Client(auth=api_key)
            database = client.databases.retrieve(database_id=db_id)
            db_name = database.get("title", [{}])[0].get("plain_text", "Unknown")

            # 成功メッセージ
            self.status_label.config(
                text=f"✓ 接続成功: {db_name}",
                foreground="green"
            )

            # 保存ボタンを有効化
            self.save_button.config(state=tk.NORMAL)

            messagebox.showinfo(
                "接続成功",
                f"Notionへの接続に成功しました！\n\nデータベース名: {db_name}\n\n「保存して起動」ボタンで設定を保存してアプリを起動できます。"
            )

        except Exception as e:
            self.status_label.config(
                text="✗ 接続失敗",
                foreground="red"
            )
            messagebox.showerror(
                "接続エラー",
                f"Notionへの接続に失敗しました。\n\n{str(e)}\n\n設定を確認してください。"
            )

    def save_and_exit(self):
        """設定を保存して終了"""
        api_key = self.api_key_entry.get().strip()
        db_id = self.db_id_entry.get().strip()
        hotkey = self.hotkey_var.get()

        # .envファイルに保存
        env_content = f"""NOTION_API_KEY={api_key}
NOTION_DATABASE_ID={db_id}
HOTKEY={hotkey}
"""

        try:
            # ディレクトリが存在しない場合は作成
            self.env_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.write(env_content)

            messagebox.showinfo(
                "保存完了",
                f"設定を保存しました！\n\n保存先: {self.env_file_path}"
            )
            self.root.destroy()

        except Exception as e:
            messagebox.showerror(
                "保存エラー",
                f"設定の保存に失敗しました。\n\n{str(e)}"
            )

    def run(self):
        """GUIを起動"""
        self.root.mainloop()


if __name__ == "__main__":
    app = SetupGUI()
    app.run()