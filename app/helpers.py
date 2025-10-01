import re
import json
from datetime import datetime

from flask import g, current_app
from sqlalchemy import (
    select,
)
from docx import Document
from docx.shared import Pt, Mm, Cm, Inches
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION, WD_ORIENT, WD_SECTION_START
from docx.enum.table import WD_ALIGN_VERTICAL
import yaml

from bs4 import BeautifulSoup
import requests

import boto3
from botocore.exceptions import ClientError

from app.models import (
    Collection,
    Publication,
    PublicationLiterature,
    Item,
    ItemSynonym,
)
from app.database import session
from app.jinja_func import pick_first

class BiotaPrint(object):
    doc = None

    def __init__(self):
        self.doc = Document()

    def as_docx(self):
        return self.doc

    def save(self, name):
        self.doc.save(f'{name}.docx')

    def create_column_section(self, num_columns):
        """Add section with specified number of columns and optional custom widths."""
        section = self.doc.add_section(WD_SECTION_START.CONTINUOUS)

        page_width = 8.5  # Standard US Letter width in inches
        margin = 1.0      # 1-inch margins
        usable_width = page_width - 2 * margin  # Available width for content
        column_widths = [usable_width] if num_columns == 1 else [usable_width / 2, usable_width / 2]

        # Create the columns XML element
        cols = OxmlElement('w:cols')
        cols.set(qn('w:num'), str(num_columns))
        cols.set(qn('w:equalWidth'), "0" if column_widths else "1")

        # If specific widths are provided, add them to the columns element
        if column_widths:
            for width in column_widths:
                col = OxmlElement('w:col')
                # Convert inches to twentieths of a point (unit used in docx)
                width_in_twips = int(width * 1440)  # 1440 twips = 1 inch
                col.set(qn('w:w'), str(width_in_twips))
                cols.append(col)

        # Add the columns element to the section properties
        section._sectPr.append(cols)
        return section

    def parse_styled_text(self, text):

        result = []
        text = text.replace('<br>', '\n\n')
        parts = re.split(r'(</?i>)', text)

        is_italic = False
        for part in parts:
            if part == '<i>':
                is_italic = True
            elif part == '</i>':
                is_italic = False
            elif part:  # Keep the text segment as-is
                style = 'italic' if is_italic else 'normal'
                result.append([part, style])

        return result


    def add_box(self, data, args={}):

        is_list = False
        if isinstance(data, list):
            is_list = True

        p = self.doc.add_paragraph()

        align = args.get('align', '')
        styles = args.get('styles', [])
        size = args.get('size', '')

        if align == 'justify':
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif align == 'center':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER


        runs = []

        if is_list:
            for x in data:
                res = self.parse_styled_text(x)
                runs += res
            runs.append(['\n', 'normal'])

        else:
            res = self.parse_styled_text(data)
            runs = res

        for t in runs:
            run = p.add_run(t[0])

            if 'h' in size:
                if 'bold' not in styles:
                    styles.append('bold')

            if 'italic' in styles or t[1] == 'italic':
                run.italic = True

            if 'bold' in styles:
                run.bold = True

            if size == 'h2':
                run.font.size = Pt(12)
            elif size == 'h3':
                run.font.size = Pt(11)


    def add_list(self, data, has_italic=False):
        p = self.doc.add_paragraph()
        for x in data:
            self.add_content(x + '\n', align='left', paragraph=p, has_italic=has_italic)


def generate_docx(data):

    biota = BiotaPrint()

    # default section
    biota.add_box('Biota Taiwanica', {'size':'h3'})
    biota.add_box(f'generated: {datetime.now()}')
    biota.doc.add_page_break()

    for idx, d in enumerate(data):
        section = biota.create_column_section(1)
        biota.add_box(d['title'], {'size': 'h2', 'align': 'center'})
        biota.add_box(d['author'], {'size': 'h3', 'align': 'center'})
        biota.add_box('LITERATURE', {'size': 'h3'})
        biota.add_box(d['literatures'])

        #biota.add_content(['a <i>haha</i> b', 'foo<i>o</i>, and <i>oo</i>p'])

        section = biota.create_column_section(2)

        for i, v in enumerate(d['items']):
            name_list = v['scientificName'].split('</i>')
            scname = name_list[0].replace('<i>', '')

            title = f"{int(i+1)}. {v['scientificName']}"
            biota.add_box(title, {'size': 'h3'})

            if v['commonNames']:
                x = pick_first(v['commonNames'], '|', 'zh')
                biota.add_box(x)

            #biota.add_content('SYNONYMS', 'h3')
            for x in v['synonyms']:
                biota.add_box(x)

            if x := v.get('description'):
                #biota.add_content('DESCRIPTION', 'h3')
                biota.add_box(x, {'align': 'justify'})

            if x:= v.get('distribution'):
                #biota.add_content('DISTRIBUTION', 'h3')
                biota.add_box(x, {'align': 'justify'})

            if len(v['specimens']):
                #biota.add_content('SPECIMENS', 'h3')
                #    biota.add_box(v['specimens'])
                s = ''
                for dist, sp_list in v['specimens'].items():
                    #s = dist
                    sp_arr = [x[1] for x in sp_list]
                    sp_str = ';'.join(sp_arr)
                    s += f'{dist}: {sp_str}. '
                biota.add_box(s)

            if x:= v['note']:
                #biota.add_content('NOTE', 'h3')
                biota.add_box(x, {'align': 'justify'})

    return biota.as_docx()


