import argostranslate.package as pkg
import argostranslate.translate as tr
import re


ARGOS = None


def is_ru(text):
    ru_re = re.compile('[а-яА-Я]')
    return bool(ru_re.search(text))


def init_translator():
    pkg.update_package_index()
    pack = next(
        (p for p in pkg.get_available_packages()
         if p.from_code == "ru" and p.to_code == "en"),
        None,
    )
    if pack:
        path = pack.download()
        pkg.install_from_path(path)

    langs = tr.get_installed_languages()
    ru = next((l for l in langs if l.code == "ru"), None)
    en = next((l for l in langs if l.code == "en"), None)
    return ru.get_translation(en) if ru and en else None


def translate_ru_en(text):
    global ARGOS
    if ARGOS is None:
        ARGOS = init_translator()
        if ARGOS is None:
            return text
    return ARGOS.translate(text)
