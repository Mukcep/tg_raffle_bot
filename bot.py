from typing import Dict, List
import models
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup

#
API_TOKEN = 'TOKEN' 

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

raffle_cb = CallbackData('raffle', 'action')

raffles = {}
# 

def get_raffle_by_chat_id(chat_id) -> models.Raffle:
    if chat_id in raffles:
        return raffles[chat_id]
    else:
        return None

#
# ----------------
@dp.message_handler(commands=['raffle'])
async def process_start(message: types.Message):
    username = message.from_user.username
    # logging.info(len(message.get_args()))
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    chat_id = message.chat.id
    # logging.info(raffles)

    prize = "Не указано"
    winners_count = 1
    args = message.get_args()
    if len(args) > 0:
        args = args.rsplit(' ', maxsplit=1)
        if args[0]:
            prize = args[0]
        if len(args) > 1 and args[1].isnumeric():
            winners_count = args[1]

    if get_raffle_by_chat_id(chat_id):
        await message.answer("В этой группе уже запущен розыгрыш!")
    else:
        raffle = models.Raffle(chat_id, 'Test', prize, models.Member(user_id, user_full_name), winners_count)
        raffles[chat_id] = raffle

        markup = InlineKeyboardMarkup()
        add_member_btn = InlineKeyboardButton("Учавствую!", callback_data=raffle_cb.new(action='addMember'))
        complete_raffle_btn = InlineKeyboardButton("Завершить", callback_data=raffle_cb.new(action='completeRaffle'))
        markup.insert(add_member_btn)
        markup.insert(complete_raffle_btn)

        message_text = raffle.generateMessage()
        await message.answer(message_text, reply_markup=markup, parse_mode='Markdown')

# ----------------
@dp.message_handler(commands=['raffle_history'])
async def process_start(message: types.Message):
    chat_id = message.chat.id
    history : List[models.RaffleHistory] = models.RaffleHistory.select().where(models.RaffleHistory.chat_id == chat_id).limit(5).order_by(models.RaffleHistory.created.desc())
    
    if len(history) == 0:
        await message.answer("В этом чате не было розыгрышей!")
        return

    text = f"Последние {len(history)} розыгрышей в этом чате:\n"
    for h in history:
        text += f"{h.generateText()}\n\n"
    await message.answer(text, parse_mode='Markdown')


# ----------------------- Инлайн Хендлеры
@dp.callback_query_handler(raffle_cb.filter(action=['addMember']))
async def add_member_to_raffle(query: types.CallbackQuery):
    chat_id = query.message.chat.id
    raffle = get_raffle_by_chat_id(chat_id)
    if not raffle:
        await query.answer("Розыгрыш уже завершен")
        return

    member = models.Member(query.from_user.id, query.from_user.full_name)
    if not raffle.add_member(member):
        await query.answer("Ты уже учавствуешь!")
        return


    message_text = raffle.generateMessage()
    markup = query.message.reply_markup
    await query.answer()
    await query.message.edit_text(message_text, parse_mode='Markdown', reply_markup=markup)


@dp.callback_query_handler(raffle_cb.filter(action=['completeRaffle']))
async def complete_raffle(query: types.CallbackQuery):
    chat_id = query.message.chat.id
    raffle = get_raffle_by_chat_id(chat_id)
    if not raffle:
        await query.answer("Розыгрыш уже завершен")
        return
        
    member = models.Member(query.from_user.id, query.from_user.full_name)
    if raffle.creator.user_id != member.user_id:
        await query.answer("Только автор может закончить розыгрыш!")
        return
    if len(raffle.members) == 0:
        raffle.raffle()
        raffles.pop(chat_id)
        await query.answer()
        await query.message.edit_text("Штош, никто не пришел, свернули лавку...", parse_mode='Markdown')
        return

    raffle.raffle()
    raffle.saveHistory()
    message_text = raffle.generateMessage()
    # markup = query.message.reply_markup
    raffles.pop(chat_id)
    await query.answer()
    await query.message.edit_text(message_text, parse_mode='Markdown')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
