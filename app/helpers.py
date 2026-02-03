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

TAIWAN_COUNTIES = {
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
        custom = args.get('custom', '')

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

            # auto add serial number (scientific name) to bold
            sn_pattern = r"^[0-9]+\. $"
            if m := re.match(sn_pattern, t[0]):
                run.bold = True

            if 'italic' in styles or t[1] == 'italic':
                run.italic = True

                if custom and custom == 'italic-to-bold':
                    run.italic = False
                    run.bold = True

            if 'bold' in styles:
                run.bold = True

            if size == 'h2':
                run.font.size = Pt(12)
            elif size == 'h3':
                run.font.size = Pt(11)
            else:
                if size:
                    run.font.size = Pt(int(size))


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

        counter = 0
        for i, v in enumerate(d['items']):
            if str(v['rank_id']) == '34': # only species has sort number
                counter += 1
                title = f"{counter}. {v['scientificName']}"
            else:
                title = v['scientificName']

            biota.add_box(title, {'size': '11', 'custom': 'italic-to-bold'})

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


def generate_pdf(data):
    """Generate a PDF document from namespace data."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Table, TableStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors, fonts
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping
    from io import BytesIO
    from xml.sax.saxutils import escape
    import os

    def sanitize_html(text):
        """Sanitize HTML content for ReportLab compatibility."""
        if not text:
            return ''
        # Convert br tags to self-closing
        text = re.sub(r'<br\s*>', '<br/>', text, flags=re.IGNORECASE)
        # Escape special characters but preserve valid HTML tags
        # ReportLab supports: b, i, u, strike, super, sub, br, a
        return text

    def convert_html_to_custom_fonts(text, base_font='Tinos'):
        """Convert HTML tags to font tags for custom font support.

        Args:
            text: HTML text with <b> and <i> tags
            base_font: Base font family ('Tinos' or 'Serif' for NotoSerifTC)

        Returns:
            Text with <font> tags instead of <b>/<i>
        """
        if not text:
            return ''

        # Map font combinations
        #if base_font == 'Tinos':
        #    fonts_map = {
        #        'regular': 'Tinos-Regular',
        #        'bold': 'Tinos-Bold',
        #        'italic': 'Tinos-Italic',
        #        'bold-italic': 'Tinos-BoldItalic'
        #    }
        #else:  # Serif (NotoSerifTC)
        fonts_map = {
            'regular': 'Serif-Regular',
            'bold': 'Serif-Bold',
            'italic': 'Serif-Italic',  # No italic variant for NotoSerifTC
            'bold-italic': 'Serif-Bold'
        }

        # Handle nested <b><i>...</i></b> or <i><b>...</b></i> -> bold-italic
        text = re.sub(
            r'<b>\s*<i>(.*?)</i>\s*</b>|<i>\s*<b>(.*?)</b>\s*</i>',
            lambda m: f'<font name="{fonts_map["bold-italic"]}">{m.group(1) or m.group(2)}</font>',
            text,
            flags=re.DOTALL
        )

        # Handle remaining <b>...</b> -> bold
        text = re.sub(
            r'<b>(.*?)</b>',
            lambda m: f'<font name="{fonts_map["bold"]}">{m.group(1)}</font>',
            text,
            flags=re.DOTALL
        )

        # Handle remaining <i>...</i> -> italic
        text = re.sub(
            r'<i>(.*?)</i>',
            lambda m: f'<font name="{fonts_map["italic"]}">{m.group(1)}</font>',
            text,
            flags=re.DOTALL
        )

        return text

    # Register regular font
    #font_regular2 = 'app/fonts/tinos/Tinos-Regular.ttf'
    #font_bold2 = 'app/fonts/tinos/Tinos-Bold.ttf'
    #NotoSerifTC-VariableFont_wght.ttf
    custom_fonts = {
        'regular_tc': ['Serif-Regular','app/fonts/NotoSerifTC-Light.ttf'],
        'bold_tc': ['Serif-Bold', 'app/fonts/NotoSerifTC-Bold.ttf'],
        'regular': ['Tinos-Regular','app/fonts/NotoSerif-Regular.ttf'],
        'bold': ['Tinos-Bold', 'app/fonts/Tinos-Bold.ttf'],
        #'italic': ['Tinos-Italic', 'app/fonts/Tinos-Italic.ttf'],
        'italic': ['Serif-Italic', 'app/fonts/NotoSerif-Italic.ttf'],
        'bold-italic': ['Tinos-BoldItalic', 'app/fonts/Tinos-BoldItalic.ttf'],
    }
    for k, v in custom_fonts.items():
        pdfmetrics.registerFont(TTFont(v[0], v[1]))

    # Register font family mappings for bold/italic support in HTML tags
    # not works
    #addMapping('myfamily', 0, 0, 'Tinos-Regular')     # normal
    #addMapping('myfamily', 1, 0, 'Tinos-Bold')        # bold
    #addMapping('myfamily', 0, 1, 'Tinos-Italic')      # italic
    #addMapping('myfamily', 1, 1, 'Tinos-BoldItalic')  # bold-italic

    # Debug code - commented out
    # for (fam, b, i), fontName in fonts.font_index.items():
    #     if fam.lower() == family_to_check.lower():
    #         print(f"  - (Bold={b}, Italic={i}) -> '{fontName}'")
    #print(pdfmetrics.getRegisteredFontNames())

    buffer = BytesIO()

    # We'll use a custom document template to support two-column layout
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

    doc = BaseDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Define frames for single and two-column layouts
    page_width, page_height = letter
    frame_width = page_width - 144  # Total width minus margins
    frame_height = page_height - 90  # Total height minus margins

    # Single column frame
    single_frame = Frame(
        72, 18, frame_width, frame_height,
        id='single_col',
        showBoundary=0
    )

    # Two column frames
    col_width = (frame_width - 20) / 2  # 20 points gap between columns
    left_frame = Frame(
        72, 18, col_width, frame_height,
        id='col_left',
        showBoundary=0
    )
    right_frame = Frame(
        72 + col_width + 20, 18, col_width, frame_height,
        id='col_right',
        showBoundary=0
    )

    # Add page templates
    doc.addPageTemplates([
        PageTemplate(id='SingleCol', frames=[single_frame]),
        PageTemplate(id='TwoCol', frames=[left_frame, right_frame]),
    ])

    # Container for the 'flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=custom_fonts['regular_tc'][0],
        fontSize=12,  # h2 size
        alignment=TA_CENTER,
        spaceAfter=8,
        spaceBefore=0,
    )

    author_style = ParagraphStyle(
        'CustomAuthor',
        parent=styles['Heading2'],
        fontName=custom_fonts['regular_tc'][0],
        fontSize=11,  # h3 size
        alignment=TA_CENTER,
        spaceAfter=8,
        spaceBefore=0,
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName=custom_fonts['regular_tc'][0],
        fontSize=12,  # h3 size
        spaceAfter=4,
        spaceBefore=8,
    )
    category_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName=custom_fonts['bold_tc'][0],
        fontSize=12,  # h3 size
        spaceAfter=4,
        spaceBefore=12,
        alignment=TA_CENTER,
    )
    literature_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName=custom_fonts['regular_tc'][0],
        fontSize=10,  # h3 size
        spaceAfter=4,
        spaceBefore=12,
        alignment=TA_CENTER,
    )
    scientific_name_style = ParagraphStyle(
        'ScientificName',
        parent=styles['Normal'],
        fontName=custom_fonts['regular'][0],  # Tinos-Regular (base font)
        fontSize=10,
        spaceAfter=2,
        spaceBefore=0,
        leading=14,
    )

    body_style = ParagraphStyle(
        'BodyJustify',
        parent=styles['Normal'],
        fontName=custom_fonts['regular_tc'][0], #'Helvetica',  # Use Helvetica for HTML tag support
        alignment=TA_JUSTIFY,
        fontSize=10,
        spaceAfter=2,
        spaceBefore=4,
        leading=14,
        firstLineIndent=14,
    )

    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontName=custom_fonts['regular_tc'][0],
        fontSize=10,
        spaceAfter=2,
        spaceBefore=0,
        leading=14,
    )

    # Add header (single column)
    from reportlab.platypus import NextPageTemplate



    elements.append(NextPageTemplate('SingleCol'))
    elements.append(Paragraph('Biota Taiwanica', title_style))
    elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', normal_style))
    elements.append(PageBreak())

    # Process each namespace
    for idx, d in enumerate(data):
        # Add title and author (single column)
        elements.append(NextPageTemplate('SingleCol'))
        elements.append(Paragraph(d['title'], title_style))
        elements.append(Paragraph(d['author'], author_style))

        # Add item_category and literature section (single column)
        elements.append(Spacer(1, 0.2*inch))
        if cat := d.get('item_category'):
            name = cat[0].get('scientificName', '')
            names = name.split(',')
            # HACK: clean name, (source_data.name_authors)
            simple_name = sanitize_html(names[0]).replace('<i>', '').replace('</i>', '')
            if x := cat[0].get('commonNames'):
                simple_name = f'{simple_name} {x}'
                if sd := cat[0].get('source_data'):
                    if authors := sd.get('name_authors'):
                        simple_name = f'{simple_name} {authors}'
            elements.append(Paragraph(simple_name, category_style))
            if desc := cat[0].get('description'):
                elements.append(Paragraph(sanitize_html(desc), body_style))

        elements.append(Paragraph('LITERATURE', literature_style))
        for lit in d.get('literatures', []):
            if isinstance(lit, dict):
                content = lit.get('content', '')
            else:
                content = str(lit)
            if content:
                elements.append(Paragraph(sanitize_html(content), normal_style))

        # Switch to two-column layout for species list
        elements.append(NextPageTemplate('TwoCol'))
        elements.append(PageBreak())

        # Process items (species) - will flow into two columns
        counter = 0
        for i, v in enumerate(d['items']):
            item_elements = []
            counter += 1
            #sci_name = f"<b>{counter}. </b><i>{sanitize_html(v['scientificName'])}</i>"
            # HACK: split name
            append_sci_name = v['fullScientificName'].split('</i>')[1].strip()
            sci_name = f"<b>{counter}. {sanitize_html(v['scientificName'])}</b> {append_sci_name}"

            # Convert HTML tags to font tags for custom font support
            sci_name_with_fonts = convert_html_to_custom_fonts(sci_name, base_font='Serif')
            item_elements.append(Paragraph(sci_name_with_fonts, scientific_name_style))

            # Common names
            if v.get('commonNames'):
                common = pick_first(v['commonNames'], '|', 'zh')
                if common:
                    normal_right_style = normal_style.clone('NormalRightText', alignment=TA_RIGHT, spaceBefore=12, spaceAfter=6)
                    item_elements.append(Paragraph(sanitize_html(common), normal_right_style))

            # Synonyms
            for syn in v.get('synonyms', []):
                if syn:
                    syn_with_fonts = convert_html_to_custom_fonts(sanitize_html(syn), base_font='Serif')
                    item_elements.append(Paragraph(syn_with_fonts, scientific_name_style))

            # Description
            if desc := v.get('description'):
                item_elements.append(Paragraph(sanitize_html(desc), body_style))

            # Distribution
            if dist := v.get('distribution'):
                item_elements.append(Paragraph(sanitize_html(dist), body_style))

            # Specimens
            print(i, v['specimens'])
            if specimens := v.get('specimens'):
                if specimens and len(specimens):
                    item_elements.append(Spacer(1, 0.1*inch))
                    s = ''
                    for county, sp_list in specimens.items():
                        dist = TAIWAN_COUNTIES.get(county, 'Other').upper()
                        sp_arr = [sanitize_html(x[1]) for x in sp_list]
                        sp_str = '; '.join(sp_arr)
                        s += f'{dist}: {sp_str}. '
                    if s:
                        item_elements.append(Paragraph(s, normal_style))

            # Note
            if note := v.get('note'):
                item_elements.append(Paragraph(sanitize_html(note), body_style))

            # Add all item elements directly without KeepTogether to allow natural flow
            elements.extend(item_elements)
            # Small space between items (matching DOCX spacing)
            elements.append(Spacer(1, 6))

        # Add page break between namespaces (except for the last one)
        if idx < len(data) - 1:
            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)

    # Reset buffer position to beginning for reading
    buffer.seek(0)

    return buffer


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


def put_publication_by_taicol_namespace(user, namespace_id):
    result = {
        'message': '',
        'status': '',
        'data': {},
    }

    if is_ok := check_namespace_available(user.email, namespace_id):
        publication_id = None
        message = ''
        if pub := Publication.query.join(Collection).filter(
            Collection.user_id==user.id,
            Collection.source_id==namespace_id,
            Collection.source_name=='taicol:namespace').scalar(): # exist
            message = f'publication [{pub.id}] already exist'
            publication_id = pub.id
            result['status'] = 'exist'
        else:
            result['status'] = 'new'
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
            publication_id = pl.id

        current_app.logger.info(message)
        result.update({
            'message': message,
            'data': {
                'publication_id': publication_id,
            }
        })
        return result

    return result


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
            sort=counter,
        )
        session.add(item)
        session.commit()

        for syn in i['synonyms']:
            item_syn = ItemSynonym(item_id=item.id, name=syn['usage_references_text'], ref=f"name_id:{i['name_id']}")
            session.add(item_syn)

        session.commit()

    return collection


def sync_collection_by_taicol_namespace(collection):
    """Update existing collection and items with latest data from TaiCOL"""
    namespace_id = collection.source_id
    url = f"{current_app.config['TAICOL_API']}/biota?namespace_id={namespace_id}&token={current_app.config['TAICOL_TOKEN']}"
    resp = requests.get(url)
    data = resp.json()

    # Update collection
    collection.name = data['title']
    collection.source_data = data

    remote_items = [i['name_id'] for i in data['group']]
    # Build existing items lookup by name_id
    existing_items = {}
    counter_del = 0
    counter_new = 0
    counter_edit = 0

    for item in collection.items:
        source_id = item.source_data.get('name_id')
        if item.source_data and source_id:
            existing_items[source_id] = item
            if source_id not in remote_items:
                counter_del += 1
                for syn in item.synonyms:
                    session.delete(syn)
                for spec in item.specimens:
                    session.delete(spec)
                for img in item.images:
                    session.delete(img)
                for dist in item.distributions:
                    session.delete(dist)
                session.delete(item)

    session.commit()
    counter = 0

    for i in data['group']:
        counter += 1
        name = i['name'].replace('<i>', '').replace('</i>', '')
        name_id = i.get('name_id')

        if name_id and name_id in existing_items:
            counter_edit += 1
            # Update existing item
            item = existing_items[name_id]
            item.scientific_name = name
            item.description = i['description']
            item.distribution = i['distribution']
            item.note = i['note']
            item.source_data = i
            item.common_names = '|'.join(i['common_names'])
            item.sort = counter

            # Update synonyms: delete old and create new
            for syn in item.synonyms:
                session.delete(syn)
        else:
            # Create new item
            item = Item(
                collection_id=collection.id,
                description=i['description'],
                distribution=i['distribution'],
                note=i['note'],
                user_id=collection.user_id,
                scientific_name=name,
                source_data=i,
                common_names='|'.join(i['common_names']),
                sort=counter
            )
            session.add(item)
            session.commit()
            counter_new += 1

        # Add synonyms
        for syn in i['synonyms']:
            item_syn = ItemSynonym(item_id=item.id, name=syn['usage_references_text'], ref=f"name_id:{i['name_id']}")
            session.add(item_syn)

    session.commit()
    return {
        'deleted': counter_del,
        'created': counter_new,
        'updated': counter_edit,
    }

def format_specimen_display(data):
    record_number = data.get('recordNumber', '--')
    recorded_by = data.get('recordedBy', '--')
    catalog_number = data.get('catalogNumber', '--')
    locality = data.get('locality', '--')
    dataset_name = data.get('datasetName', '--') # institudion ID ?
    return f'{locality}, {recorded_by} {record_number} ({dataset_name}:{catalog_number})'

def check_namespace_available(email, namespace_id):
    taicol_api = current_app.config['TAICOL_API']
    resp = requests.get(f'{taicol_api}/user/namespace?email={email}')
    if resp.ok:
        resp_json = resp.json()
        available_namespaces = resp_json.get('namespaces', [])
        if int(namespace_id) in available_namespaces:
            return True

    return False
