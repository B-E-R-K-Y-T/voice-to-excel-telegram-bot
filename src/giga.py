from typing import Final

import orjson
from gigachat import GigaChat
from gigachat.models import Messages, MessagesRole, Chat

from config import settings, BASE_DIR

with open(BASE_DIR / "system_prompt.txt", encoding="utf-8") as file_prompt:
    SYSTEM_PROMPT: Final[Messages] = Messages(
        role=MessagesRole.SYSTEM,
        content=file_prompt.read(),
    )


class GigaApi:
    def __init__(self):
        self.giga_bot = GigaChat(
            credentials=settings.giga_chat_token,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            model="GigaChat",
        )

    async def get_json_from_text(self, message: str) -> list[dict]:
        response = await self.giga_bot.achat(
            Chat(
                messages=[
                    SYSTEM_PROMPT,
                    Messages(role=MessagesRole.USER, content=message),
                ]
            )
        )

        return orjson.loads(response.choices[0].message.content)


giga_api = GigaApi()
