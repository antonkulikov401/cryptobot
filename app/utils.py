from pathlib import Path
import os
import matplotlib.pyplot as plt  # sudo apt-get install python3-tk
import speech_recognition as sr  # pip3 install SpeechRecognition
from app.globals import dicts, fiat


def load_dicts():
    global dicts
    path = Path('./dicts')
    for dict_path in path.iterdir():
        with open(str(dict_path), 'r', encoding='utf-8') as dict_file:
            dict_content = dict_file.read().splitlines()
            dict_lang = dict_content[0]
            dict_content.pop(0)
            dict = {x.split(':')[0]: '\n'.join(x.split(':')[1].split('\\n'))
                    for x in dict_content}
            dicts[dict_lang] = dict


def t(msg, lang):
    global dicts
    try:
        return dicts[lang][msg]
    except BaseException:
        return '?'


def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio)


def create_graph(xdata, ydata, path, coin_name, lang, curr):
    plt.clf()
    plt.figure(figsize=(11, 7.5))
    plt.xticks(rotation=45)
    plt.grid(linestyle='-.')
    plt.xlabel(t('17', lang), fontsize=18)
    plt.ylabel(t('18', lang) + ', ' + fiat[curr], fontsize=18)
    plt.title(coin_name + '-' + t('19', lang), fontsize=24)
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.plot(xdata, ydata, linewidth=3)
    plt.savefig(path)


class UnknownCoinError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
