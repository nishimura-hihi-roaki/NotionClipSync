#!/usr/bin/env python3
"""
設定画面を別プロセスで起動するためのランチャー
"""
import sys
from pathlib import Path
from setup_gui import SetupGUI

if __name__ == "__main__":
    # コマンドライン引数から .env ファイルのパスを取得
    if len(sys.argv) > 1:
        env_path = Path(sys.argv[1])
    else:
        env_path = Path.home() / '.clip_to_notion' / '.env'
    
    app = SetupGUI(env_path)
    app.root.mainloop()
