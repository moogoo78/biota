import os
import re
import json
#import logging
from logging.config import dictConfig

from flask import (
    g,
    Flask,
    jsonify,
    render_template,
    redirect,
    request,
    flash,
    url_for,
    abort,
    Response,
)

#from app.database import session

def apply_blueprints(app):
    from app.blueprints.main import bp as main_bp;
    app.register_blueprint(main_bp, url_prefix='/')

def create_app():
    app = Flask(__name__)
    if os.getenv('WEB_ENV') == 'dev':
        app.config.from_object('app.config.DevelopmentConfig')
    elif os.getenv('WEB_ENV') == 'prod':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.Config')

    app.url_map.strict_slashes = False
    #print(app.config, flush=True)
    return app

flask_app = create_app()
apply_blueprints(flask_app)

# flask extensions
#babel = Babel(flask_app, locale_selector=get_locale)
#flask_app.jinja_env.globals['get_locale'] = get_locale
#flask_app.jinja_env.globals['get_lang_path'] = get_lang_path
#flask_app.jinja_env.globals['str_to_date'] = str_to_date

@flask_app.route('/')
def index():
    return render_template('index.html')

@flask_app.route('/robots.txt')
def robots_txt():
    robots_content = """
User-agent: *
Disallow: /
"""
    robots_content = robots_content.lstrip()
    return Response(robots_content, mimetype='text/plain')

@flask_app.route('/url_maps')
def debug_url_maps():
    rules = []
    for rule in flask_app.url_map.iter_rules():
        rules.append([str(rule), str(rule.methods), rule.endpoint])
    return jsonify(rules)

# @flask_app.teardown_appcontext
# def shutdown_session(exception=None):
#     # SQLAlchemy won`t close connection, will occupy pool
#     session.remove()

# with flask_app.app_context():
#    # needed to make CLI commands work
#     from .commands import *
