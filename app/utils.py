from pathlib import Path
import os
import speech_recognition as sr  # pip3 install SpeechRecognition
from app.globals import dicts


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


class UnknownCoinError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg
