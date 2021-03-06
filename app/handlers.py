import difflib
import telebot
import os
import subprocess  # sudo apt-get install ffmpeg
import urllib.request as req
from pathlib import Path
from datetime import date, timedelta
from contextlib import contextmanager
from speech_recognition import RequestError, UnknownValueError
from app import bot, cg, coins, dicts, fiat, token
import app.db_utils as db
from app.utils import t, UnknownCoinError, transcribe_audio, create_graph


@bot.message_handler(commands=['start'])
def handle_start(message):
    lang = db.get_lang(str(message.chat.id))
    bot.send_message(message.chat.id, t('2', lang))
    bot.send_sticker(message.chat.id, 'CAADAgADhAYAAmMr4gmSKCx3G-t1mAI')
    db.add_user(message.chat.id)
    select_lang(message.chat.id)


@bot.message_handler(commands=['help'])
def handle_help(message):
    lang = db.get_lang(message.chat.id)
    bot.send_message(message.chat.id, t('4', lang), parse_mode='Markdown')


@bot.message_handler(commands=['lang'])
def handle_change_lang(message):
    select_lang(message.chat.id)


@bot.message_handler(commands=['curr'])
def handle_change_currency(message):
    select_currency(message.chat.id)


@bot.message_handler(content_types=['text'], regexp='^[0-9a-zA-Z- ]+$')
def handle_text_command(message):
    command = message.text.lower().split()
    if len(command) == 1:
        get_coin_info(message.chat.id, command[0])
    elif (len(command) == 2 and len(difflib.get_close_matches(command[0],
          ['history'], 1, 0.8)) != 0):
        analyze_coin(message.chat.id, message.message_id, command[1])
    elif len(command) == 3 and command[1] == 'to':
        get_coin_rate(message.chat.id, command[0], command[2])
    else:
        handle_unknown_command(message)


@bot.message_handler(content_types=['text'])
def handle_unknown_command(message):
    lang = db.get_lang(message.chat.id)
    bot.send_message(message.chat.id, t('12', lang))


@bot.message_handler(content_types=['voice'])
def handle_audio_command(message):
    try:
        info = bot.get_file(message.voice.file_id)
        url = 'https://api.telegram.org/file/bot{0}/{1}'.format(token,
                                                                info.file_path)
        opener = req.build_opener(req.ProxyHandler(telebot.apihelper.proxy))
        audio_data = opener.open(url)
        Path('./temp/audio/').mkdir(parents=True, exist_ok=True)
        path = str(Path('./temp/audio/' + info.file_id))
        with open(path + '.oga', 'wb') as f:
            f.write(audio_data.read())
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-i',
                        path + '.oga', path + '.wav'])
        message.text = transcribe_audio(path + '.wav')
        bot.send_message(message.chat.id, message.text)
        handle_text_command(message)
    except UnknownValueError:
        lang = db.get_lang(message.chat.id)
        bot.send_message(message.chat.id, t('15', lang))
    except RequestError:
        lang = db.get_lang(message.chat.id)
        bot.send_message(message.chat.id, t('16', lang))
    except BaseException:
        lang = db.get_lang(message.chat.id)
        bot.send_message(message.chat.id, t('14', lang))
    finally:
        os.remove(path + '.oga')
        os.remove(path + '.wav')


@contextmanager
def get_coin_name(cid, raw_name):
    try:
        if raw_name in coins.keys():
            yield raw_name
        else:
            match = difflib.get_close_matches(raw_name, coins.keys(), 1, 0.75)
            if len(match) > 0:
                lang = db.get_lang(cid)
                bot.send_message(cid, t('13', lang) + ': _' + match[0] + '_',
                                 parse_mode='Markdown')
                yield match[0]
            else:
                yield None
    except UnknownCoinError as e:
        lang = db.get_lang(cid)
        bot.send_message(cid, t('1', lang) + ': ' + e.msg)
        bot.send_sticker(cid, 'CAADAgADWwADsiFfFVNQKDUCqm9IAg')
    except Exception:
        lang = db.get_lang(cid)
        bot.send_message(cid, t('14', lang))


