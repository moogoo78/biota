import json
from datetime import datetime

from flask import g
from docx import Document
from docx.shared import Pt, Mm, Cm, Inches
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION, WD_ORIENT, WD_SECTION_START
from docx.enum.table import WD_ALIGN_VERTICAL
import yaml

from bs4 import BeautifulSoup

#import pymysql
#pymysql.install_as_MySQLdb()
#import MySQLdb

#mysql_conn = MySQLdb.connect(host="mysql", user="root", passwd="example", db="taicol")
#mysql_cursor = mysql_conn.cursor()

import pymysql.cursors

def get_db_connection():
    """Opens a new database connection if there is none for the current context."""
    if 'db' not in g:
        g.db = pymysql.connect(host='mysql',
                                 user='root',
                                 password='example',
                                 database='taicol',
                                 cursorclass=pymysql.cursors.DictCursor)
    return g.db

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

    def add_content(self, title, size='text', align=''):
        p = self.doc.add_paragraph()
        if align == 'center':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run = p.add_run(title)
        if 'h' in size:
            run.bold = True

        if size == 'h2':
            run.font.size = Pt(14)
        elif size == 'h3':
            run.font.size = Pt(12)

    def add_list(self, data):
        p = self.doc.add_paragraph()
        for x in data:
            p.add_run(x + '\n')


def generate_docx(data):

    biota = BiotaPrint()

    # default section
    biota.add_content('Biota Taiwanica', 'h3')
    biota.add_content(f'generated: {datetime.now()}')
    biota.doc.add_page_break()

    for idx, d in enumerate(data):
        section = biota.create_column_section(1)
        biota.add_content(d['title'], 'h2', 'center')
        biota.add_content(d['author'], 'h3', 'center')
        biota.add_content('LITERATURE', 'h3')
        biota.add_list(d['literatures'])

        section = biota.create_column_section(2)
        for i, v in enumerate(d['items']):
            #print(i, v)
            s = f"{int(i+1)}. {v['scientificName']}"
            if len(v['commonNames']):
                s += ', '.join(v['commonNames'])
            biota.add_content(s)

            biota.add_content('SYNONYMS', 'h3')
            syns = []
            for x in v['synonyms']:
                s = x[0]
                if s[1]:
                    s = f'{x[0]} [{x[1]}]'
                syns.append(s)
            biota.add_list(syns)

            '''
            if len(v['synonyms']):
                p_synonyms = doc.add_paragraph()
                for j in v['synonyms']:
                    r1 = p_synonyms.add_run(j[0])
                    r1.italic = True
                    if j[1]:
                        p_synonyms.add_run(f' {j[1]}')

            '''
            if x := v['addFields'].get('description'):
                biota.add_content('DESCRIPTION', 'h3')
                biota.add_content(x)

            if x:= v['addFields'].get('distribution'):
                biota.add_content('DISTRIBUTION', 'h3')
                biota.add_content(x)

            if len(v['specimens']):
                biota.add_content('SPECIMENS', 'h3')
                sps = []
                for x in v['specimens']:
                    s = ''
                    if y := x.get('herbarium'):
                        s = y
                    if y := x.get('accession_number'):
                        s = f'{s}:{y}'
                    sps.append(s)
                biota.add_list(sps)

            if x:= v['note']:
                biota.add_content('NOTE', 'h3')
                biota.add_content(x)

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
    literature_sql = f'SELECT a.author, a.short_author, a.content FROM import_checklist_logs c LEFT JOIN api_citations a ON FIND_IN_SET(a.reference_id, c.included_references) > 0 WHERE c.namespace_id = {namespace_id}'
    mysql_cursor.execute(literature_sql)
    rows = mysql_cursor.fetchall()
    for r in rows:
        data['literatures'].append({'author': r['author'], 'short_author': r['short_author'], 'content': r['content']})

    mysql_cursor.execute(f'SELECT n.title, u.name FROM my_namespaces n LEFT JOIN users u ON u.id = n.user_id WHERE n.id={namespace_id}')
    result = mysql_cursor.fetchone()
    data['title'] = result['title']
    data['author'] = result['name']

    mysql_cursor.execute(f"SELECT t.name, t._authorship, t.id, u.per_usages, u.type_specimens, u.properties, r.title, u.id, t.properties, u.name_remark, u.group FROM my_namespace_usages u LEFT JOIN taxon_names t ON u.taxon_name_id = t.id LEFT JOIN `references` r ON r.id = t.reference_id WHERE namespace_id={namespace_id} AND u.status='accepted' ORDER by `order`")

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
        taicol_name_id = None

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
            # taicol_name_id = x
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
            item_title['scientific_name']['author'] = x
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
        })

    return data
