import json
import re
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
)

#from flask.views import MethodView
from app.helpers import get_namespace_data, generate_docx

import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb
import requests

mysql_conn = MySQLdb.connect(host="mysql", user="root", passwd="example", db="taicol")
mysql_cursor = mysql_conn.cursor()

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('main.html')

@bp.route('/api/schema')
def get_schema():
    tables = {
        'my_namespaces': [],
        #'references': [],
        #'taxon_names':[],
    }
    for k in tables:
        mysql_cursor.execute(f'SHOW COLUMNS FROM `{k}`')
        rows = mysql_cursor.fetchall()
        tables[k] = [x[0] for x in rows]

    return jsonify(tables)

@bp.route('/api/data/<schema>')
def get_data(schema):
    offset = 0
    limit = 100
    if q := request.args.get('request'):
        payload = json.loads(q)
        limit = payload.get('limit')
        offset = payload.get('offset')

    mysql_cursor.execute(f'SHOW COLUMNS FROM `{schema}`')
    columns = [x[0] for x in mysql_cursor.fetchall()]

    total = 0
    mysql_cursor.execute(f'SELECT COUNT(*) FROM `{schema}`')
    if r := mysql_cursor.fetchone():
        total = r[0]

    mysql_cursor.execute(f'SELECT * FROM `{schema}` ORDER BY id DESC LIMIT {limit} OFFSET {offset}')
    rows = mysql_cursor.fetchall()
    records = []
    for i, v in enumerate(rows):
        r = {
            'recid': v[0],
            'url': '<a href="http://w2ui.com" target="_blank" title="Click Me!"><u>http://w2ui.com</u></a>',
        }
        for xi, x in enumerate(v):
            r[columns[xi]] = x
        records.append(r)

    # {
    #     "status": "error",
    #     "message": "Error Message"
    # }

    return jsonify({
        'status': 'success',
        'total': total,
        'records': records,
    })


@bp.route('/preview')
def preview():
    namespace_ids = request.args.get('namespace_ids')
    data = []
    for namespace_id in namespace_ids.split(','):
        data.append(get_namespace_data(namespace_id))
    return render_template('preview.html', data=data)

@bp.route('/api/namespaces/<namespace_ids>')
def get_namespaces_data_api(namespace_ids):
    data = []
    for namespace_id in namespace_ids.split(','):
        data.append(get_namespace_data(namespace_id))
    return jsonify(data)

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
            print(i, v)
            records.append({
                'recid': i,
                'key': v['speciesKey'],
                'scientificName': sciName,
                'ref': v['publishedIn'],
                'accordingTo': 'gbif-backbone',
                'status': v['taxonomicStatus'],
            })

    if source == 'taicol':
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

    return jsonify({
        'status': 'success',
        'total': len(records),
        'records': records,
    })

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
        url = f'https://api.gbif.org/v1/occurrence/search?basisOfRecord=PreservedSpecimen&taxonKey={taxon_key}&limit={limit}&offset={offset}'
        resp = requests.get(url)
        data = resp.json()
        print(data)
        dataset_map = {}
        for i, v in enumerate(data['results']):

            # fetch dataset
            dataset_title = ''
            dataset_key = v['datasetKey']
            if dataset_key not in dataset_map:
                resp2 = requests.get(f'https://api.gbif.org/v1/dataset/{dataset_key}')
                data2 = resp2.json()
                dataset_title = data2['title']
                dataset_map[dataset_key] = dataset_title

            #for k2, v2 in v.items():
            #    if 'associa' in k2:
            #        print(k2, v2)
            print(v)
            records.append({
                'recid': i,
                'recordedBy': v['recordedBy'],
                'recordNumber': v.get('recordNumber', ''),
                'catalogNumber': v.get('catalogNumber', ''),
                'remarks': v.get('occurrenceRemarks', ''),
                'locality': v.get('locality', ''),
                'datasetTitle': dataset_map[dataset_key]
            })

        return jsonify({
            'status': 'success',
            'total': data['count'],
            'records': records,
        })
    elif source == 'tbia':
        url = f'https://tbiadata.tw/api/v1/occurrence?basisOfRecord=PreservedSpecimen&taxonID={taxon_key}&limit={limit}'
        resp = requests.get(url)
        data = resp.json()
        #print(data)
        return jsonify({
            'status': 'success',
            'total': 0,
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

