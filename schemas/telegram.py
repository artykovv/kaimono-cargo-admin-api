from typing import List
from pydantic import BaseModel

class TelegramMessage(BaseModel):
    message_text: str
    telegram_chat_ids: List[int] = None