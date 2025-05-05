import json
from datetime import datetime

from docx import Document
from docx.shared import Pt, Mm, Cm, Inches
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION, WD_ORIENT, WD_SECTION_START
from docx.enum.table import WD_ALIGN_VERTICAL

import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

mysql_conn = MySQLdb.connect(host="mysql", user="root", passwd="example", db="taicol")
mysql_cursor = mysql_conn.cursor()

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

            if x:= v['addFields'].get('description'):
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
    data = {
        'title': '',
        'author': '',
        'literatures': [],
        'items': [],
    }

    mysql_cursor.execute(f'SELECT n.title, u.name FROM my_namespaces n LEFT JOIN users u ON u.id = n.user_id WHERE n.id={namespace_id}')
    result = mysql_cursor.fetchone()
    data['title'] = result[0]
    data['author'] = result[1]

    mysql_cursor.execute(f"SELECT t.name, t._authorship, t.id, u.per_usages, u.type_specimens, u.properties, r.title FROM my_namespace_usages u LEFT JOIN taxon_names t ON u.taxon_name_id = t.id LEFT JOIN `references` r ON r.id = t.reference_id WHERE namespace_id={namespace_id} AND u.status='accepted'")

    rows = mysql_cursor.fetchall()
    for row in rows:
        common_names = []
        synonyms = []
        note = ''
        description = ''
        distribution = ''
        add_fields = {}
        specimens = []
        if x := row[5]:
            props = json.loads(x)
            #print(props)
            if names := props.get('common_names'):
                for n in names:
                    if x := n['name']:
                        common_names.append(x.replace('\u0000', '').strip())

            if x := props.get('note'):
                note = x

            if xlist := props.get('additional_fields'):
                for x in xlist:
                    #description:"特徵描述",diagnosis:"鑑定特徵",distribution:"物種分布",etymology:"語源",habitat:"棲地",substrata:"基質",measurements:"測量",coloration:"顏色",otherExaminedMaterial:"其他引證標本"
                    add_fields[x['field_name']] = x['field_value']

        if x := row[4]:
            sp = json.loads(x)
            for i in sp:
                if sp_list := i.get('specimens'):
                    for j in sp_list:
                        specimens.append(j)

        if x := row[6]:
            if x not in data['literatures']:
                data['literatures'].append(x)

        if x:= row[2]:
            mysql_cursor.execute(f"SELECT ru.id, ru.status, t.name, t._authorship, r.title FROM reference_usages ru LEFT JOIN `references` r ON r.id = ru.reference_id LEFT JOIN taxon_names t ON t.id = ru.taxon_name_id WHERE ru.accepted_taxon_name_id={x} and ru.status != 'accepted'")
            results = mysql_cursor.fetchall()
            sci_name = ''
            ref_title = ''
            for i in results:
                sci_name = i[2]
                if author := i[3]:
                    sci_name = f'{sci_name} {author}'
                if ref := i[4]:
                    ref_title = ref
                synonyms.append([sci_name, ref_title])

        scname = row[0]
        if row[1]:
            scname = f'{scname} {row[1]}'

        data['items'].append({
            'scientificName': scname,
            'status': row[2],
            'commonNames': common_names,
            'addFields': add_fields,
            'note': note,
            'synonyms': synonyms,
            'specimens': specimens,
        })

    return data