def get_namespace_data(namespace_id):
    conn = get_db_connection()
    data = {
        'title': '',
        'author': '',
        'literatures': [],
        'items': [],
        'id': namespace_id,
        'reference_name': ''
    }

    #mysql_cursor.execute(literature_sql)
    mysql_cursor = conn.cursor()
    #with conn.cursor() as cursor:
    literature_sql = f'SELECT a.author, a.reference_id, a.content FROM import_checklist_logs c LEFT JOIN api_citations a ON FIND_IN_SET(a.reference_id, c.included_references) > 0 WHERE c.namespace_id = {namespace_id}'
    mysql_cursor.execute(literature_sql)
    rows = mysql_cursor.fetchall()
    for r in rows:
        data['literatures'].append({'author': r['author'], 'id': r['reference_id'], 'content': r['content']})

    mysql_cursor.execute(f'SELECT n.title, u.name FROM my_namespaces n LEFT JOIN users u ON u.id = n.user_id WHERE n.id={namespace_id}')
    result = mysql_cursor.fetchone()
    data['title'] = result['title']
    data['author'] = result['name']

    mysql_cursor.execute(f"SELECT t.name, t._authorship, t.id, u.per_usages, u.type_specimens, u.properties, r.title, u.id, t.properties, u.name_remark, u.group, u.updated_at FROM my_namespace_usages u LEFT JOIN taxon_names t ON u.taxon_name_id = t.id LEFT JOIN `references` r ON r.id = t.reference_id WHERE namespace_id={namespace_id} AND u.status='accepted' ORDER by `order`")

    rows = mysql_cursor.fetchall()
    for row in rows:
        #print(row)
        common_names = []
        synonyms = []
        note = ''
        description = ''
        distribution = ''
        add_fields = {}
        specimens = []
        taicol_name_id = row['id']

        per_usages = []
        type_specimens = {}
        properties = {}

        if x := row['per_usages']:
            #source_data['usages'] = yaml.dump(json.loads(x), default_flow_style=False, sort_keys=False, allow_unicode=True)
            per_usages = json.loads(row['per_usages'])
        if x := row['properties']:
            #description:"特徵描述",diagnosis:"鑑定特徵",distribution:"物種分布",etymology:"語源",habitat:"棲地",substrata:"基質",measurements:"測量",coloration:"顏色",otherExaminedMaterial:"其他引證標本"
            properties = json.loads(x)
            #source_data['props'] = yaml.dump(props, default_flow_style=False, sort_keys=False, allow_unicode=True)

            if names := properties.get('common_names'):
                for n in names:
                    if x := n['name']:
                        common_names.append(x.replace('\u0000', '').strip())

        if x := row['type_specimens']:
            type_specimens = json.loads(x)
            #source_data['type'] = yaml.dump(sp, default_flow_style=False, sort_keys=False, allow_unicode=True)

        #if x := row[6]:
        #    if x not in data['literatures']:
        #        data['literatures'].append(x)

        if x:= row['group']:
            # mysql_cursor.execute(f"SELECT ru.id, ru.status, t.name, t._authorship, r.title FROM reference_usages ru LEFT JOIN `references` r ON r.id = ru.reference_id LEFT JOIN taxon_names t ON t.id = ru.taxon_name_id WHERE ru.accepted_taxon_name_id={x} and ru.status != 'accepted'")
            # results = mysql_cursor.fetchall()
            # sci_name = ''
            # ref_title = ''
            # for i in results:
            #     sci_name = i['name']
            #     if author := i['_authorship']:
            #         sci_name = f'{sci_name} {author}'
            #     if ref := i['title']:
            #         ref_title = ref
            #     synonyms.append([sci_name, ref_title])

            mysql_cursor.execute(f"SELECT t.name, t.formatted_authors, t.id, u.properties FROM my_namespace_usages u LEFT JOIN taxon_names t ON u.taxon_name_id = t.id WHERE u.namespace_id={namespace_id} AND u.status != 'accepted' AND u.group = {x}")

            res_synonyms = mysql_cursor.fetchall()
            for x in res_synonyms:
                y = {}
                for k, v in x.items():
                    if k == 'properties':
                        y[k] = json.loads(v)
                    else:
                        y[k] = v
                synonyms.append(y)

        # item_title atomic struct
        item_title = {
            'scientific_name': {
                'canonical': row['name'],
                'author': '',
                'full': ''
            },
            'ref': '',
            'name_in_ref': '',
            'type': {
                'use': '',
                'gathering': {
                    'country': '',
                    'locality': '',
                    'locality2': '',
                    'year': '',
                    'month': '',
                    'day': '',
                    'field_number': '',
                },
                'specimens': [],
            },
            'description': description,
            'distributions': distribution,
            #'display_name': ['', ['', '', ''],'',''], # ['canonical_name', ["author", "ref", "name-in-ref"], "type status:"]
        }

        if x := row['name']:
            item_title['scientific_name']['author'] = row['_authorship']
            item_title['scientific_name']['full'] = f"{item_title['scientific_name']['canonical']} {x}"
            #item_title['display_name'][1][0] = x

        if x := row['properties']:
            taxon_props = json.loads(x)
            if y := taxon_props.get('reference_name'):
                item_title['ref'] = y
                #item_title['display_name'][1][1] = y

        for u in per_usages:
            if x := u.get('name_in_reference'):
                item_title['name_in_ref'] = x
                #item_title['display_name'][1][2] = x

        for s in type_specimens:
            if x := s.get('use'):
                item_title['type']['use'] = x

            # gathering
            if country := s.get('country'):
                if d := country.get('display'):
                    if c := d.get('en-us'):
                        item_title['type']['gathering']['country'] = c

            if x := s.get('locality'):
                item_title['type']['gathering']['locality'] = x
            if x := s.get('locality_verbatim'):
                item_title['type']['gathering']['locality2'] = x

            if x := s.get('collection_year'):
                item_title['type']['gathering']['year'] = x
            if x := s.get('collection_month'):
                item_title['type']['gathering']['month'] = x
            if x := s.get('collection_day'):
                item_title['type']['gathering']['day'] = x

            if x := s.get('specimens'):
                item_title['type']['specimens'] = x


        # format display string
        #tmp = f"{item_title['scientific_name']}"
        tmp = ''
        if x := item_title['scientific_name']['author']:
            tmp = x
        if x := item_title['ref']:
            tmp = f"{tmp}, {x}"
        if x := item_title['name_in_ref']:
            if tmp[-1] == '.':
                tmp = tmp[:-1] # Berberis aristatoserrulata, ref 最後有一個. => 組起來要拿掉
            tmp = f"{tmp}, {x}."

        voucher = ''
        if x:= item_title['type']['use']:
            voucher = x.capitalize()
        if x := item_title['type']['gathering']['country']:
            voucher = f"{voucher}: {x.upper()}"
        loc = ''
        if x := item_title['type']['gathering']['locality']:
            loc = x
            if x2 := item_title['type']['gathering']['locality2']:
                loc = f'{loc}({x2})'
        if loc:
            voucher = f'{voucher}, {loc}'

        ymd = []
        if x := item_title['type']['gathering']['day']:
            ymd.append(x)
        if x := item_title['type']['gathering']['month']:
            ymd.append(x)
        if x := item_title['type']['gathering']['year']:
            ymd.append(x)
        if ymd:
            voucher = f"{voucher}, {' '.join(ymd)}"

        if x := item_title['type']['gathering']['field_number']:
            vouche = f"{voucher}, {x}"
        #else:
        #    voucher = f"{voucher}, sine coll" # s.n.

        sp = []
        for index, x in enumerate(item_title['type']['specimens']):
            s = x['herbarium']
            prefix = ''
            if index > 0:
                prefix = 'isotype: '

            if an := x.get('accession_number'):
                sp.append(f"{prefix}{s} [{an}]")
            else:
                sp.append(f"{prefix}{s}")

        if len(sp):
            voucher = f"{voucher}. ({'; '.join(sp)})."

        if voucher:
            tmp = f"{tmp} {voucher}"

        # parse name_remark
        full_name = ''
        if name_remark := row['name_remark']:
            soup = BeautifulSoup(name_remark, 'lxml')
            if soup.i:
                name_remark = soup.i.string
                full_name = soup.get_text()
                full_name = full_name.replace(name_remark, '').strip()

        #print('---')
        #print(full_name)
        #print(tmp)
        #print(item_title)
        item_title['name_remark'] = full_name
        item_title['voucher'] = voucher
        item_title['display_name'] = tmp

        data['items'].append({
            'item_title': item_title,
            'status': row['id'],
            'commonNames': common_names,
            'synonyms': synonyms,
            'type_specimens': type_specimens,
            'properties': properties,
            'taicol_taxon_name_id': taicol_name_id,
            'taicol_usage_id': row['id'],
            'updated': row['updated_at'].strftime('%Y-%m-%d %H:%M:%S'),
        })

    return data

