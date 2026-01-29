import json
import re
from datetime import datetime
from io import BytesIO
from urllib.parse import quote

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
    IdentificationKey,
    KeyEntry,
)
from app.database import session
from app.helpers import (
    put_publication_by_taicol_namespace,
    sync_collection_by_taicol_namespace,
    format_specimen_display,
    generate_docx,
    generate_pdf,
)

bp = Blueprint('publication', __name__)

@bp.route('/publication/<int:item_id>/sync')
@login_required
def sync_publication(item_id):
    if pub := session.get(Publication, item_id):
        c = pub.collections[0]
        actions = sync_collection_by_taicol_namespace(c)
        msg = f'[CREATE] {actions['created']} new name(s), [UPDATE] {actions['updated']} name(s), [DELETE] {actions['deleted']} name(s)'
        flash(msg)
    return redirect(url_for('publication.detail_view', item_id=pub.id) + '?action=fetchAll#groups')


@bp.route('/')
@login_required
def list_view():
    namespace_id = request.args.get('namespace_id')
    if namespace_id:
        res = put_publication_by_taicol_namespace(current_user, namespace_id)
        pub_id = res['data'].get('publication_id')
        if res['status'] == 'new':
            return redirect(url_for('publication.detail_view', item_id=pub_id) + '?action=fetchAll#groups')
        elif res['status'] == 'exist':
            if pub_id := res['data'].get('publication_id'):
                confirm_url = url_for('publication.sync_publication', item_id=pub_id)
                cancel_url = url_for('publication.list_view')
                return f'''
            <script>
                if (confirm('Publication already exists. Continue will overwrite the existing content. Cancel will go back to publication list.')) {{
                    window.location.href = '{confirm_url}';
                }} else {{
                    window.location.href = '{cancel_url}';
                }}
            </script>
            '''
    else:
        collections = Collection.query.filter(Collection.user_id==current_user.id, Collection.publication_id > 0).all()
        publications = [x.publication for x in collections]
        return render_template('publication_list.html', publications=publications)


@bp.route('/<int:item_id>/delete')
@login_required
def delete_publication(item_id):
    if pub := session.get(Publication, item_id):
        # Check permission
        if current_user.id not in pub.get_user_id():
            return abort(401)

        # Delete related items and their children
        for c in pub.collections:
            for item in c.items:
                for syn in item.synonyms:
                    session.delete(syn)
                for spec in item.specimens:
                    session.delete(spec)
                for img in item.images:
                    session.delete(img)
                for dist in item.distributions:
                    session.delete(dist)
                session.delete(item)
            c.publication_id = None

        # Delete literatures
        for lit in pub.literatures:
            session.delete(lit)

        # Delete publication
        session.delete(pub)
        session.commit()

        flash('稿件已刪除', 'success')
        return redirect(url_for('publication.list_view'))

    return abort(404)


