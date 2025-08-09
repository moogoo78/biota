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
import requests

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

                    resp = requests.get(f'https://staging.taicol.tw/api/user/namespace?email={email}')
g                    if resp.ok:
                        resp_json = resp.json()
                        available_namespaces = resp_json.get('namespaces', [])
                        namespace_id = data['data']['namespace_id']
                        print(namespace_id, data)
                        if namespace_id in available_namespaces:
                            n = Notification(event_id=w.id, user_id=user.id, content=f'namespace [{namespace_id}] published')
                            session.add(n)
                            session.commit()
                        else:
                            return jsonify({'message': 'namespace not available'})
                    else:
                        return jsonify({'message': 'email namespace not available'})
                else:
                    return jsonify({'message': 'no user'})
            else:
                return jsonify({'message': 'invalid data'})

    return jsonify({'message': 'ok'})
