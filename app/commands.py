import subprocess
from app.application import flask_app
import click

from werkzeug.security import (
    generate_password_hash,
 )

from app.database import session
from app.models import User


@flask_app.cli.command('makemigrations')
@click.argument('message')
def makemigrations(message):
    cmd_list = ['alembic', 'revision', '--autogenerate', '-m', message]
    subprocess.call(cmd_list)


@flask_app.cli.command('migrate')
def migrate():
    cmd_list = ['alembic', 'upgrade', 'head']
    subprocess.call(cmd_list)


@flask_app.cli.command('createuser')
@click.argument('username')
@click.argument('email')
@click.argument('passwd')
def createuser(username, email, passwd):
    hashed_password = generate_password_hash(passwd)
    user = User(username=username, email=email, passwd=hashed_password)
    session.add(user)
    session.commit()
    print(f'create user: {username}, {hashed_password}',flush=True)
