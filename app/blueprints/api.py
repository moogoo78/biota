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
from flask.views import MethodView

import requests
from flask_login import(
    current_user,
)

from app.database import session
from app.models import (
    WebhookEvent,
    Notification,
    User,
    Collection,
    Publication,
    PublicationLiterature,
    Item,
    ItemSynonym,
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

                    taicol_api = current_app.config['TAICOL_API']
                    resp = requests.get(f'{taicol_api}/user/namespace?email={email}')
                    if resp.ok:
                        resp_json = resp.json()
                        available_namespaces = resp_json.get('namespaces', [])
                        namespace_id = data['data']['namespace_id']
                        if namespace_id in available_namespaces:
                            try:
                                if c := Collection.query.filter(Collection.source_id==namespace_id, Collection.user_id==user.id).scalar():
                                    current_app.logger.info(f'collection [{c.id}] already exist')
                                else:
                                    c = Collection(name=data['data'].get('name', ''), source_id=namespace_id, user_id=user.id)
                                    session.add(c)

                                n = Notification(event_id=w.id, user_id=user.id, content=f'namespace [{namespace_id}] published')
                                session.add(n)
                                session.commit()
                            except Exception as err_msg:
                                current_app.logger.error(f'insert db error: {err_msg}');
                                return jsonify({'message': 'insert db error'})
                        else:
                            return jsonify({'message': 'namespace not available'})
                    else:
                        return jsonify({'message': 'email namespace not available'})
                else:
                    return jsonify({'message': 'no user'})
            else:
                return jsonify({'message': 'invalid data'})

    return jsonify({'message': 'ok'})

@bp.route('/publications', methods=['POST'])
def post_publication():
    if request.method == 'POST':
        data = request.json
        if cid := data.get('collectionid'):
            if collection := session.get(Collection, int(cid)):
                pub = Publication(title=collection.name, author=current_user.username)
                session.add(pub)
                session.commit()
                collection.publication_id = pub.id
                session.commit()

                # update collection
                url = f"{current_app.config['TAICOL_API']}/biota?namespace_id={collection.source_id}&token={current_app.config['TAICOL_TOKEN']}"
                resp = requests.get(url)
                data = resp.json()

                collection.source_name = data['title']
                collection.source_data = data
                for i in data['literatures']:
                    pl = PublicationLiterature(publication_id=pub.id, source_id=i['reference_id'], name=i['citation'])
                    session.add(pl)

                session.commit()

                for i in data['group']:
                    name = i['name'].replace('<i>', '').replace('</i>', '')
                    item = Item(collection_id=cid, description=i['description'], distribution=i['distribution'], note=i['note'], user_id=current_user.id, scientific_name=name, source_data=i, common_names='|'.join(i['common_names']))
                    session.add(item)
                    session.commit()

                    for syn in i['synonyms']:
                        item_syn = ItemSynonym(item_id=item.id, name=syn['usage_references_text'], ref=f"name_id:{i['name_id']}")
                        session.add(item_syn)

                session.commit()

                return jsonify({
                    'message': 'ok',
                    'data': data,
                })

    return jsonify({
        'message': 'error',
    })

@bp.route('/publications/<int:publication_id>', methods=['PATCH'])
def put_publication(publication_id):
    if request.method == 'PUT':
        data = request.json
        print(data)
        # TODO
# @bp.route('/items/<int:item_id>/specimens', methods=['POST'])
# def post_item_specimens(item_id):
#     if request.method == 'POST':
#         data = request.json
#         if item := session.get(Item, item_id):
#             sp = ItemSpecimen(item_id=item_id, source_data=data['source_data'], source_id=, text=)
#         print(data)
#         #session.add(sp)
#         return jsonify({
#             'message': 'ok',
#         })
