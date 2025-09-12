import secrets
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    request,
    url_for,
    render_template,
    redirect,
    current_app,
    jsonify,
    abort,
    flash,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
 )
from flask_login import (
    login_required,
    logout_user,
    login_user,
    current_user,
)

from app.database import session
from app.models import (
    User,
)
from app.helpers import (
    send_email,
)
bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('signin.html')
    elif request.method == 'POST':
        email = request.form.get('email', '')
        passwd = request.form.get('password', '')

        if u := User.query.filter(User.email==email, User.isactivated==True).first():
            if check_password_hash(u.passwd, passwd):
                login_user(u)
                if next_url := request.args.get('next'):
                    return redirect(next_url)
                elif url := u.next_url:
                    u.next_url = ''
                    session.commit()
                    return redirect(url)

                return redirect(url_for('index'))
        else:
            flash('login error')
            url = url_for('auth.login')
            if next_url := request.args.get('next'):
                url = f'{url}?next={next_url}'

            return redirect(url)

    return abort(401)

@bp.route('/logout')
def logout():
    logout_user()

    response = jsonify({"msg": "logout successful"})
    #unset_jwt_cookies(response)
    #return response
    return redirect(url_for('auth.login'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        email = request.form.get('email')
        passwd1 = request.form.get('password')
        passwd2 = request.form.get('confirm-password')
        if email and passwd1 and passwd2 and passwd1 == passwd2:
            if exist := User.query.filter(User.email==email).scalar():
                flash('此email已存在')
                return redirect(url_for('auth.signup'))

            token = secrets.token_urlsafe(32)
            passwd = generate_password_hash(passwd1)
            activate_url = url_for('auth.activate_token', token=token)
            base_url = current_app.config['API_URL']
            activate_url = f'{base_url}{activate_url}'
            user = User(email=email, passwd=passwd, username=email, activation_token=token)
            if next_url := request.form.get('next'):
                user.next_url = next_url
            session.add(user)
            session.commit()
            body = f"""
    Welcome! Please Activate Your Account

    Hello!

    Thank you for registering with us. To complete your registration and activate your account, please visit:

    {activate_url}

    Important: This activation link will expire in 24 hours for security reasons.

    If you didn't create this account, please ignore this email.

    This is an automated message, please do not reply to this email.
    """
            resp = send_email(email, '[Biota Taiwanica] Please Activate Your Account', body)
            #return redirect(url_for('login'))
            return 'email認證信已送出'
        else:
            flash('signup error')
            return redirect(url_for('auth.signup'))

@bp.route('/activate/<token>')
def activate_token(token):
    message = ''
    status = ''
    if user := User.query.filter(User.activation_token==token).scalar():
        if user.is_activated:
            login_url = url_for('auth.login')
            message = f'Account successfully activated! You can now <a href="{login_url}">login</a>.'
            status = "success"
        else:
            # Check if token is expired (24 hours)
            if datetime.now() - user.created_at > timedelta(hours=24):
                message = "Activation link has expired. Please request a new one."
                status = "error"
            else:
                user.is_activated = True
                user.activated_at = datetime.now()
                session.commit()
                message = f'Account successfully activated! You can now <a href="{url_for('auth.login')}">login</a>.'
                status = "success"
    else:
        message = "Invalid activation link."
        status = "error"

    return f'{status}: {message}'
