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
from werkzeug.security import (
    check_password_hash,
)
from flask_login import (
    LoginManager,
    login_user,
)
import pymysql.cursors
#from app.database import session


def apply_blueprints(app):
    from app.blueprints.main import bp as main_bp;
    from app.blueprints.api import bp as api_bp;
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(api_bp, url_prefix='/api/v1')

def apply_extensions(app):
    # login
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    @login_manager.unauthorized_handler
    def unauthorized():
        # do stuff
        return redirect(url_for('admin.login') + '?next=' + request.path)

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

@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form.get('email', '')
        passwd = request.form.get('password', '')
        if u := User.query.filter(User.email==email).first():
            if check_password_hash(u.passwd, passwd):
                login_user(u)
                return redirect(url_for('index'))

    return abort(404)


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

@flask_app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

with flask_app.app_context():
    # needed to make CLI commands work
    from .commands import *
