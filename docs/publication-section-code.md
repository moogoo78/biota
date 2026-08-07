# Publication Section Codes

A stable name for every part of a generated publication, so we can point at one
("`FM-LIT` is too big", "`TX-DIAG` has no data source yet") instead of describing it.

Scope: the journal / preprint layout (`?format=pdf2`, `generate_pdf2()`) and its compact
variant (`?format=pdf3`, `generate_pdf3()`), the content context (`?format=json`,
`generate_json()`), the older PDF (`?format=pdf`, `generate_pdf()`), and the design
mockup `docs/design/biota-journal-article.dc.html`.

PDF3 draws the same sections as PDF2 from the same context, with three deliberate
differences: `FM-TITLE` is hidden (it survives only in the running head, `PG-HEAD-R`),
`FM-TAXON` / `FM-AUTHOR` are centered, and `FM-TAXON` is regular weight instead of bold.
Everything else differs only in metrics (`JOURNAL_LAYOUT_COMPACT`, see
[Layout variants](#layout-variants)), so a PDF2 ✅/⬜ below applies to PDF3 unchanged.

Font weights inside `FM-TAXON`: `<i>` always maps to `Serif-Italic` = NotoSerif-Italic,
a 400-weight face (`fonts_map`, `app/helpers.py:403` — there is no bold-italic entry).
So the upright part has to be 400 too, or the line looks two-toned:

- PDF2 (`taxon_weight: bold`) → `Serif-Bold` (700). The italic name stays 400, so the
  heading is bold only from the authors onward.
- PDF3 (`taxon_weight: regular`) → `Serif-Text` = NotoSerifTC-Regular (400), *not* the
  body face `Serif-Regular` = NotoSerifTC-Light (300), which would render the authors
  and common name lighter than the italic name. On top of that,
  `taxon_authors_font: medium_tc` lifts `FM-TAXON.authors` alone to `Serif-Medium`
  = NotoSerifTC-Medium (500), a step above the name and common name without going bold.

## Code format

```
<ZONE>-<PART>          e.g. FM-TITLE, TX-DESC, KEY-ROW
<ZONE>-<PART>#<n>      for repeating blocks, 1-based:  TX-ITEM#3, KEY-ROW#5
<ZONE>-<PART>.<field>  for a field inside a block:     TX-MAT.region
```

| Zone   | Meaning                                       |
| ------ | --------------------------------------------- |
| `META` | document-level metadata, not printed as prose |
| `PG`   | page furniture (repeats on every page)        |
| `FM`   | front matter, full page width                 |
| `BD`   | body prose sections, two columns              |
| `TX`   | taxon (species) treatment block               |
| `KEY`  | identification key                            |
| `FIG`  | figures / plates                              |
| `AP`   | appendix                                      |
| `FR`   | layout frames & page templates                |

Status column:

- **✅** rendered from real data
- **⚠️** rendered, but mapped from a field that does not really mean this
- **⬜** exists in the design only — no field in the data model yet

## Section registry

### META — document metadata

| Code           | Name       | 中文     | JSON key      | PDF2  | PDF   |
| -------------- | ---------- | -------- | ------------- | ----- | ----- |
| `META-GEN`     | Generator  | 產生器   | `generator`   | ✅ head | ✅ cover |
| `META-TS`      | Timestamp  | 產生時間 | `generatedAt` | ✅ foot | ✅ cover |

Source: `app/helpers.py:372`.

### PG — page furniture

| Code          | Name          | 中文       | Content                                   | PDF2 | PDF | Design |
| ------------- | ------------- | ---------- | ----------------------------------------- | ---- | --- | ------ |
| `PG-HEAD-L`   | Running head, left  | 頁首左 | `META-GEN`                            | ✅   | —   | journal name |
| `PG-HEAD-R`   | Running head, right | 頁首右 | short `FM-TITLE` (truncated at `running_title_max`: 70 in PDF2, 82 in PDF3) | ✅ | — | volume(issue): pages · year |
| `PG-FOOT-L`   | Running foot, left  | 頁尾左 | `META-TS`                             | ✅   | —   | DOI |
| `PG-FOOT-R`   | Running foot, right | 頁尾右 | page number                           | ✅   | —   | short citation |

Source: `app/helpers.py:919` (`draw_furniture`). PDF has no furniture; it prints
`META-GEN` / `META-TS` on a cover page instead (`FM-COVER`, `app/helpers.py:627`).

### FM — front matter (full width, page 1)

| Code           | Name                  | 中文       | JSON key                     | PDF2 | PDF | Design |
| -------------- | --------------------- | ---------- | ---------------------------- | ---- | --- | ------ |
| `FM-COVER`     | Cover page            | 封面頁     | `generator`, `generatedAt`   | —    | ✅  | —      |
| `FM-BADGE`     | Article type / access | 文章類型   | —                            | ⬜   | ⬜  | ✅     |
| `FM-TITLE`     | Article title         | 標題       | `publications[].title`       | ✅ / PDF3 hidden⁰ | ✅  | ✅     |
| `FM-TAXON`     | Taxon heading         | 分類群標題 | `…category.heading`          | ✅ left, bold / PDF3 centered, regular | ✅ centered, bold | ✅ (as genus header) |
| `FM-AUTHOR`    | Authors               | 作者       | `publications[].author`      | ✅ left, bold / PDF3 centered, bold, smaller than `FM-TAXON` | ✅¹ centered, bold | ✅     |
| `FM-AFFIL`     | Affiliations          | 單位       | —                            | ⬜   | ⬜  | ✅     |
| `FM-CORR`      | Corresponding author / editor | 通訊作者 | —                    | ⬜   | ⬜  | ✅     |
| `FM-ABSTRACT`  | Abstract              | 摘要       | `…category.description`      | ⚠️²  | ⚠️² | ✅     |
| `FM-KEYWORDS`  | Keywords              | 關鍵詞     | —                            | ⬜   | ⬜  | ✅     |
| `FM-DATES`     | Received / accepted / published, ZooBank | 日期 | —       | ⬜   | ⬜  | ✅     |
| `FM-LIT`       | LITERATURE list       | 文獻       | `publications[].literatures[]` | ✅ | ✅  | ✅ (as `BD-REF`, at the end) |
| `FM-RULE`      | Rule closing the front block | 分隔線 | —                        | ✅   | —   | ✅     |

⁰ PDF3 sets `show_title: False`, so the title appears only in the running head; the
publication still carries it as the PDF document title.
¹ In PDF, `FM-AUTHOR` is printed inside the `if cat:` branch — a publication with no
`category` silently loses its author line (`app/helpers.py:640`).
² `FM-ABSTRACT` currently reuses the category description; there is no separate
abstract field.

`FM-TAXON` sub-parts — `heading` is the three joined with single spaces, in the order
`{scientificName} {authors} {commonNames}`, skipping whichever are empty
(e.g. `Berberis L. 小檗屬`). Useful when only one piece is wrong:

| Code                | Field                       | JSON key                    |
| ------------------- | --------------------------- | --------------------------- |
| `FM-TAXON.sci`      | scientific name (italic)    | `…category.scientificName`  |
| `FM-TAXON.common`   | common name(s)              | `…category.commonNames`     |
| `FM-TAXON.authors`  | name authors                | `…category.authors`         |

PDF2/PDF3 rebuild the heading from these three parts rather than slicing the joined
string, so each can carry its own font; a heading that does not match the documented
join falls back to italicising the leading name only (`app/helpers.py:1022`).

Source: `app/helpers.py:999` (`build_header`), `app/helpers.py:289` (category build).

### BD — body prose sections (two columns)

| Code             | Name                  | 中文     | JSON key | PDF2 | PDF | Design |
| ---------------- | --------------------- | -------- | -------- | ---- | --- | ------ |
| `BD-INTRO`       | Introduction          | 前言     | —        | ⬜   | ⬜  | ✅     |
| `BD-METHODS`     | Materials and methods | 材料與方法 | —      | ⬜   | ⬜  | ✅     |
| `BD-METHODS.samp`| — Sampling            | 採集     | —        | ⬜   | ⬜  | ✅     |
| `BD-METHODS.morph`| — Morphology         | 形態     | —        | ⬜   | ⬜  | ✅     |
| `BD-METHODS.abbr`| — Abbreviations       | 縮寫     | —        | ⬜   | ⬜  | ✅     |
| `BD-METHODS.mol` | — Molecular data      | 分子資料 | —        | ⬜   | ⬜  | ✅     |
| `BD-TAX`         | Taxonomy heading      | 分類     | —        | ⬜³  | ⬜³ | ✅     |
| `BD-DISC`        | Discussion            | 討論     | —        | ⬜   | ⬜  | ✅     |
| `BD-ACK`         | Acknowledgements      | 誌謝     | —        | ⬜   | ⬜  | ✅     |
| `BD-REF`         | References            | 參考文獻 | see `FM-LIT` | — | — | ✅     |

³ The treatments (`TX-ITEM`) start directly, with no "Taxonomy" heading above them.

### TX — taxon treatment (repeats per species: `TX-ITEM#n`)

| Code         | Name                | 中文     | JSON key (`publications[].items[]`) | PDF2 | PDF | Design |
| ------------ | ------------------- | -------- | ----------------------------------- | ---- | --- | ------ |
| `TX-NUM`     | Item number         | 編號     | `number`                            | ✅   | ✅  | —      |
| `TX-NAME`    | Scientific name     | 學名     | `scientificName` + `nameSuffix`     | ✅   | ✅  | ✅     |
| `TX-COMMON`  | Common name         | 俗名     | `commonName`                        | ✅   | ✅  | ✅     |
| `TX-SYN`     | Synonyms            | 異名     | `synonyms[]`                        | ✅   | ✅  | —      |
| `TX-TYPE`    | Type material       | 模式標本 | —                                   | ⬜⁴  | ⬜⁴ | ✅     |
| `TX-DIAG`    | Diagnosis           | 鑑別特徵 | —                                   | ⬜   | ⬜  | ✅     |
| `TX-DESC`    | Description         | 描述     | `description`                       | ✅   | ✅  | ✅     |
| `TX-ETYM`    | Etymology           | 命名由來 | —                                   | ⬜   | ⬜  | ✅     |
| `TX-DIST`    | Distribution        | 分布     | `distribution`                      | ✅⁵  | ✅  | ✅     |
| `TX-MAT`     | Material examined   | 檢視標本 | `specimens[]`                       | ✅⁵  | ✅  | ✅     |
| `TX-NOTE`    | Note                | 備註     | `note`                              | ✅⁵  | ✅  | —      |

⁴ Type specimens are folded into `TX-MAT`; there is no separate type-material block.
⁵ PDF2 prefixes these with a bold run-in label (`Distribution.`, `Material examined.`,
`Note.`); PDF prints the text with no label.

`TX-MAT` sub-parts, one group per county:

| Code             | Field                              | JSON key                 |
| ---------------- | ---------------------------------- | ------------------------ |
| `TX-MAT.county`  | county name as stored              | `specimens[].county`     |
| `TX-MAT.region`  | uppercase region label printed before the records | `specimens[].region` (from `TAIWAN_COUNTIES`, `app/helpers.py:34`) |
| `TX-MAT.records` | specimen strings, joined with `; ` | `specimens[].records[]`  |

Source: `app/helpers.py:1031` (`build_body`), `app/helpers.py:356` (item build).

### KEY — identification key (repeats per key: `KEY#n`)

| Code         | Name           | 中文     | JSON key (`publications[].keys[]`) | PDF2 | PDF | Design |
| ------------ | -------------- | -------- | ---------------------------------- | ---- | --- | ------ |
| `KEY-TITLE`  | Key heading    | 檢索表標題 | `title`                          | ✅   | ✅  | ✅     |
| `KEY-ROW`    | Couplet row    | 檢索項    | `entries[]`                       | ✅   | ✅  | ✅     |
| `KEY-ROW.no` | Lead number    | 編號     | `entries[].number`                 | ✅   | ✅  | ✅     |
| `KEY-ROW.txt`| Lead text      | 敘述     | `entries[].description`            | ✅   | ✅  | ✅     |
| `KEY-ROW.res`| Result         | 結果     | `entries[].result` / `.resultType` | ✅   | ✅  | ✅     |
| `KEY-ROW.ind`| Indent level   | 縮排     | `entries[].indentLevel`            | ✅   | ✅  | ✅     |

`resultType` is `item` (a species name, italicised) or `couplet` (a number to jump to);
see `app/helpers.py:310`.

Placement differs between renderers, worth naming when reporting a bug:

- **PDF2** — keys come *after* all `TX-ITEM` blocks, in the columns, as a bordered
  table, heading `檢索表 Key: <title>` (`app/helpers.py:1066`).
- **PDF** — keys come *before* the items, in the single-column front section, as
  indented paragraphs, heading `檢索表: <title>` (`app/helpers.py:653`).

### FIG / AP — not rendered

| Code          | Name                   | 中文       | Design element              | Status |
| ------------- | ---------------------- | ---------- | --------------------------- | ------ |
| `FIG-HABITAT` | Habitat figure         | 生育地照片 | `#fig-habitat` + caption    | ⬜     |
| `FIG-PLATE`   | Habitus / genitalia plate per taxon | 圖版 | `#plate-*` + caption | ⬜ |
| `AP-TABLE`    | Appendix specimen table | 標本資料表 | Appendix 1 table (Voucher / Taxon / Locality / Elev. / Date / Dep. / GenBank) | ⬜ |
| `AP-NOTE`     | Appendix footnote      | 附錄註     | HT/PT abbreviation note     | ⬜     |

Both PDF renderers intentionally skip the image slots and the appendix table.

### FR — frames and page templates (PDF2)

Names here are the actual ReportLab ids, so they can be quoted directly in a layout bug.

| Code           | ReportLab id      | Covers                                            |
| -------------- | ----------------- | ------------------------------------------------- |
| `FR-HEAD`      | `head{idx}`       | the `FM-*` block, full width, top of page 1        |
| `FR-FIRST-L`   | `first_left{idx}` | left column on page 1, below `FR-HEAD`             |
| `FR-FIRST-R`   | `first_right{idx}`| right column on page 1                             |
| `FR-COL-L`     | `col_left`        | left column, pages 2+                              |
| `FR-COL-R`     | `col_right`       | right column, pages 2+                             |
| `PT-HEAD`      | `Head{idx}`       | page template for the first page of publication *idx* |
| `PT-TWOCOL`    | `TwoCol`          | page template for every following page             |

Fallback: if `FR-HEAD` would leave less than `MIN_BODY_HEIGHT` (140 pt) for the
columns, the front matter takes a page of its own and the body starts on the next page
(`app/helpers.py:1128`).

## Layout variants

Both journal renderers call `build_journal_pdf(data, layout)`; the `layout` dict holds
every page dimension, font size and spacing, so a variant only overrides numbers.
Type entries are `(fontSize, leading)`; `space` scales every `spaceBefore` /
`spaceAfter` in the styles.

| Metric              | `JOURNAL_LAYOUT` (PDF2) | `JOURNAL_LAYOUT_COMPACT` (PDF3) |
| ------------------- | ----------------------- | ------------------------------- |
| `show_title` (`FM-TITLE`) | `True`            | `False` — hidden                |
| `taxon_align` (`FM-TAXON`) | `left`           | `center`                        |
| `taxon_weight` (`FM-TAXON`) | `bold` → Serif-Bold (700) | `regular` → Serif-Text (400) |
| `taxon_authors_font` (`FM-TAXON.authors`) | `None` — same as heading | `medium_tc` → Serif-Medium (500) |
| `author_align` (`FM-AUTHOR`) | `left`         | `center`                        |
| page margin         | 18 mm                   | 15 mm                           |
| head / foot reserve | 30 / 24 pt              | 26 / 20 pt                      |
| column gap          | 20 pt                   | 16 pt                           |
| `min_body_height`   | 140 pt                  | 120 pt                          |
| running head / foot | 8.5 / 8 pt              | 7.5 / 7 pt                      |
| `FM-TITLE`          | 21 / 27                 | 16.5 / 21                       |
| `FM-TAXON`          | 14 / 20                 | 13.5 / 18                       |
| `FM-AUTHOR`         | 11.2 / 17               | 9.5 / 13.5 — under `FM-TAXON`   |
| `FM-ABSTRACT`       | 10.1 / 17               | 8.8 / 13.6                      |
| `FM-LIT` entry      | 9.4 / 15                | 8.2 / 12                        |
| `TX-NAME`           | 11.3 / 15               | 9.6 / 12.8                      |
| `TX-COMMON`         | 9.8 / 14                | 8.4 / 11.6                      |
| `TX-SYN`            | 9.8 / 14                | 8.4 / 11.6                      |
| `TX-DESC` and body  | 10.9 / 17.6             | 9.2 / 13.8                      |
| `KEY-ROW`           | 10.2 / 15               | 8.8 / 12.4                      |
| section heading     | 12.4 / 16               | 10.4 / 13.5                     |
| `space` multiplier  | 1.0                     | 0.8                             |
| hanging indent      | 10.5 pt                 | 9 pt                            |
| key indent / number column / row padding | 10 / 15 / 5 pt | 8 / 13 / 3.5 pt      |

Defined at `app/helpers.py:759`; the renderer is `app/helpers.py:848`.

Geometry for PDF2: A4, 18 mm margins, 30 pt head reserve, 24 pt foot reserve, 20 pt
column gap.

## Annotated context (JSONC)

The shape returned by `generate_json()` / `?format=json`, with the code for each part.

```jsonc
{
  "generator":   "Biota Taiwanica",     // META-GEN  → PG-HEAD-L
  "generatedAt": "2026-08-07 14:09",    // META-TS   → PG-FOOT-L
  "publications": [
    {
      "title":  "…",                    // FM-TITLE  → PG-HEAD-R (truncated)
      "author": "…",                    // FM-AUTHOR
      "category": {                     // FM-TAXON
        "scientificName": "…",          // FM-TAXON.sci
        "commonNames":    "…",          // FM-TAXON.common
        "authors":        "…",          // FM-TAXON.authors
        "heading":        "…",          // FM-TAXON  = "{scientificName} {authors} {commonNames}"
        "description":    "…"           // FM-ABSTRACT
      },
      "literatures": ["…"],             // FM-LIT
      "keys": [                         // KEY#n
        {
          "title": "…",                 // KEY-TITLE
          "entries": [                  // KEY-ROW#n
            {
              "number":      "1",       // KEY-ROW.no
              "indentLevel": 0,         // KEY-ROW.ind
              "description": "…",       // KEY-ROW.txt
              "result":      "…",       // KEY-ROW.res
              "resultType":  "item"     // KEY-ROW.res  ("item" | "couplet")
            }
          ]
        }
      ],
      "items": [                        // TX-ITEM#n
        {
          "number":              1,     // TX-NUM
          "scientificName":      "…",   // TX-NAME
          "nameSuffix":          "…",   // TX-NAME  (author/ref after </i>)
          "fullScientificName":  "…",   //          (raw, not printed)
          "rankId":              "…",   //          (not printed)
          "commonName":          "…",   // TX-COMMON
          "synonyms":            ["…"], // TX-SYN
          "description":         "…",   // TX-DESC
          "distribution":        "…",   // TX-DIST
          "specimens": [                // TX-MAT
            {
              "county":  "…",           // TX-MAT.county
              "region":  "…",           // TX-MAT.region
              "records": ["…"]          // TX-MAT.records
            }
          ],
          "note": "…"                   // TX-NOTE
        }
      ]
    }
  ]
}
```

## Proposed keys for the ⬜ sections

Not implemented — listed so the codes already have a landing place if we add them,
following the same camelCase, presentation-free style.

```jsonc
{
  "publications": [
    {
      "articleType":  "Research Article · 研究論文",  // FM-BADGE
      "license":      "Open Access · CC BY 4.0",     // FM-BADGE
      "affiliations": ["…"],                          // FM-AFFIL
      "correspondence": { "author": "…", "email": "…", "editor": "…" }, // FM-CORR
      "abstract":     "…",                            // FM-ABSTRACT (own field)
      "keywords":     ["…"],                          // FM-KEYWORDS
      "dates": { "received": "…", "accepted": "…", "published": "…", "zoobank": "…" }, // FM-DATES
      "sections": [                                   // BD-INTRO / BD-METHODS / BD-DISC / BD-ACK
        { "code": "BD-INTRO", "heading": "Introduction", "body": "…",
          "subsections": [ { "code": "BD-METHODS.samp", "heading": "Sampling", "body": "…" } ] }
      ],
      "figures": [                                    // FIG-HABITAT / FIG-PLATE
        { "code": "FIG-HABITAT", "src": "…", "caption": "…" }
      ],
      "appendix": {                                   // AP-TABLE / AP-NOTE
        "heading": "Appendix 1", "intro": "…",
        "columns": ["Voucher", "Taxon", "Locality", "Elev. (m)", "Date", "Dep.", "GenBank"],
        "rows": [["…"]], "note": "…"
      },
      "items": [
        { "typeMaterial": "…",   // TX-TYPE
          "diagnosis":    "…",   // TX-DIAG
          "etymology":    "…" }  // TX-ETYM
      ]
    }
  ]
}
```

## Where each code lives in the code

| Area                | File                                             |
| ------------------- | ------------------------------------------------ |
| `META-*`, all JSON keys | `app/helpers.py:247` `generate_json()`        |
| Layout metrics      | `app/helpers.py:759` `JOURNAL_LAYOUT` / `JOURNAL_LAYOUT_COMPACT` |
| PDF2 / PDF3 renderer| `app/helpers.py:848` `build_journal_pdf()`        |
| PDF2 / PDF3 `PG-*`  | `draw_furniture()` inside the renderer            |
| PDF2 / PDF3 `FM-*`  | `build_header()` inside the renderer              |
| PDF2 / PDF3 `TX-*`, `KEY-*` | `build_body()` inside the renderer        |
| PDF (older layout)  | `app/helpers.py:456` `generate_pdf()`             |
| Format routing      | `app/blueprints/publication.py:476` (`docx` / `pdf` / `pdf2` / `pdf3` / `json`) |
| Download buttons    | `app/templates/_inc-publication-main-preview.html:100` |
| Design reference    | `docs/design/biota-journal-article.dc.html` (extracted from `Biota Journal PDF Layout.zip`, which is gitignored — the 10 MB habitat photo is not committed, so that one image slot renders as a placeholder) |
