import json
import re
from datetime import datetime
from io import BytesIO


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

#from flask.views import MethodView
from app.helpers import get_namespace_data, generate_docx, fetch_tbia_specimens, send_email
from app.database import session

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
#import pymysql

#pymysql.install_as_MySQLdb()
#import MySQLdb

import requests
from bs4 import BeautifulSoup

#mysql_conn = MySQLdb.connect(host="mysql", user="root", passwd="example", db="taicol")
#mysql_cursor = mysql_conn.cursor()

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html', subheader='Index')



@bp.route('/nametool')
def nametool():
    return render_template('main.html')

'''
@bp.route('/publications')
@login_required
def publication_list():
    if namespace_id := request.args.get('namespace_id'):
        # create a publication invoked by TaiCOL nametool
        taicol_api = current_app.config['TAICOL_API']
        email = current_user.email
        resp = requests.get(f'{taicol_api}/user/namespace?email={email}')
        if resp.ok:
            resp_json = resp.json()
            available_namespaces = resp_json.get('namespaces', [])
            if int(namespace_id) in available_namespaces:
                collection_id = None
                if c := Collection.query.filter(Collection.source_id==namespace_id, Collection.user_id==current_user.id).scalar():
                    collection_id = c.id
                    current_app.logger.info(f'collection [{c.id}] already exist')
                else:
                    c = Collection(name='', source_id=namespace_id, user_id=current_user.id)
                    session.add(c)

                    n = Notification(user_id=current_user.id, content=f'namespace [{namespace_id}] published')
                    session.add(n)
                    session.commit()
                    collection_id = c.id
                return redirect(url_for('main.create_publication', collection_id=collection_id))
        return abort(401)
    else:
        collections = Collection.query.filter(Collection.user_id==current_user.id).all()
        return render_template('publication_list.html', collections=collections, subheader='Publications')


@bp.route('/publications/create/<int:collection_id>')
@login_required
def create_publication(collection_id):
    if collection := session.get(Collection, int(collection_id)):
        pub = Publication(title=collection.name, author=current_user.username)
        session.add(pub)
        session.commit()
        collection.publication_id = pub.id
        session.commit()

        # update collection, call TAICOL API
        url = f"{current_app.config['TAICOL_API']}/biota?namespace_id={collection.source_id}&token={current_app.config['TAICOL_TOKEN']}"
        resp = requests.get(url)
        data = resp.json()

        pub.title = data['title']
        collection.name = data['title']
        collection.source_name = 'namespace'
        collection.source_data = data

        for i in data['literatures']:
            pl = PublicationLiterature(publication_id=pub.id, source_id=i['reference_id'], name=i['citation'])
            session.add(pl)

        for i in data['group']:
            name = i['name'].replace('<i>', '').replace('</i>', '')
            item = Item(collection_id=collection_id, description=i['description'], distribution=i['distribution'], note=i['note'], user_id=current_user.id, scientific_name=name, source_data=i, common_names='|'.join(i['common_names']))
            session.add(item)
            session.commit()

            for syn in i['synonyms']:
                item_syn = ItemSynonym(item_id=item.id, name=syn['usage_references_text'], ref=f"name_id:{i['name_id']}")
                session.add(item_syn)

        session.commit()
        flash(f'publication created, via: namespace_id {collection.source_id}')
    return redirect(url_for('main.publication_detail', publication_id=pub.id))


@bp.route('/publications/<int:publication_id>')
@login_required
def publication_detail(publication_id):
    publication = session.get(Publication, publication_id)
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
    return render_template('publication_detail.html', publication=publication, subheader='Publications', API_URL=API_URL, item_data_json=json.dumps(item_data))@bp.route('/publications/<int:publication_id>')
@login_required
def publication_detail(publication_id):
    publication = session.get(Publication, publication_id)
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
    return render_template('publication_detail.html', publication=publication, subheader='Publications', API_URL=API_URL, item_data_json=json.dumps(item_data))


@bp.route('/publications/<int:publication_id>/delete')
@login_required
def delete_publication(publication_id):
    publication = session.get(Publication, publication_id)
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
    return redirect(url_for('main.publication_list'))
'''