def get_coin_info(cid, coin_name):
    lang = db.get_lang(cid)
    curr = db.get_currency(cid)
    with get_coin_name(cid, coin_name) as coin:
        if coin is None:
            raise UnknownCoinError(coin_name)
        coin = coins[coin]
        info = cg.get_price(ids=coin, vs_currencies=curr,
                            include_market_cap='true',
                            include_24hr_vol='true',
                            include_24hr_change='true')
        msg = ('*' + coin + '*\n' + t('6', lang) + ': ' +
               str(info[coin][curr]) + fiat[curr] + '\n' + t('7', lang) +
               ': ' + str(info[coin][curr + '_market_cap']) + fiat[curr] +
               '\n' + t('8', lang) + ': ' +
               str(info[coin][curr + '_24h_vol']) + fiat[curr] + '\n'
               + t('9', lang) + ': ' +
               str(info[coin][curr + '_24h_change']) + '%')
        bot.send_message(cid, msg, parse_mode='Markdown')


def get_coin_rate(cid, coin_name_from, coin_name_to):
    lang = db.get_lang(cid)
    curr = db.get_currency(cid)
    with get_coin_name(cid, coin_name_from) as coin_from:
        with get_coin_name(cid, coin_name_to) as coin_to:
            if coin_from is None or coin_to is None:
                raise UnknownCoinError(coin_name_from if coin_from is None
                                       else coin_name_to)
            coin_from = coins[coin_from]
            coin_to = coins[coin_to]
            price_from = cg.get_price(ids=coin_from, vs_currencies='usd')
            price_to = cg.get_price(ids=coin_to, vs_currencies='usd')
            rate = price_from[coin_from]['usd'] / price_to[coin_to]['usd']
            bot.send_message(cid, '1 ' + coin_from + u' \u2248' +
                             ' {0:.10f} '.format(rate) + coin_to)


def analyze_coin(cid, mid, coin_name):
    lang = db.get_lang(cid)
    curr = db.get_currency(cid)
    with get_coin_name(cid, coin_name) as coin:
        if coin is None:
            raise UnknownCoinError(coin_name)
        coin = coins[coin]
        xdate = [(date.today() - timedelta(days=x)).strftime('%d-%m-%Y')
                 for x in range(10, 0, -1)]
        yprice = [cg.get_coin_history_by_id(id=coin, date=d,
                  string='false')['market_data']['current_price'][curr]
                  for d in xdate]
        bot.send_chat_action(cid, 'upload_photo')
        Path('./temp/image/').mkdir(parents=True, exist_ok=True)
        path = str(Path('./temp/image/' + str(cid) + str(mid) + '.png'))
        create_graph(xdate, yprice, path, coin, lang, curr)
        with open(path, 'rb') as plot:
            bot.send_photo(cid, plot)
        os.remove(path)


def select_lang(cid):
    lang = db.get_lang(cid)
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_eng = telebot.types.InlineKeyboardButton(text='\U0001F1F7\U0001F1FA',
                                                 callback_data='rus')
    key_rus = telebot.types.InlineKeyboardButton(text='\U0001F1FA\U0001F1F8',
                                                 callback_data='eng')
    keyboard.add(key_eng, key_rus)
    bot.send_message(cid, t('3', lang) + ':', reply_markup=keyboard)


def select_currency(cid):
    lang = db.get_lang(cid)
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_usd = telebot.types.InlineKeyboardButton(text=u'\u0024',
                                                 callback_data='usd')
    key_eur = telebot.types.InlineKeyboardButton(text=u'\u20AC',
                                                 callback_data='eur')
    key_rub = telebot.types.InlineKeyboardButton(text=u'\u20BD',
                                                 callback_data='rub')
    keyboard.add(key_usd, key_eur, key_rub)
    bot.send_message(cid, t('10', lang) + ':', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    cid = call.message.chat.id
    if call.data in dicts.keys():
        db.change_lang(cid, call.data)
        bot.edit_message_text(chat_id=cid, message_id=call.message.message_id,
                              text=t('5', call.data))
    if call.data in fiat.keys():
        db.change_currency(cid, call.data)
        lang = db.get_lang(cid)
        bot.edit_message_text(chat_id=cid, message_id=call.message.message_id,
                              text=t('11', lang))
