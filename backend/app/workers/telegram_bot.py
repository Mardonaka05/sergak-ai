"""
Telegram bot worker — sends alerts to per-department chats.

Listens to AlertManager events and dispatches:
- screenshot + caption
- inline 'Acknowledge' button (TODO)
"""
import asyncio
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile
from app.core.config import settings


class TelegramNotifier:
    def __init__(self, token: str = None, default_chat: str = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.default_chat = default_chat or settings.TELEGRAM_DEFAULT_CHAT
        self.bot = None
        if self.token:
            self.bot = Bot(token=self.token)

    async def send_alert(self, alert: dict, chat_id: str = None):
        """Send a single alert to Telegram"""
        if not self.bot:
            print(f"[Telegram] Bot disabled — would have sent: {alert['message']}")
            return

        chat = chat_id or self.default_chat
        priority_emoji = {"critical": "🚨", "high": "⚠️", "normal": "📢", "low": "ℹ️"}.get(alert.get("priority", "normal"), "📢")

        caption = (
            f"{priority_emoji} <b>QOIDABUZARLIK ANIQLANDI</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📷 Kamera: <b>{alert['camera_name']}</b>\n"
            f"⚠️ Modul: <b>{alert['module']}</b>\n"
            f"📝 {alert['message']}\n"
            f"🎯 Aniqlik: {int(alert['confidence']*100)}%\n"
            f"🕐 Vaqt: {alert['timestamp']}"
        )

        snapshot = Path(alert.get("snapshot_path", ""))
        try:
            if snapshot.exists():
                await self.bot.send_photo(chat_id=chat, photo=FSInputFile(snapshot), caption=caption, parse_mode="HTML")
            else:
                await self.bot.send_message(chat_id=chat, text=caption, parse_mode="HTML")
        except Exception as e:
            print(f"[Telegram] send failed: {e}")


# Global notifier
notifier = TelegramNotifier()


async def telegram_listener(alert: dict):
    """Subscribe this to AlertManager"""
    await notifier.send_alert(alert)
