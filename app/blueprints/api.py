from flask import (
    Blueprint,
    request,
    Response,
    abort,
    jsonify,
    redirect,
    url_for,
    current_app,
)
from app.database import session
from app.models import (
    WebhookEvent,
    Notification,
    User,
)

bp = Blueprint('api', __name__)

@bp.route('/hooks', methods=['POST'])
def activate_namespace():
    if request.method == 'POST':
        data = request.json
        if event := data.get('event'):
            w = WebhookEvent(name=event, data=data['data'])
            session.add(w)
            session.commit()

            if email := data['data'].get('email'):
                if user := User.query.filter(User.email==email).scalar():
                    n = Notification(event_id=w.id, user_id=user.id)
                    session.add(n)
                    session.commit()
                else:
                    return jsonify({'message': 'no user'})
            else:
                return jsonify({'message': 'invalid data'})

    return jsonify({'message': 'ok'})
