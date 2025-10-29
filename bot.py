import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os

# 🔑 Укажи токен своего бота
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔹 Списки вопросов по режимам
QUESTIONS = {
    "Обычный": [
        "Как тебя зовут?",
        "Сколько тебе лет?",
    ],
    "Средний": [
        "Как тебя зовут?",
        "Сколько тебе лет?",
        "Где ты живёшь?",
        "Чем увлекаешься?",
    ],
    "Максимальный": [
        "Как тебя зовут?",
        "Сколько тебе лет?",
        "Где ты живёшь?",
        "Чем увлекаешься?",
        "Какая у тебя мечта?",
        "Какую книгу ты недавно прочитал?",
        "Как ты любишь проводить выходные?",
    ]
}

# 🧭 Храним состояние пользователей
user_modes = {}
user_states = {}  # {user_id: {"mode": str, "q_index": int, "answers": []}}

def settings_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Обычный режим"),
                KeyboardButton(text="Средний режим"),
                KeyboardButton(text="Максимальный режим"),
            ]
        ],
        resize_keyboard=True
    )
    return kb

# 🔹 Команда /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_modes[message.from_user.id] = "Обычный"
    await message.answer(
        "Привет! Я бот, который узнаёт о тебе больше 😊\n"
        "Используй /info, чтобы ответить на вопросы.\n"
        "Используй /settings, чтобы выбрать режим.",
    )


# 🔹 Команда /settings
@dp.message(Command("settings"))
async def settings_cmd(message: types.Message):
    await message.answer("Выбери режим:", reply_markup=settings_keyboard())


# 🔹 Установка режима
@dp.message(lambda m: m.text in ["Обычный режим", "Средний режим", "Максимальный режим"])
async def set_mode(message: types.Message):
    mode = message.text.replace(" режим", "")
    user_modes[message.from_user.id] = mode
    await message.answer(f"✅ Режим изменён на: {mode}", reply_markup=ReplyKeyboardRemove())


# 🔹 Команда /info
@dp.message(Command("info"))
async def info_cmd(message: types.Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "Обычный")
    questions = QUESTIONS[mode]

    user_states[user_id] = {"mode": mode, "q_index": 0, "answers": []}

    await message.answer(f"Ты выбрал режим: {mode}\nНачнём вопросы!")
    await message.answer(questions[0])


# 🔹 Обработка ответов
@dp.message()
async def handle_answer(message: types.Message):
    user_id = message.from_user.id

    # Если пользователь не в режиме опроса — игнорируем
    if user_id not in user_states:
        return

    state = user_states[user_id]
    mode = state["mode"]
    questions = QUESTIONS[mode]

    # Сохраняем ответ
    state["answers"].append(message.text)
    state["q_index"] += 1

    # Если есть ещё вопросы
    if state["q_index"] < len(questions):
        next_q = questions[state["q_index"]]
        await message.answer(next_q)
    else:
        # Завершение опроса
        username = message.from_user.username or message.from_user.full_name
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        answers_text = [f"{q} — {a}" for q, a in zip(questions, state["answers"])]

        # Формируем текст файла
        file_content = f"Ответы пользователя @{username} ({timestamp})\n\n" + "\n".join(answers_text)

        # Сохраняем во временный файл
        filename = f"answers_{user_id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(file_content)

        # Отправляем файл пользователю
        await message.answer("Спасибо за ответы! ❤️ Вот твой файл:")
        await message.answer_document(types.FSInputFile(filename))

        # Удаляем временный файл и состояние
        os.remove(filename)
        del user_states[user_id]


# 🔹 Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
