import os
from notion_client import Client
from datetime import datetime
from pathlib import Path

class NotionAPI:
    def __init__(self):
        # 環境変数から取得（load_dotenv済みの前提）
        self.api_key = os.environ.get('NOTION_API_KEY')
        self.database_id = os.environ.get('NOTION_DATABASE_ID')

        if not self.api_key:
            raise ValueError("NOTION_API_KEY環境変数が設定されていません")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID環境変数が設定されていません")

        self.client = Client(auth=self.api_key)
        self.title_property = None
        self.memo_property_name = "メモ"

    def create_page(self, title, content):
        """Notionデータベースに新しいページを作成"""
        try:
            # 初回のみデータベース構造を取得
            if self.title_property is None:
                database = self.client.databases.retrieve(database_id=self.database_id)
                properties_schema = database.get("properties", {})

                # タイトルプロパティを探す
                for prop_name, prop_info in properties_schema.items():
                    if prop_info.get("type") == "title":
                        self.title_property = prop_name
                        print(f"タイトルプロパティを検出: {prop_name}")
                        break

                if not self.title_property:
                    raise ValueError("タイトルプロパティが見つかりません")

            # 日付列に入れるための現在時刻を生成
            page_name_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # プロパティを構築
            properties = {
                # タイトルプロパティ（日付列）に現在時刻を設定
                self.title_property: {
                    "title": [
                        {
                            "text": {
                                "content": page_name_date 
                            }
                        }
                    ]
                },
                # 「メモ」プロパティに選択範囲のテキストを設定
                self.memo_property_name: {
                    "rich_text": [
                        {
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }

            # ページ本文は空
            children = [] 

            # Notionにページを作成
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )

            return {
                "success": True,
                "page_id": response["id"],
                "url": response["url"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def test_connection(self):
        """Notion接続をテスト"""
        try:
            # データベース情報を取得して接続を確認
            database = self.client.databases.retrieve(database_id=self.database_id)
            return {
                "success": True,
                "database_name": database.get("title", [{}])[0].get("plain_text", "Unknown")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }