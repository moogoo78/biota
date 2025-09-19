import json
import re
from datetime import datetime

from flask import (
    Blueprint,
    request,
    Response,
    abort,
    jsonify,
    redirect,
    url_for,
    current_app,
    render_template,
    send_file,
    redirect,
    flash,
)
from flask_login import (
    login_required,
    logout_user,
    current_user,
)
import requests
from bs4 import BeautifulSoup

from app.models import (
    User,
    Collection,
    Notification,
    Publication,
    Item,
    ItemSpecimen,
    ItemSynonym,
    ItemImage,
    PublicationLiterature,
)
from app.database import session
from app.helpers import (
    put_publication_by_taicol_namespace,
)

bp = Blueprint('publication', __name__)


@bp.route('/')
@login_required
def list_view():
    if namespace_id := request.args.get('namespace_id'):
        res = put_publication_by_taicol_namespace(current_user, namespace_id)

        if res['is_success'] is True:
            return redirect(url_for('publication.list_view'))
        else:
            return res['message']
    else:
        collections = Collection.query.filter(Collection.user_id==current_user.id).all()
        publications = [x.publication for x in collections]
        return render_template('publication_list.html', publications=publications)
    return abort(404)

@bp.route('/<int:item_id>')
@login_required
def detail_view(item_id):
    publication = session.get(Publication, item_id)
    API_URL=current_app.config['API_URL']
    item_data = []
    for i in publication.collections[0].items:
        # 整理給前端
        specimens = []
        for x in i.specimens:
            data = x.source_data
            data['_id'] = x.id
            data['_text'] = x.text
            specimens.append(data)

        item_data.append({
            'item_id': i.id,
            'name': i.scientific_name,
            'name_id': i.source_data['name_id'],
            'rank_id': i.source_data['rank_id'],
            'specimens': specimens
        })
    return render_template('publication_detail.html', publication=publication, API_URL=API_URL, item_data_json=json.dumps(item_data))


@bp.route('/<int:item_id>/delete')
@login_required
def delete_item(item_id):
    publication = session.get(Publication, item_id)
    for c in publication.collections:
        for i in c.items:
            for j in i.synonyms:
                session.delete(j)
            for j in i.specimens:
                session.delete(j)
            session.delete(i)
        #session.delete(c) keep collection
        c.publication_id = None

    for i in publication.literatures:
        session.delete(i)

    session.delete(publication)
    session.commit()
    return redirect(url_for('publication.list_view'))

@bp.route('/<int:item_id>/patch', methods=['POST'])
@login_required
def patch_item(item_id):
    publication = session.get(Publication, item_id)
    for k, v in request.form.items():
        a = getattr(publication, k)
        if a != v:
            setattr(publication, k, v)

    session.commit()

    flash('patch ok')
    return redirect(url_for('publication.detail_view', item_id=item_id)+'#meta')


@bp.route('/<int:item_id>/literatures/post', methods=['POST'])
@login_required
def create_publication_literature(item_id):
    if payload := request.json:
        source_id = payload.get('reference_id', '')
        name = payload.get('citation', '')
        pl = PublicationLiterature(publication_id=item_id, source_id=source_id, name=name)
        session.add(pl)
        session.commit()
        flash('新增文獻')
        return jsonify({
            'status': 'success'
        })
    return jsonify({
        'status': 'fail'
    })

@bp.route('/<int:publication_id>/literatures/<int:item_id>/delete')
@login_required
def delete_publication_literature(publication_id, item_id):
    if pl := session.get(PublicationLiterature, item_id):
        session.delete(pl)
        session.commit()
        flash('刪除文獻')
        return redirect(url_for('publication.detail_view', item_id=publication_id)+'#literatures')

    return abort(404)