@bp.route('/literatures/patch')
@login_required
def patch_literatures():
    #for k, v in request.form.items():
    #    print(k, v)
    #session.commit()
    for k, v in request.args.items():
        if 'literature_text_' in k:
            lit_id = k.replace('literature_text_', '')
            print(lit_id, v)
            if lit := session.get(PublicationLiterature, lit_id):
                lit.name = v
    session.commit()
    flash('update literature')
    return jsonify({'status': 'success'})


'''
@bp.route('/publications/<int:publication_id>/patch')
@login_required
def patch_publication(publication_id):
    publication = session.get(Publication, publication_id)
    if status := request.args.get('status', ''):
        publication.status = status
    if x := request.args.get('title', ''):
        publication.title = x

    session.commit()
    #return redirect(url_for('main.publication_detail', publication_id=publication_id))
    #flash('patch ok')
    return jsonify({'status': 'success'})
'''
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

@bp.route('/items/<int:item_id>/patch-specimens')
@login_required
def patch_item_specimen(item_id):
    # default specimen format
    if item_specimen := session.get(Item, item_id):
        if selected := request.args.get('selected'):
            for i in selected.split(','):
                if isp := session.get(ItemSpecimen, i):
                    sd = isp.source_data
                    record_number = sd.get('recordNumber', '--')
                    recorded_by = sd.get('recordedBy', '--')
                    locality = sd.get('locality', '--')
                    dataset_name = sd.get('datasetName', '--') # institudion ID ?
                    isp.text = f'{locality}, {recorded_by} {record_number} ({dataset_name})'
        session.commit()
        return jsonify({'message': 'success'})

@login_required
@bp.route('/modify-specimen')
def modify_specimen_text():
    content = request.args.get('specimen_content', '')
    if spid := request.args.get('spid', ''):
        if sp := session.get(ItemSpecimen, spid):
            sp.text = content
            session.commit()
            flash('edit specimen format')
            return jsonify({'message': 'success'})

@bp.route('/client')
def client():
    return render_template('client.html')

@bp.route('/api/schema')
def get_schema():
    from app.helpers import get_db_connection
    conn = get_db_connection()
    mysql_cursor = conn.cursor()

    tables = {
        'my_namespaces': [],
        #'references': [],
        #'taxon_names':[],
    }
    for k in tables:
        mysql_cursor.execute(f'SHOW COLUMNS FROM `{k}`')
        rows = mysql_cursor.fetchall()
        #    tables[k] = [x[0] for x in rows]
        tables[k] = [x['Field'] for x in rows]

    return jsonify(tables)

@bp.route('/api/data/<schema>')
def get_data(schema):
    from app.helpers import get_db_connection
    conn = get_db_connection()
    mysql_cursor = conn.cursor()

    offset = 0
    limit = 100
    if q := request.args.get('request'):
        payload = json.loads(q)
        limit = payload.get('limit')
        offset = payload.get('offset')

    mysql_cursor.execute(f'SHOW COLUMNS FROM `{schema}`')
    columns = [x['Field'] for x in mysql_cursor.fetchall()]

    total = 0
    mysql_cursor.execute(f'SELECT COUNT(*) FROM `{schema}`')
    if r := mysql_cursor.fetchone():
        total = r['COUNT(*)']

    mysql_cursor.execute(f'SELECT * FROM `{schema}` ORDER BY id DESC LIMIT {limit} OFFSET {offset}')
    rows = mysql_cursor.fetchall()
    records = []
    for i, v in enumerate(rows):
        r = {
            'recid': v['id'],
            'url': '<a href="http://w2ui.com" target="_blank" title="Click Me!"><u>http://w2ui.com</u></a>',
        }
        #for xi, x in enumerate(v):
        #    print(xi, x, columns[xi])
            #r[columns[xi]] = x
        #r.update(v)
        v['recid'] = v['id']
        records.append(v)

    # {
    #     "status": "error",
    #     "message": "Error Message"
    # }
    return jsonify({
        'status': 'success',
        'total': total,
        'records': records,
    })

