# -*- coding: utf-8 -*-
"""
Telegram delivery helper (stateless): send files to a Telegram chat via HTTP API.
This module is intentionally minimal and independent from bot runtime.
"""
import os

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

def send_file_to_user(chat_id: int, file_path: str, caption: str = "") -> bool:
    """Send a document to a Telegram user via HTTP API.
    Requires TELEGRAM_BOT_TOKEN in environment.
    """
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token or token == 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
            return False
        if requests is None:
            return False
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption[:1024]
            resp = requests.post(url, files=files, data=data, timeout=60)
            return bool(resp and resp.ok)
    except Exception:
        return False
