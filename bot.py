from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import random
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

BOT_TOKEN = "7821396988:AAFl8ysdBft9ILdntusKaXwfqmWM9eqh7BY"  # ← замени на свой токен
PIXABAY_API_KEY = "49851188-401fccb1ab9bd9b40659faf0a"

# 🐾 Фразы для мема
phrases = [
    "Сегодня я не ленюсь. Я заряжаюсь энергией через лежание.",
    "Иногда лучший план — это одеяло и тишина.",
    "Смысл жизни? Пожалуйста, перезагрузите меня позже.",
    "Ты справишься! Ну… или хотя бы красиво проиграешь.",
    "Если не можешь изменить ситуацию — измяукай её!",
    "Счастье — это когда утро, а вставать не надо.",
    "Работай как будто никто не смотрит. Потому что никому не интересно.",
    "Я не прокрастинирую. Я стратегически отдыхаю.",
    "Хорошее настроение — это когда ты кот.",
    "Главное — не сдаваться! Но и не перенапрягаться.",
    "Мир не идеален. Зато есть печеньки."
]

# 🔤 Разбиваем текст по строкам
def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = line + word + " "
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            line = test_line
        else:
            lines.append(line.strip())
            line = word + " "
    if line:
        lines.append(line.strip())
    return lines

# 🔠 Подбираем лучший размер шрифта
def get_best_font_size(text, max_width, draw, font_path="Arial.ttf", max_font_size=60, min_font_size=20):
    for size in range(max_font_size, min_font_size - 1, -2):
        try:
            font = ImageFont.truetype(font_path, size=size)
        except:
            font = ImageFont.load_default()
        lines = wrap_text(text, font, max_width, draw)
        fits = True
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            width = bbox[2] - bbox[0]
            if width > max_width:
                fits = False
                break
        if fits:
            return font
    return font

# 🐱 Генерация мема с котом
def generate_cat_meme():
    cat_folder = "cats"
    images = [img for img in os.listdir(cat_folder) if img.endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        return None

    print(f"📸 Найдено изображений: {len(images)}")
    chosen = random.choice(images)
    print(f"🎯 Выбранное изображение: {chosen}")

    cat_img = Image.open(os.path.join(cat_folder, chosen)).convert("RGB")
    draw = ImageDraw.Draw(cat_img)
    text = random.choice(phrases)
    max_width = cat_img.width - 40

    font = get_best_font_size(text, max_width, draw)
    lines = wrap_text(text, font, max_width, draw)

    y = 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (cat_img.width - text_width) // 2

        # Обводка: чёрный контур
        outline_range = 2
        for dx in range(-outline_range, outline_range + 1):
            for dy in range(-outline_range, outline_range + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))

        # Основной текст: белый
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += text_height + 5


    output_path = "cat_meme.jpg"
    cat_img.save(output_path)
    return output_path

def create_image_with_text_from_pixabay(text, api_key):
    url = "https://pixabay.com/api/"
    params = {
        "key": api_key,
        "q": text,
        "image_type": "photo",
        "safesearch": "true",
        "per_page": 10
    }
    response = requests.get(url, params=params)
    
    print("🔗 Запрос отправлен на:", response.url)
    print("📥 Статус ответа:", response.status_code)
    print("📄 Ответ:", response.text[:500])  # покажем первые 500 символов

    try:
        data = response.json()
        hits = data.get("hits")
        if not hits:
            print("❌ Не найдено ни одного изображения.")
            return None
    except Exception as e:
        print("❌ Ошибка при разборе JSON:", str(e))
        return None

    chosen = random.choice(hits)
    img_url = chosen["largeImageURL"]
    img_response = requests.get(img_url)
    img = Image.open(BytesIO(img_response.content)).convert("RGB")

    draw = ImageDraw.Draw(img)
    font_path = "Arial.ttf"
    try:
        font = ImageFont.truetype(font_path, size=40)
    except:
        font = ImageFont.load_default()

    max_width = img.width - 40
    lines = wrap_text(text, font, max_width, draw)

    y = img.height - (len(lines) * 50) - 40
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (img.width - text_width) // 2
        # Обводка
        outline_range = 2
        for ox in range(-outline_range, outline_range + 1):
            for oy in range(-outline_range, outline_range + 1):
                draw.text((x + ox, y + oy), line, font=font, fill="black")
        draw.text((x, y), line, font=font, fill="white")
        y += 50

    output_path = "captioned_image.jpg"
    img.save(output_path)
    return output_path


# ▶️ Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🐾 Сторис с текстом", "🎨 Картинка с подписью"],
        ["😂 Мем", "🎲 Рандом-вдохновение"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Я Clicksy 🐾\nВыбери, что ты хочешь создать:", reply_markup=reply_markup)

# 🔘 Обработка кнопок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # 👇 Сначала проверяем, ждал ли бот подпись от пользователя
    if context.user_data.get("awaiting_caption"):
        user_caption = text
        context.user_data["awaiting_caption"] = False
        await update.message.reply_text("Ищу подходящую картинку...")

        image_path = create_image_with_text_from_pixabay(user_caption, PIXABAY_API_KEY)
        if image_path:
            await update.message.reply_photo(photo=open(image_path, "rb"))
        else:
            await update.message.reply_text("Не удалось найти подходящую картинку 😿")
        return  # ✅ Выходим из функции, чтобы не обрабатывать кнопки дальше

    # 🎛 Обработка кнопок
    if text == "🐾 Сторис с текстом":
        await update.message.reply_text("Вот твоя сторис с текстом! (пока заглушка)")

    elif text == "🎨 Картинка с подписью":
        await update.message.reply_text("Напиши подпись, которую хочешь на картинке:")
        context.user_data["awaiting_caption"] = True

    elif text == "😂 Мем":
        meme_path = generate_cat_meme()
        if meme_path:
            await update.message.reply_photo(photo=open(meme_path, "rb"))
        else:
            await update.message.reply_text("Не удалось найти котика 😿")

    elif text == "🎲 Рандом-вдохновение":
        await update.message.reply_text("Окей, ловим вдохновение... (тоже заглушка)")

    else:
        await update.message.reply_text("Пока не знаю, что с этим делать. Выбери из меню 😊")

# 🚀 Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()