@bp.route('/preview3/<int:namespace_id>')
def preview3(namespace_id):
    return render_template('preview3.html', data=get_namespace_data(namespace_id))

@bp.route('/preview')
def preview():
    #namespace_ids = request.args.get('namespace_ids')
    #data = []
    #for namespace_id in namespace_ids.split(','):
    #    data.append(get_namespace_data(namespace_id))
    #return render_template('preview.html', data=data)

    if namespace_id := request.args.get('namespace_id'):
        #data = get_namespace_data(namespace_id)
        return render_template(
            'preview.html',
            #data=data,
            API_URL=current_app.config['API_URL'],
            TAICOL_TOKEN=current_app.config['TAICOL_TOKEN'],
            TAICOL_API=current_app.config['TAICOL_API'],
            subheader="Editing")

@bp.route('/preview2/<int:namespace_id>')
def preview2(namespace_id):
    return render_template('preview2.html', namespace_id=namespace_id)

@bp.route('/api/namespaces/<namespace_ids>')
def get_namespaces_data_api(namespace_ids):
    data = []
    for namespace_id in namespace_ids.split(','):
        data.append(get_namespace_data(namespace_id))

        # TODO: CORS
        resp = jsonify(data)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Methods', '*')
        return resp

@bp.route('/api/external/names/<source>/<key>')
def get_external_names_api(source, key):
    records = []
    if source == 'gbif':
        nlist = key.split(' ')
        cname = nlist[0]
        if len(nlist) > 1:
            cname = f'{cname} {nlist[1]}'
        resp = requests.get(f'https://api.gbif.org/v1/species/search?q=${cname}&rank=SPECIES&datasetKey=d7dddbf4-2cf0-4f39-9b2a-bb099caae36c')
        results = resp.json()
        for i, v in enumerate(results['results']):
            sci_name = v['scientificName']
            if x := v['authorship']:
                sciName = f'{sci_name} {x}';
            #print(i, v)
            records.append({
                'recid': i,
                'key': v['speciesKey'],
                'scientificName': sciName,
                'ref': v['publishedIn'],
                'accordingTo': 'gbif-backbone',
                'status': v['taxonomicStatus'],
            })

        return jsonify({
            'status': 'success',
            'total': len(records),
            'records': records,
        })

    elif source == 'taicol':
        if m := re.match(r'\[([0-9]+)\](.+)', key):
            nameid = m.group(1)
            q = m.group(2)
            #resp = requests.get(f'https://api.taicol.tw/v2/taxon?scientific_name={cname}')
            resp = requests.get(f'https://api.taicol.tw/v2/name?name_id={nameid}')
            results = resp.json()
            inc = 0

            if results['status']['code'] == 200:
                for i,v in enumerate(results['data']):
                    nlist = []
                    nlist.append(v['simple_name'])
                    if x := v.get('name_author'):
                        nlist.append(x)
                    if x := v.get('common_name_c'):
                        nlist.append(x)

                    for t in v['taxon']:
                        records.append({
                            'recid': inc,
                            'key': t.get('taxon_id', ''),
                            'scientificName': ' '.join(nlist),
                            'status': t['taicol_name_status'],
                            'ref': v['protologue'],
                            'accordingTo': 'taicol',
                        })
                        inc += 1

                # TODO: CORS
                resp = jsonify({
                    'status': 'success',
                    'total': len(records),
                    'records': records,
                })
                resp.headers.add('Access-Control-Allow-Origin', '*')
                resp.headers.add('Access-Control-Allow-Methods', '*')
                return resp
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"[{source}]{results['status']['message']}",
                })
    elif source == 'nametool':
        if m := re.match(r'\[([0-9]+)\](.+)', key):
            nameid = m.group(1)
            q = m.group(2)

            mysql_cursor.execute(f'SELECT t.taxon_id, r.title FROM api_taxon t LEFT JOIN `references` r ON r.id = t.fixed_reference_id WHERE fixed_taxon_name_id={nameid}')
            rows = mysql_cursor.fetchall()
            inc = 0
            for r in rows:
                records.append({
                    'recid': inc,
                    'key': r[0],
                    'scientificName': q,
                    'status': '',
                    'ref': r[1],
                    'accordingTo': 'nametool',
                })
            return jsonify({
                'status': 'success',
                'total': len(records),
                'records': records,
            })
    elif source == 'tai2':
        nlist = key.split(' ')
        cname = nlist[0]
        if len(nlist) > 1:
            cname = f'{cname} {nlist[1]}'

        resp = requests.get(f'https://tai2.ntu.edu.tw/search_name/{cname}')
        for i, v in enumerate(resp.json()['result2']):

            # get ref info
            resp2 = requests.get(f"https://tai2.ntu.edu.tw/species/{v['code']}")
            soup = BeautifulSoup(resp2.text, 'lxml')
            ref_container = soup.find('div', class_='name1')
            ref_tags = soup.find('div', class_='name1').contents
            ref_tags = [x for x in ref_tags if x.get_text(strip=True)]
            refs = []
            refs.append(f"{ref_tags[0].get_text(strip=True)}: {ref_tags[1].get_text(strip=True)}")
            refs.append(f"{ref_tags[2].get_text(strip=True)}: {ref_tags[3].get_text(strip=True)}")
            records.append({
                'recid': i,
                'key': v['code'],
                'scientificName': v['ebooksearch'],
                'status': '',
                'ref': '|'.join(refs),
                'accordingTo': 'Tai2',
            })

        return jsonify({
            'status': 'success',
            'total': len(records),
            'records': records,
        })
    elif source == 'pass':
        names = key.split(' ')
        cname = names[0]
        if len(names) > 1:
            cname = f'{cname} {names[1]}'

        records.append({
            'recid': 0,
            'key': cname,
            'scientificName': key,
            'status': '',
            'ref': '',
            'accordingTo': '',
        })
        return jsonify({
            'status': 'success',
            'total': len(records),
            'records': records,
        })

DWC_TERMS = {
    'countryCode': 'cc',
    'stateProvince': 'adm1',
    'county': 'adm2',
    'municipality': 'adm3',
    'locationID': '',
    'higherGeographyID': '',
    'higherGeography': '',
    'continent': '',
    'waterBody': '',
    'islandGroup': '',
    'island': '',
    'country': '',
    'locality': '',
    'verbatimLocality': '',
    'minimumElevationInMeters': '',
    'maximumElevationInMeters': '',
    'verbatimElevation': '',
    'verticalDatum': '',
    'minimumDepthInMeters': '',
    'maximumDepthInMeters': '',
    'verbatimDepth': '',
    'minimumDistanceAboveSurfaceInMeters': '',
    'maximumDistanceAboveSurfaceInMeters': '',
    'locationAccordingTo': '',
    'locationRemarks': '',
    'decimalLatitude': '',
    'decimalLongitude': '',
    'geodeticDatum': '',
    'coordinateUncertaintyInMeters': '',
    'coordinatePrecision': '',
    'pointRadiusSpatialFit': '',
    'verbatimCoordinates': '',
    'verbatimLatitude': '',
    'verbatimLongitude': '',
    'verbatimCoordinateSystem': '',
    'verbatimSRS': '',
    'footprintWKT': '',
    'footprintSRS': '',
    'footprintSpatialFit': '',
    'georeferencedBy': '',
    'georeferencedDate': '',
    'georeferenceProtocol': '',
    'georeferenceSources': '',
    'georeferenceRemarks': '',
}

TBIA_TERMS = {
    'county': 'adm1',
    'municipality': 'adm2',
}

taiwan_counties_english = {
    '宜蘭縣': 'Yilan',
    '桃園市': 'Taoyuan',
    '新竹縣': 'Hsinchu',
    '苗栗縣': 'Miaoli',
    '彰化縣': 'Changhua',
    '南投縣': 'Nantou',
    '雲林縣': 'Yunlin',
    '嘉義縣': 'Chiayi',
    '屏東縣': 'Pingtung',
    '臺東縣': 'Taitung',
    '花蓮縣': 'Hualien',
    '澎湖縣': 'Penghu',
    '基隆市': 'Keelung',
    '新竹市': 'Hsinchu',
    '嘉義市': 'Chiayi',
    '臺北市': 'Taipei',
    '新北市': 'New Taipei',
    '臺中市': 'Taichung',
    '臺南市': 'Tainan',
    '高雄市': 'Kaohsiung'
}
#    'standardDate',
#    'standardLatitude',
#    'standardLongitude',
@bp.route('/api/external/data/<source>/<taxon_key>', methods=['GET', 'POST'])
def get_external_data_api(source, taxon_key):
    '''w2ui style request & response'''
    offset = 0
    limit = 100
    records = []
    if q := request.args.get('request'):
        payload = json.loads(q)
        limit = payload.get('limit')
        offset = payload.get('offset')

    if source == 'gbif':
        url = f'https://api.gbif.org/v1/occurrence/search?basisOfRecord=PreservedSpecimen&basisOfRecord=LivingSpecimen&taxonKey={taxon_key}&limit={limit}&offset={offset}'
        resp = requests.get(url)
        data = resp.json()
        #print(data)
        dataset_map = {}
        distribution = {}
        for i, v in enumerate(data['results']):

            # fetch dataset
            dataset_title = ''
            dataset_key = v['datasetKey']
            if dataset_key not in dataset_map:
                resp2 = requests.get(f'https://api.gbif.org/v1/dataset/{dataset_key}')
                data2 = resp2.json()
                dataset_title = data2['title']
                dataset_map[dataset_key] = dataset_title
                #print(data2['title'])

            locality_list = []
            #if x:= v.get('country'):
            named_areas = {}
            for term, field in DWC_TERMS.items():
                if x := v.get(term):
                    key = term if field == '' else field
                    named_areas[key] = x

            if x:= v.get('county'):
                locality_list.append(x)
            if x:= v.get('locality'):
                locality_list.append(x)

            #print(named_areas)
            media = []
            if m := v.get('media'):
                for i in m:
                    if type_ := i.get('type'):
                      if type_ == 'StillImage':
                          if iden := i.get('identifier'):
                              media.append(iden)

            #for k2, v2 in v.items():
            #    if 'media' in k2:
            #        print(k2, v2)
            #print(v)
            records.append({
                'recid': i,
                'url': f"https://www.gbif.org/occurrence/{v.get('key')}",
                'institutionCode': v.get('institutionCode', ''),
                'basisOfRecord': v['basisOfRecord'],
                'recordedBy': v.get('recordedBy', ''),
                'recordNumber': v.get('recordNumber', ''),
                'catalogNumber': v.get('catalogNumber', ''),
                'date': f"{v.get('year', 'Y')}.{v.get('month', 'M')}.{v.get('day', 'D')}",
                'remarks': v.get('occurrenceRemarks', ''),
                'locality': '|'.join(locality_list),
                'datasetTitle': dataset_map[dataset_key],
                'media': media,
                'named_areas': named_areas,
            })

        return jsonify({
            'status': 'success',
            'total': data['count'],
            'records': records,
        })
    elif source == 'tbia':
        has_item = False
        item_id = request.args.get('item_id', '')
        existSpecimenData = []
        if item_id:
            item = session.get(Item, item_id)
            has_item = True
            for x in item.specimens:
                existSpecimenData.append(x.source_data)

        data = {}
        if len(existSpecimenData) > 0:
            data = {
                'status': 'success',
                'total': len(existSpecimenData),
                'records': existSpecimenData
            }
        else:
            # fetch tbia (new)
            data = fetch_tbia_specimens(taxon_key)
            if has_item:
                for r in data['records']:
                    # save to ItemSpecimen
                    raw = r['_raw']
                    item_sp = ItemSpecimen(item_id=item.id, source_data=raw, text='', key=raw['id'], source_name='tbia')
                    session.add(item_sp)
                session.commit()

        # TODO: CORS
        resp = jsonify(data)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Methods', '*')
        return resp

    elif source == 'tai2':
        resp = requests.get(f'https://tai2.ntu.edu.tw/species/{taxon_key}')
        soup = BeautifulSoup(resp.text, 'lxml')

        # find specimens
        specimens = []
        for x in soup.find_all('script'):
            text = x.get_text(strip=True)
            if 'var spcm=new Array();' in text:
                start = text.index('var spcm=new Array();') + len('var spcm=new Array();\nvar spcm=') + 1
                end = text.index('var spcmtype=new Array();')
                s = text[start:end].strip()
                specimens = json.loads(s[0:-1])

        #print(len(specimens))
        for i, v in enumerate(specimens):
            print(v)
            locs = []
            if info := v['locinfo']:
                if x := info['district']:
                    locs.append(x)
                if x := info['loc']:
                    locs.append(x)

            media = []
            if x := v['imgsmall']:
                media.append(f"https://tai2.ntu.edu.tw{x}")

            date = ''
            if x:= v['date']:
                date = x.replace('/', '.')

            records.append({
                'recid': i,
                'recordedBy': v.get('collinfo', ''),
                'catalogNumber': v.get('TAIID', ''),
                'recordNumber': v.get('collno', ''),
                'date': date,
                'basisOfRecord': '',
                'locality': '|'.join(locs),
                'institutionCode': v['herb'],
                'media': media,
                'remarks': '',
                'datasetTitle': 'Tai2',
                'url': f"https://tai2.ntu.edu.tw/species/{taxon_key}/{v['TAIID']}"
            })
        return jsonify({
            'status': 'success',
            'total': 0,
            'records': records,
        })
    elif source == 'taif':
        # DEPRECATED, use tbia API
        response = requests.get(f'https://taif.tfri.gov.tw/search/result.php?l=Cht&ol=1&keyword={key}')
        soup = BeautifulSoup(response.text, 'lxml')
        inc = 0
        for row in soup.find_all('div', class_='table-rows'):
            coll_data = row.find('div', class_="collector").contents
            collector = coll_data[0].text
            coll_num = coll_data[1].text

            date = row.find('div', class_='cdate').text # format need change
            locality = row.find('div', class_='locality').text
            catalog_number = row.find('div', class_='hno').contents[0].text
            url = row['onclick'].replace("window.open('", '').replace("', '_blank')", '')
            url = f'https://taif.tfri.gov.tw/search/{url}'
            #media = ['https://taif.tfri.gov.tw/specimen-images-tiles/20221004/541064_005_000_000.jpg']
            media = []
            records.append({
                'recid': inc,
                'url': url,
                'catologNumber': catalog_number,
                'recordedBy': collector,
                'recordNumber': coll_num,
                'locality': locality,
                'date': date,
                'remarks': '',
                'datasetTitle': 'TAIF',
                'institutionCode': 'TAIF',
                'basisOfRecord': 'PreservedSpecimen',
                'media': [],
            })
        return jsonify({
            'status': 'success',
            'total': len(records),
            'records': records,
        })


