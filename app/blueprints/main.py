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

from flask_login import (
    login_required,
    logout_user,
)

#from flask.views import MethodView
from app.helpers import get_namespace_data, generate_docx
from app.database import session

from app.models import (
    User,
    Collection,
    Notification,
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
def index():
    return render_template('dashboard.html')

@bp.route('/main')
def main():
    return render_template('main.html')

@bp.route('/namespaces/')
def namespace_list():
    current_user = session.get(User, 2)
    collections = Collection.query.filter(Collection.user_id==current_user.id).all()
    return render_template('namespace_list.html', collections=collections)

@bp.route('/client')
def client():
    return render_template('client.html')


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
        data = get_namespace_data(namespace_id)
        return render_template('preview.html', data=data)

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

            print(named_areas)
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
        url = f'https://tbiadata.tw/api/v1/occurrence?isCollection=true&taxonID={taxon_key}&limit={limit}'
        resp = requests.get(url)
        data = resp.json()
        if data['status']['code'] == 200:
            for i,v in enumerate(data['data']):
                specimen_display = {
                    'county': '',
                    'locality': '',
                    'collector': '',
                    'record_number': '',
                }
                named_areas = {}
                for term, field in DWC_TERMS.items():
                    if x := v.get(term):
                        key = term if field == '' else field
                        named_areas[key] = x
                        if key == 'adm2':
                            if county_en := taiwan_counties_english.get(x):
                                specimen_display['county'] = county_en.upper()
                        if key == 'locality':
                            specimen_display['locality'] = x
                            #'ILAN: Nanhutashan, Lu 24973.
                            # NANTOU: Mt.Kiraishiu, Wilson 10074 (Type of B. nantoensis, A!);'
                media = []
                if x := v.get('associatedMedia'):
                    media.append(x)

                locality_list = []
                if x:= v.get('county'):
                    locality_list.append(x)
                if x:= v.get('locality'):
                    locality_list.append(x)

                date = ''
                if x := v.get('eventDate'):
                    y = x[0:4]
                    m = x[5:7]
                    d = x[8:10]
                    date = f'{y}.{m}.{d}'

                #print(v)
                #print(named_areas)
                recorded_by = ''
                if x := v.get('recordedBy', ''):
                    recorded_by = x
                    specimen_display['collector'] = recorded_by
                record_number = ''
                if x := v.get('recordNumber', ''):
                    record_number = x
                    specimen_display['record_number'] = x

                records.append({
                    'recid': i,
                    'url': v.get('references', ''),
                    'institutionCode': '',
                    'recordedBy': recorded_by,
                    'basisOfRecord': v.get('basisOfRecord', ''),
                    'recordNumber': record_number,
                    'catalogNumber': v.get('catalogNumber', ''),
                    'date': date,
                    'remarks': '',
                    'locality': '|'.join(locality_list),
                    'datasetTitle': v['datasetName'],
                    'media': media,
                    'named_areas': named_areas,
                    'specimen_display': specimen_display,
                })

            # TODO: CORS
            resp = jsonify({
                'status': 'success',
                'total': data['meta']['total'],
                'records': records,
            })
            resp.headers.add('Access-Control-Allow-Origin', '*')
            resp.headers.add('Access-Control-Allow-Methods', '*')
            return resp
        else:
            return jsonify({
                'status': 'error',
                'message': data['status']['message'],
            })
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