class TBIASpecimens(object):

    records = []
    url = ''
    def __init__(self):

        pass

    def fetch_taxon(self, taxon_key):
        self.url = f'https://tbiadata.tw/api/v1/occurrence?isCollection=true&taxonID={taxon_key}&limit=100'
        current_app.logger.debug(f'TBIASpecimens) fetch_taxon: {taxon_key}')
        self.records = []
        res = self.fetch_api(self.url)
        return {
            'is_success': res['is_success'],
            'records': self.records,
        }


    def fetch_api(self, url):
        current_app.logger.debug(f'TBIASpecimens) fetch_api: {url}')
        resp = requests.get(url)
        is_success = False
        try:
            data = resp.json()
            if data['status']['code']!= 200:
                is_success = False
            else:
                self.records += data['data']
                is_success = True

            if next_url := data['links'].get('next'):
                self.fetch_api(next_url)
        except:
            current_app.logger.error('TBIASpecimens) fetch_api error')


        return {
            'is_success': is_success,
            'records': self.records,
        }


    def conv_data(self, data):
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
        records = []
        for i,v in enumerate(data):
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
                '_raw': v,
            })

        return records


def send_email(to, subject, body):
    ses_client = boto3.client(
        'ses',
        region_name=current_app.config['AWS_SES_REGION_NAME'],
        aws_access_key_id=current_app.config['AWS_SES_ACCESS_KEY'],
        aws_secret_access_key=current_app.config['AWS_SES_SECRET_ACCESS_KEY']
    )

    try:
        response = ses_client.send_email(
            Source=current_app.config['AWS_SES_SOURCE'],
            Destination={
                'ToAddresses': [
                    to,
                ],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )

        current_app.logger.info(f"Email sent successfully! Message ID: {response['MessageId']}")
        return response

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        current_app.logger.error(f"Error sending email: {error_code} - {error_message}")
        return None

def create_collection_by_taicol_namespace(user_id, namespace_id):
    url = f"{current_app.config['TAICOL_API']}/biota?namespace_id={namespace_id}&token={current_app.config['TAICOL_TOKEN']}"
    resp = requests.get(url)
    data = resp.json()
    collection = Collection(name=data['title'], source_name=f'taicol:namespace', source_data=data, source_id=namespace_id, user_id=user_id)
    session.add(collection)
    session.commit()

    counter = 0
    for i in data['group']:
        counter += 1
        name = i['name'].replace('<i>', '').replace('</i>', '')
        item = Item(
            collection_id=collection.id,
            description=i['description'],
            distribution=i['distribution'],
            note=i['note'],
            user_id=user_id,
            scientific_name=name,
            source_data=i,
            common_names='|'.join(i['common_names']),
            sort=counter
        )
        session.add(item)
        session.commit()

        for syn in i['synonyms']:
            item_syn = ItemSynonym(item_id=item.id, name=syn['usage_references_text'], ref=f"name_id:{i['name_id']}")
            session.add(item_syn)

        session.commit()

    return collection


def put_publication_by_taicol_namespace(user, namespace_id):
    taicol_api = current_app.config['TAICOL_API']
    email = user.email
    resp = requests.get(f'{taicol_api}/user/namespace?email={email}')
    result = {
        'message': '',
        'is_success': False
    }
    if resp.ok:
        resp_json = resp.json()
        available_namespaces = resp_json.get('namespaces', [])

        if int(namespace_id) in available_namespaces:
            if pub := Publication.query.join(Collection).filter(
                Collection.user_id==user.id,
                Collection.source_id==namespace_id,
                Collection.source_name=='taicol:namespace').scalar(): # exist: do nothing
                current_app.logger.info(f'publication [{pub.id}] already exist')
                result['message'] = 'publication already exists'
                # TODO: sync literatures, groups (Item)

            else: # create new pub
                pub = Publication(title='', author='')
                session.add(pub)
                session.commit()

                c = create_collection_by_taicol_namespace(user.id, namespace_id)
                pub.title = c.name
                pub.author = c.source_data.get('author')
                c.publication_id = pub.id

                for i, v in enumerate(c.source_data['literatures']):
                    pl = PublicationLiterature(publication_id=pub.id, source_id=v['reference_id'], name=v['citation'], sort=i+1)
                    session.add(pl)

                session.commit()
                result['is_success'] = True
                result['publication_id'] = pub.id
                return result
        else:
            result['message'] = 'namespace not available'

    return result


def format_specimen_display(data):
    record_number = data.get('recordNumber', '--')
    recorded_by = data.get('recordedBy', '--')
    catalog_number = data.get('catalogNumber', '--')
    locality = data.get('locality', '--')
    dataset_name = data.get('datasetName', '--') # institudion ID ?
    return f'{locality}, {recorded_by} {record_number} ({dataset_name}:{catalog_number})'