@bp.route('/api/publish', methods=['POST'])
def post_publish():
    if request.method == 'POST':
        payload = request.json
        if ids := payload.get('namespaceIds'):
            data = []
            for namespace_id in ids.split(','):
                data.append(get_namespace_data(namespace_id))

            if payload.get('format', '') == 'docx':
                docx = generate_docx(data)
                buf = BytesIO()
                docx.save(buf)
                buf.seek(0)

                filename = f"output-{ids.replace(',', 'x')}.docx"
                response = send_file(
                    buf,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response.headers['Content-Disposition'] = 'attachment'
                response.headers['filename'] = filename

                return response

@bp.route('/api/fake-literatures')
def get_fake_literatures_api():
    from app.helpers import get_db_connection
    conn = get_db_connection()
    mysql_cursor = conn.cursor()

    result = {}
    if q := request.args.get('q'):
        mysql_cursor.execute(f"SELECT * FROM `references` WHERE title LIKE '%{q}%'")
        rows = mysql_cursor.fetchall()
        result['data'] = [{'id': x['id'], 'title': x['title']} for x in rows]

    return jsonify(result)

@bp.route('/notifications')
def notification_list():
    return render_template('notification_list.html', notifications=current_user.notifications)

@bp.route('/notifications/<int:nid>/read')
def read_notification(nid):
    if n := session.get(Notification, nid):
        n.read_at = datetime.utcnow()
        session.commit()
        return redirect(url_for('main.notification_list'))