@bp.route('/<int:item_id>')
@login_required
def detail_view(item_id):
    publication = session.get(Publication, item_id)

    if current_user.id not in publication.get_user_id():
        return abort(401)

    API_URL=current_app.config['API_URL']
    item_data = []
    for i in publication.collections[0].items:
        # 整理給前端
        specimens = []
        for x in i.specimens:
            data = None
            if x.source_data:
                data = x.source_data
            else:
                data = {}

            data['_id'] = x.id
            data['_text'] = x.text
            data['_recorded_by'] = x.recorded_by
            data['_record_number'] = x.record_number
            data['_locality'] = x.locality
            data['_catalog_number'] = x.catalog_number
            data['_county'] = x.county
            data['_institution_code'] = x.institution_code
            data['_sort'] = x.sort
            specimens.append(data)

        fetched = []
        if i.fetched_specimen_data and len(i.fetched_specimen_data) > 0:
            fetched = i.fetched_specimen_data[0]['data']

        item_data.append({
            'item_id': i.id,
            'name': i.scientific_name,
            'name_id': i.source_data['name_id'],
            'rank_id': i.source_data['rank_id'],
            'selected_specimens': specimens,
            'fetched_specimens': fetched,
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
        session.delete(c)
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

    flash('content modified')
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

        # re-sort literatures
        pl_all = PublicationLiterature.query.filter(PublicationLiterature.publication_id==item_id).order_by(PublicationLiterature.name).all()
        for i, v in enumerate(pl_all):
            v.sort = i+1

        session.commit()
        flash('新增文獻')
        return jsonify({
            'status': 'success'
        })
    return jsonify({
        'status': 'fail'
    })

@bp.route('/<int:item_id>/literatures/patch', methods=['POST'])
@login_required
def patch_publication_literature(item_id):
    if payload := request.json:
        for k, v in payload.items():
            if pl := session.get(PublicationLiterature, int(k)):
                pl.sort = v
        session.commit()
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

@bp.route('/<int:item_id>/update-status/<status>')
@login_required
def update_status(item_id, status):
    publication = session.get(Publication, item_id)
    publication.status = status
    session.commit()

    return jsonify({
        'is_success': True,
    })


@bp.route('/items/<int:item_id>/save-images')
@login_required
def create_item_image(item_id):
    if item := session.get(Item, item_id):
        if payload := request.args.get('payload'):
            data = json.loads(payload)
            for k, v in data.items():
                source_id = k[4:] # chk-xxxx
                vlist = v.split('|')
                im = ItemImage(item_id=item_id, source_id=source_id, text=vlist[0], attribution=vlist[1])
                session.add(im)
            session.commit()
            flash('save images')
            return jsonify({
                'status': 'success',
            })

    return jsonify({
        'status': 'error',
        'massage': 'no item or payload'
    })

@bp.route('/<int:publication_id>/items/<int:item_id>/patch-specimens')
@login_required
def patch_item_specimen(publication_id, item_id):
    # default specimen format
    if item := session.get(Item, item_id):
        exist = {}
        exist_ids = []
        selected_ids = []
        for s in item.specimens:
            exist[s.source_name] = s
            exist_ids.append(s.source_name)

        sort = 0
        selectedIndex = request.args.get('selected', '')
        for i in selectedIndex.split(','):
            sort += 1
            if data := item.fetched_specimen_data:
                d = data[0]['data'][int(i)]
                _id = d['id']
                selected_ids.append(_id)
                text = format_specimen_display(d)
                if _id in exist:
                    #exist[_id].text = text
                    pass
                else:
                    s = ItemSpecimen(
                        item_id=item_id,
                        source_data=d,
                        source_name=_id,
                        text=text,
                        sort=sort,
                        recorded_by=d.get('recordedBy', ''),
                        locality=d.get('locality', ''),
                        record_number=d.get('recordNumber', ''),
                        catalog_number=d.get('catalogNumber', ''),
                        institution_code=d.get('datasetName'), # TODO
                        county=d.get('county', ''),
                    )
                    session.add(s)

        session.commit()

        # delete un checkted
        for k, v in exist.items():
            if k not in selected_ids:
                session.delete(v)
        session.commit()

        return jsonify({'message': 'success'})

@login_required
@bp.route('/<int:publication_id>/modify-specimen/patch', methods=['POST'])
def modify_specimen_text(publication_id):
    if payload := request.json:
        #print(payload)
        if spid := payload.get('spid', ''):
            if sp := session.get(ItemSpecimen, spid):
                sp.text = payload.get('text', '')
                sp.record_number = payload.get('record_number', '')
                sp.recorded_by = payload.get('recorded_by', '')
                sp.catalog_number = payload.get('catalog_number', '')
                sp.institution_code = payload.get('institution_code', '')
                sp.locality = payload.get('locality', '')
                sp.county = payload.get('county', '')
                if sort := payload.get('sort'):
                    sp.sort = sort

                if item_id := payload.get('to_item', ''):
                    old_item_id = sp.item_id
                    if item := session.get(Item, item_id):
                        sp.item_id = item_id

                        if not sp.changed_history:
                            now = datetime.now().strftime('%y%m%d_%H%M%S')
                            sp.changed_history = [[now, int(old_item_id), int(item_id)]]
                    else:
                        return jsonify({'is_success': False, 'message': 'no item_id'})

                session.commit()
                #flash('edit specimen format')
            return jsonify({'is_success': True})
        else:
            ## new 
            if item_id := payload.get('item_id'):
                sp = ItemSpecimen(item_id=item_id)
                sp.text = payload.get('text', '')
                sp.record_number = payload.get('record_number', '')
                sp.recorded_by = payload.get('recorded_by', '')
                sp.catalog_number = payload.get('catalog_number', '')
                sp.institution_code = payload.get('institution_code', '')
                sp.locality = payload.get('locality', '')
                sp.county = payload.get('county', '')
                if sort := payload.get('sort'):
                    sp.sort = sort
                else:
                    if item := session.get(Item, item_id):
                        sp.sort = len(item.specimens) + 1
                session.add(sp)
                session.commit()
            return jsonify({'is_success': True})

    return jsonify({'is_success': False})


@bp.route('/<int:item_id>/publish/post', methods=['POST', 'GET'])
def post_publish(item_id):
    if request.method == 'GET':
        #payload  = request.json
        pub = session.get(Publication, item_id)
        #if payload.get('format', '') == 'docx':
        fmt = request.args.get('format')

        data = {
            'title': pub.title,
            'author': pub.author,
            'literatures': [],
            'items': [],
            'item_category': [],
        }
        for i in pub.literatures:
            data['literatures'].append(i.name)

        for i in pub.collections[0].items:
            rank_id = i.source_data.get('rank_id', '') if i.source_data else ''
            item = {
                'rank_id': rank_id,
                'commonNames': i.common_names,
                'description': i.description,
                'distribution': i.distribution,
                'fullScientificName': i.source_data.get('usage_references_text', '') if i.source_data else '',
                'scientificName': i.scientific_name,
                'note': i.note,
                'synonyms': [],
                'specimens': [],
            }
            for s in i.synonyms:
                item['synonyms'].append(s.name)
                #for j in i.specimens:
                #    item['specimens'].append(j.text)
                item['specimens'] = i.get_grouped_specimens()

            if int(rank_id) == 34: # species level
                #print(i.source_data['usage_references_text'])
                data['items'].append(item)
            else:
                data['item_category'].append(item)


        if fmt == 'docx':
            docx = generate_docx([data])
            buf = BytesIO()
            docx.save(buf)
            buf.seek(0)
            filename = quote(f"output-biota-pub-{pub.title}.docx")
            response = send_file(
                buf,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename}" # for unicode
            response.headers['filename'] = filename

        elif fmt == 'pdf':
            pdf_buffer = generate_pdf([data])
            filename = quote(f"output-biota-pub-{pub.title}.pdf")
            response = send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename}" # for unicode
            response.headers['filename'] = filename

        return response


# ===== Identification Key Routes =====

@bp.route('/<int:pub_id>/keys')
@login_required
def key_list(pub_id):
    if pub := session.get(Publication, pub_id):
        if current_user.id not in pub.get_user_id():
            return abort(401)
        return render_template('publication_key_list.html', publication=pub)
    return abort(404)


@bp.route('/<int:pub_id>/keys/create', methods=['GET', 'POST'])
@login_required
def key_create(pub_id):
    if pub := session.get(Publication, pub_id):
        if current_user.id not in pub.get_user_id():
            return abort(401)

        if request.method == 'POST':
            title = request.form.get('title', '')
            key = IdentificationKey(title=title, publication_id=pub_id)
            session.add(key)
            session.commit()
            return redirect(url_for('publication.key_edit', pub_id=pub_id, key_id=key.id))

        return render_template('publication_key_form.html', publication=pub, key=None)
    return abort(404)


@bp.route('/<int:pub_id>/keys/<int:key_id>')
@login_required
def key_edit(pub_id, key_id):
    if pub := session.get(Publication, pub_id):
        if current_user.id not in pub.get_user_id():
            return abort(401)

        if key := session.get(IdentificationKey, key_id):
            items_raw = pub.collections[0].items if pub.collections else []
            items = [{'id': item.id, 'scientific_name': item.scientific_name} for item in items_raw]
            return render_template('publication_key_form.html', publication=pub, key=key, items=items)

    return abort(404)


@bp.route('/<int:pub_id>/keys/<int:key_id>/entries', methods=['POST'])
@login_required
def key_entry_save(pub_id, key_id):
    if pub := session.get(Publication, pub_id):
        if current_user.id not in pub.get_user_id():
            return abort(401)

        if key := session.get(IdentificationKey, key_id):
            data = request.json

            # Clear existing entries and recreate
            for entry in key.entries:
                session.delete(entry)
            session.commit()

            # Add new entries
            for i, entry_data in enumerate(data.get('entries', [])):
                entry = KeyEntry(
                    key_id=key_id,
                    number=entry_data.get('number', 1),
                    indent_level=entry_data.get('indent_level', 0),
                    description=entry_data.get('description', ''),
                    result_couplet=entry_data.get('result_couplet') or None,
                    result_item_id=entry_data.get('result_item_id') or None,
                    sort=i + 1
                )
                session.add(entry)

            session.commit()
            return jsonify({'status': 'success', 'message': '檢索表已儲存'})

    return jsonify({'status': 'error', 'message': 'Not found'}), 404


@bp.route('/<int:pub_id>/keys/<int:key_id>/delete', methods=['POST', 'GET'])
@login_required
def key_delete(pub_id, key_id):
    if pub := session.get(Publication, pub_id):
        if current_user.id not in pub.get_user_id():
            return abort(401)

        if key := session.get(IdentificationKey, key_id):
            for entry in key.entries:
                session.delete(entry)
            session.delete(key)
            session.commit()
            flash('檢索表已刪除', 'success')
            return redirect(url_for('publication.key_list', pub_id=pub_id))

    return abort(404)
