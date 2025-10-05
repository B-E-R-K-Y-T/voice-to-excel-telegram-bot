import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from orjson import JSONDecodeError

from config import settings
from src.giga import giga_api
from src.util import audio_to_text_bytes, create_excel_from_json

# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = settings.bot_token
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer("""
Привет! Отправь мне голосовое сообщение, и я преобразую его в таблицу!

Например:

Иванов оценка C(10 киберонов),
Смирнов Михаил оценка B(15 киберонов),
Беркут Тимофей оценка A(30 киберонов),
Сидоров Ваня не был

младшая группа город Москва
""")


@dp.message()
async def handle_voice_message(message: Message):
    user_id = message.from_user.id
    logger.info(f"Received message from user {user_id}")

    if settings.check_admin and settings.admin_id != user_id:
        logger.info(f"Skip user: {user_id}")
        return

    await bot.send_chat_action(message.chat.id, "typing")

    """Обрабатывает голосовые сообщения"""
    if not message.voice:
        logger.info(f"User {user_id} sent text message instead of voice")
        return await message.answer(
            "Отправь мне голосовое сообщение для распознавания!"
        )

    logger.info(f"Processing voice message from user {user_id}")
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    voice_bytes = await bot.download_file(file.file_path)
    json_data = {}
    text = ""

    try:
        # Преобразуем аудио в текст
        logger.debug("Converting audio to text")
        text = audio_to_text_bytes(voice_bytes.read())
        logger.info(f"Recognized text: '{text}'...")

        logger.debug("Sending text to GigaChat API")
        json_data = await giga_api.get_json_from_text(text)
        logger.info(f"Received JSON data from API: {bool(json_data)}")

    except JSONDecodeError as e:
        logger.error(f"JSON decode error for user {user_id}: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing voice message for user {user_id}: {e}")
        await message.answer("❌ Произошла непредвиденная ошибка при обработке сообщения")

    if not json_data:
        logger.warning(f"No JSON data received for user {user_id}")
        return await message.answer("❌ Не удалось распознать речь")

    try:
        # Создаем Excel таблицу из JSON
        logger.debug("Creating Excel file from JSON")
        excel_file = await create_excel_from_json(json_data)
        logger.info(f"Excel file created successfully: {bool(excel_file)}")

        if excel_file:
            # Отправляем Excel файл
            group = json_data.get('group', 'неизвестно')
            date = datetime.now().strftime("%d.%m.%Y")

            logger.info(f"Sending Excel file to user {user_id}. Group: {group}, Date: {date}")

            await message.answer_document(
                document=excel_file,
                caption=f"📊 Отчет по занятию\nГруппа: {group}\nДата: {date}\n\nВаш текст: {text[:150]}",
            )
            logger.info(f"Excel file successfully sent to user {user_id}")
        else:
            logger.error(f"Failed to create Excel file for user {user_id}")
            await message.answer("❌ Не удалось создать таблицу")

    except Exception as e:
        logger.error(f"Error creating/sending Excel file for user {user_id}: {e}")
        await message.answer("❌ Произошла ошибка при создании таблицы")


async def main():
    logger.info("Starting bot...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        raise
    finally:
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")