import pandas as pd
import speech_recognition as sr
import soundfile as sf
import io
from aiogram.types import BufferedInputFile

_recognizer = sr.Recognizer()


def audio_to_text_bytes(audio_bytes: bytes) -> str:
    """Конвертирует аудио байты (OGA) в текст"""
    try:
        # Читаем OGG файл с помощью soundfile
        data, samplerate = sf.read(io.BytesIO(audio_bytes))

        # Конвертируем в WAV форма
        wav_bytes = io.BytesIO()
        sf.write(wav_bytes, data, samplerate, format="WAV")
        wav_bytes.seek(0)

        # Распознаем текст
        with sr.AudioFile(wav_bytes) as source:
            audio = _recognizer.record(source)
            text = _recognizer.recognize_google(audio, language="ru-RU")
            return text

    except Exception as e:
        print(f"Ошибка распознавания: {e}")
        return ""


async def create_excel_from_json(json_data):
    """Создает Excel файл из JSON данных"""
    try:
        # Создаем DataFrame из списка участников
        attendees = json_data.get("attendees", [])

        # Преобразуем данные для таблицы
        data = []
        for attendee in attendees:
            cyberons = attendee.get("cyberons", {})
            data.append(
                {
                    "Имя": attendee.get("name", ""),
                    "Присутствовал": "Да" if attendee.get("was", False) else "Нет",
                    "Базовые кибероны": cyberons.get("base", 0),
                    "Кибероны активности": cyberons.get("activity", 0),
                    "Кибероны достижений": cyberons.get("achievement", 0),
                    "Всего киберонов": cyberons.get("total", 0),
                }
            )

        # Создаем DataFrame
        df = pd.DataFrame(data)

        # Создаем Excel файл в памяти
        output = io.BytesIO()

        # Используем openpyxl как движок для лучшей совместимости
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Посещаемость", index=False)

            # Получаем workbook и worksheet для форматирования
            workbook = writer.book
            worksheet = writer.sheets["Посещаемость"]

            # Настраиваем ширину колонок
            column_widths = {
                "A": 20,  # Имя
                "B": 15,  # Присутствовал
                "C": 18,  # Базовые кибероны
                "D": 20,  # Кибероны активности
                "E": 22,  # Кибероны достижений
                "F": 18,  # Всего киберонов
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        output.seek(0)

        # Создаем имя файла
        group = json_data.get("group", "неизвестно").replace(" ", "_")
        date = json_data.get("date", "неизвестно").replace(" ", "_")
        filename = f"отчет_{group}_{date}.xlsx"

        # Создаем BufferedInputFile для отправки
        excel_buffer = output.getvalue()
        return BufferedInputFile(excel_buffer, filename=filename)

    except Exception as e:
        print(f"Ошибка при создании Excel: {e}")
        return None
