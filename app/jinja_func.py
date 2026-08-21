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

def pick_first(string, seperator='', lang='zh'):
    a = string.split(seperator)
    if len(a) > 1:
        if lang == 'zh':
            other = '、'.join(a[1:])
            return f'{a[0]}（{other}）'
    elif len(a) == 1:
        return a[0]


# rank connectors and qualifiers that stay upright inside an otherwise
# italicized scientific name (botanical convention: the name parts are
# italic, the abbreviation joining them is not)
UPRIGHT_NAME_PARTS = {
    'var.', 'subvar.', 'subsp.', 'ssp.', 'f.', 'fo.', 'forma', 'subf.',
    'nothovar.', 'nothosubsp.', 'sect.', 'subsect.', 'ser.', 'cv.',
    'sp.', 'spp.', 'aff.', 'cf.', 'x', '×',
}


def italicize_name(name):
    """Wrap a scientific name in <i>, keeping rank connectors upright.

    "Camphora officinarum var. nominale" becomes
    "<i>Camphora officinarum</i> var. <i>nominale</i>".
    """
    if not name:
        return ''

    out = []
    italic = []

    def flush():
        if italic:
            out.append(f"<i>{' '.join(italic)}</i>")
            italic.clear()

    for word in name.split():
        if word.lower() in UPRIGHT_NAME_PARTS:
            flush()
            out.append(word)
        else:
            italic.append(word)
    flush()

    return ' '.join(out)
