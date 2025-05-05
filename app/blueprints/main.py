import json
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

