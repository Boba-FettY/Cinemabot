import logging
import sqlite3
from telegram.ext import Application, MessageHandler, filters, \
    CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Update
from kinopoisk_api import KP

con = sqlite3.connect("films.db")
cursor = con.cursor()
kinopoisk = KP(token='b4f90fec-97ab-42a7-9e36-38b77b977032')
last_film = None
start_reply_keyboard = [['🔦Найти фильм'],
                        ['📼Мои фильмы'], ['🕹Помощь']]
my_films_reply_keyboard = [['💎Любимые'], ['⏱Хочу посмотреть'], ['🧰Посмотренные'], ['⬅Назад']]
my_films__markup = ReplyKeyboardMarkup(my_films_reply_keyboard, one_time_keyboard=False)
start_markup = ReplyKeyboardMarkup(start_reply_keyboard, one_time_keyboard=False)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def search_films(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == '🔦Найти фильм':
        await update.message.reply_text('Напишите название фильма, а я постараюсь найти его)')
    elif update.message.text == '📼Мои фильмы':
        await update.message.reply_text(
            "Ваши фильмы:",
            reply_markup=my_films__markup
        )
    elif update.message.text == '🕹Помощь':
        await update.message.reply_text('Я тебе что помогатор чтоле???')
    elif update.message.text == '⬅Назад':
        await update.message.reply_text('-Вы вернулись в главное меню-',
                                        reply_markup=start_markup)
    elif update.message.text in ('💎Любимые', '⏱Хочу посмотреть', '🧰Посмотренные'):
        konverter = {'💎Любимые': 'LUBIMIE', '⏱Хочу посмотреть': 'HOCH_POSMOTRET',
                     '🧰Посмотренные': 'PROSMOTRENIE'}
        tablica = f"SELECT name_film from {konverter[update.message.text]}" \
                  f" WHERE name = '{update.message.from_user.id}'"
        tablica = cursor.execute(tablica).fetchall()
        print(tablica)
        k = 1
        if tablica:
            keyboard = [
                [
                    InlineKeyboardButton("🔍Подробнее", callback_data="под"),
                    InlineKeyboardButton("❌Удалить", callback_data="дел"),
                ],
                [InlineKeyboardButton("В '🧰Посмотренные'", callback_data="сом")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            for x in tablica:
                await update.message.reply_text(f'{k}.{x[0]}, {update.message.text[0]}',
                                                reply_markup=reply_markup)
                k += 1
        else:
            await update.message.reply_text(f'Пока что здесь у ват нет фильмов')
    else:
        naidenye = kinopoisk.search(update.message.text)
        if naidenye:
            await context.bot.send_photo(
                update.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
                # Ссылка на static API, по сути, ссылка на картинку.
                # Телеграму можно передать прямо её, не скачивая предварительно карту.
                naidenye[0].poster,
                caption=f"{naidenye[0].ru_name}, {naidenye[0].year}\n"
                        f"{', '.join(naidenye[0].genres)}\n"
                        f"{', '.join(naidenye[0].countries)}", reply_markup=start_markup)
            keyboard = [
                [
                    InlineKeyboardButton("В '💎Любимые'", callback_data="1"),
                    InlineKeyboardButton("В '⏱Хочу посмотреть'", callback_data="2"),
                ],
                [InlineKeyboardButton("В '🧰Посмотренные'", callback_data="3")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # global last_film
            # last_film = f'{naidenye[0].ru_name}, {naidenye[0].year}'
            await update.message.reply_text(f"В какую группу добавить фильм {naidenye[0].ru_name}, {naidenye[0].year}?",
                                            reply_markup=reply_markup)
        else:
            await update.message.reply_text('Извините, по вашему запросу ничего не найдено🙁',
                                            reply_markup=start_markup)


async def start(update, context):
    print(update.message.chat.last_name)
    await update.message.reply_text(
        "Я Кинопоиск-бот",
        reply_markup=start_markup
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    if query.data in ('1', '2', '3'):
        imy_polzovately = query.from_user.id

        nazvanie_filma = query.message.text[30:-1]
        slovar_tablica = {'1': 'LUBIMIE', '2': 'HOCH_POSMOTRET', '3': 'PROSMOTRENIE'}
        proverka = f"SELECT * from {slovar_tablica[query.data]} WHERE name = '{imy_polzovately}'" \
                   f" AND name_film = '{nazvanie_filma}'"
        proverka = cursor.execute(proverka).fetchall()
        print(proverka)
        if not proverka:
            humus = f""" INSERT INTO {slovar_tablica[query.data]} (name, name_film) VALUES 
            ('{imy_polzovately}', '{nazvanie_filma}') """
            cursor.execute(humus)
            con.commit()
            await query.edit_message_text(text=f"***Выполнено***")
        else:
            await query.edit_message_text(text=f"***Ошибка, такой уже есть***")
    elif query.data == 'под':
        naidenye = kinopoisk.search(query.message.text[2:-3])
        if naidenye:
            await context.bot.send_photo(
                query.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
                # Ссылка на static API, по сути, ссылка на картинку.
                # Телеграму можно передать прямо её, не скачивая предварительно карту.
                naidenye[0].poster,
                caption=f"{naidenye[0].ru_name}, {naidenye[0].year}\n"
                        f"{', '.join(naidenye[0].genres)}\n"
                        f"{', '.join(naidenye[0].countries)}", reply_markup=start_markup)
            keyboard = [
                [
                    InlineKeyboardButton("В '💎Любимые'", callback_data="1"),
                    InlineKeyboardButton("В '⏱Хочу посмотреть'", callback_data="2"),
                ],
                [InlineKeyboardButton("В '🧰Посмотренные'", callback_data="3")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # global last_film
            # last_film = f'{naidenye[0].ru_name}, {naidenye[0].year}'
            await query.message.reply_text(f"В какую группу добавить фильм {naidenye[0].ru_name}, {naidenye[0].year}?",
                                           reply_markup=reply_markup)
        else:
            print(query.message.text)
            await query.message.reply_text('Извините, по вашему запросу ничего не найдено🙁',
                                           reply_markup=start_markup)
    elif query.data in ('дел', 'сом'):
        konverter = {'💎': 'LUBIMIE', '⏱': 'HOCH_POSMOTRET', '🧰': 'PROSMOTRENIE'}
        naz_f = query.message.text[2:-3]
        cursor.execute(f"DELETE FROM {konverter[query.message.text[-1]]} WHERE name_film = '{naz_f}'"
                       f" AND name = '{query.from_user.id}'")
        con.commit()
        if query.data == 'сом':
            imy_polzovately = query.from_user.id
            humus = f""" INSERT INTO PROSMOTRENIE (name, name_film) VALUES 
                        ('{imy_polzovately}', '{naz_f}') """
            cursor.execute(humus)
            con.commit()
            await query.edit_message_text(text="***Выполнено***")
        else:
            await query.edit_message_text(text="***Удалено***")


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, search_films)
    application.add_handler(text_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

    # Регистрируем обработчик в приложении.

    # Запускаем приложение.
    application.run_polling()
    con.close()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
