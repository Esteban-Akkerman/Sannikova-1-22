import pdfplumber
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import os

API_TOKEN = '23PD322PDSs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

menu_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
menu_buttons.add(KeyboardButton("Расписание на неделю"))
menu_buttons.add(KeyboardButton("Расписание на день"))

schedule_data = None

def load_schedule(file_path):
    """Загрузка расписания из Excel или PDF"""
    global schedule_data
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".xlsx":
        schedule_data = pd.read_excel(file_path)
    elif ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages)
            rows = [line.split("\t") for line in text.split("\n") if line.strip()]
            schedule_data = pd.DataFrame(rows, columns=["День", "Время", "Название пары", "Преподаватель"])
    else:
        raise ValueError("Неподдерживаемый формат файла")


def get_schedule_for_day(day):
    """Получить расписание на конкретный день"""
    if schedule_data is None:
        return "Расписание еще не загружено."
    day_schedule = schedule_data[schedule_data["День"].str.contains(day, case=False, na=False)]
    if day_schedule.empty:
        return f"На {day} занятий нет."
    return "\n".join(
        f"{row['Время']}: {row['Название пары']} ({row['Преподаватель']})"
        for _, row in day_schedule.iterrows()
    )


def get_schedule_for_week():
    """Получить расписание на неделю"""
    if schedule_data is None:
        return "Расписание еще не загружено."
    result = []
    for day in schedule_data["День"].unique():
        result.append(f" {day}:\n{get_schedule_for_day(day)}")
    return "\n\n".join(result)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Я бот для отображения расписания занятий. Загрузите файл расписания (PDF или Excel) или выберите действие:", reply_markup=menu_buttons)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_file(message: types.Message):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = f"downloads/{message.document.file_name}"
    os.makedirs("downloads", exist_ok=True)
    await bot.download_file(file.file_path, file_path)
    try:
        load_schedule(file_path)
        await message.reply("Файл расписания успешно загружен!")
    except Exception as e:
        await message.reply(f"Ошибка загрузки файла: {e}")


@dp.message_handler(lambda message: message.text == "Расписание на неделю")
async def week_schedule(message: types.Message):
    schedule = get_schedule_for_week()
    await message.reply(schedule)


@dp.message_handler(lambda message: message.text == "Расписание на день")
async def day_schedule(message: types.Message):
    await message.reply("Введите день недели (например, 'Понедельник'):")


@dp.message_handler()
async def handle_day_request(message: types.Message):
    day = message.text.strip()
    schedule = get_schedule_for_day(day)
    await message.reply(schedule)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
