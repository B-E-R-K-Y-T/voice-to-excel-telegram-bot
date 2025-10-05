from typing import Literal, Final

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path, PurePath

BASE_DIR: Final[PurePath] = Path(__file__).parent


class Settings(BaseSettings):
    admin_id: int = Field(..., alias="ADMIN_ID")
    check_admin: bool = Field(False, alias="CHECK_ADMIN")
    bot_token: str = Field(..., alias="BOT_TOKEN")
    giga_chat_token: str = Field(..., alias="GIGA_CHAT_TOKEN")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field("DEBUG", alias="LOG_LEVEL")

    class Config:
        env_file = BASE_DIR / '.env'
        env_file_encoding = "utf-8"


settings = Settings()
