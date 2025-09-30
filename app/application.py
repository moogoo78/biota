import os
import re
import json
import logging
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler

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
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
)
from flask_babel import (
    Babel,
    gettext,
    #ngettext,
)
from app.jinja_func import *


logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('[CONSOLE] %(levelname)s: %(message)s'))

#file_handler = RotatingFileHandler('/var/log/biota/flask.log', maxBytes=5 * 1024 * 1024, backupCount=10)
#file_handler.setLevel(logging.DEBUG)
#file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))

logger.addHandler(console_handler)
#logger.addHandler(file_handler)


def apply_blueprints(app):
    from app.blueprints.main import bp as main_bp
    from app.blueprints.publication import bp as publication_bp
    from app.blueprints.api import bp as api_bp
    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(publication_bp, url_prefix='/publications')

def apply_extensions(app):
    # babel
    babel = Babel(app, locale_selector=get_locale)
    app.jinja_env.globals['get_locale'] = get_locale
    app.jinja_env.globals['get_lang_path'] = get_lang_path
    app.jinja_env.globals['str_to_date'] = str_to_date
    app.jinja_env.globals['pick_first'] = pick_first

    # login
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for('auth.login') + '?next=' + request.url)

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

    apply_extensions(app)

    return app

flask_app = create_app()
apply_blueprints(flask_app)

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

@flask_app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()

#@flask_app.teardown_appcontext
#def close_db_connection(exception):
#    """Closes the database again at the end of the request."""
#    db = g.pop('db', None)
#    if db is not None:
#        db.close()

with flask_app.app_context():
    # needed to make CLI commands work
    from .commands import *
