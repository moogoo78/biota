from datetime import datetime
from flask import (
    request,
    g,
)

def str_to_date(string, format='%Y-%m-%d'):
    return datetime.strptime(string, format)

def get_locale():
    locale = 'zh'
    if request.path[0:3] == '/en':
        locale = 'en'
    return getattr(g, 'LOCALE', locale)

def get_lang_path(lang):
    by = None
    if request.path[0:3] == '/en':
        by = 'prefix'
    elif request.path[0:3] == '/zh':
        by = 'prefix'
    else:
        locale = request.accept_languages.best_match(['zh', 'en'])
        by = 'accept-languages'
    if by == 'prefix':
        return f'/{lang}{request.path[3:]}'
    elif by == 'accept-languages':
        return f'/{lang}{request.path}'
