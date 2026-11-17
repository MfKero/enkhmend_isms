# -*- coding: utf-8 -*-
"""project-data.json-оос docs/*.csv файлуудыг цэгцтэй баганатай үүсгэнэ (Excel-д UTF-8 BOM-той)."""
import csv, html, json, os, re, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mn_terms import mn

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'project-data.json').read_text(encoding='utf-8'))
DOCS = ROOT / 'docs'

LABELS = ['Asset', 'Risk Owner', 'Threat', 'Vulnerability', 'Likelihood', 'Impact', 'Risk Score', 'Risk Level',
          'Potential Consequences', 'Treatment Plan', 'Treatment', 'Related ISO Controls', 'Related Controls',
          'Completion Evidence', 'Техникийн арга хэмжээ хариуцах']


def field(text, key):
    others = [l for l in LABELS if l != key]
    m = re.search(re.escape(key) + r':\s*(.*?)(?=(?:' + '|'.join(re.escape(o) + ':' for o in others) + r')|$)', text, re.S)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''


def note(desc, key):
    text = html.unescape(re.sub('<[^>]+>', '\n', desc))
    m = re.search(re.escape(key) + r':\s*([^\n]+)', text)
    return m.group(1).strip() if m else ''


def write(name, header, rows):
    with open(DOCS / name, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


write('asset-register.csv', ['Код', 'Хөрөнгө', 'Эзэмшигч', 'Ангилал', 'Байршил', 'Эрсдэл', 'Зориулалт'],
      [[a['code'], a['name'], note(a['description'], 'Owner'), note(a['description'], 'Classification'),
        note(a['description'], 'Location'), note(a['description'], 'Risk'), note(a['description'], 'Purpose')]
       for a in DATA['assets']])

rows = []
for r in DATA['risks']:
    d = r['description']
    l = re.search(r'Likelihood:\s*(\d)', d); i = re.search(r'Impact:\s*(\d)', d)
    l, i = (int(l.group(1)) if l else 0), (int(i.group(1)) if i else 0)
    treat = field(d, 'Treatment Plan') or field(d, 'Treatment')
    treat = mn(treat).replace('\n', ' ')
    ctrls = field(d, 'Related ISO Controls') or field(d, 'Related Controls')
    code, _, title = r['name'].partition(' — ')
    rows.append([code, title, field(d, 'Asset').split(' — ')[0], mn(field(d, 'Threat')), mn(field(d, 'Vulnerability')),
                 l, i, l * i, 'High' if l * i >= 15 else 'Medium' if l * i >= 6 else 'Low', treat,
                 ', '.join(re.findall(r'A\.\d+\.\d+', ctrls)), r.get('stage', 'Assessed'), 'Risk Analyst',
                 str(r.get('deadline', '2026-12-16'))[:10]])
write('risk-register.csv', ['Код', 'Эрсдэл', 'Хөрөнгө', 'Аюул (Threat)', 'Эмзэг байдал (Vulnerability)', 'Магадлал (L)',
                            'Нөлөөлөл (I)', 'Оноо (L×I)', 'Түвшин', 'Бууруулах арга хэмжээ', 'ISO хяналт', 'Үе шат',
                            'Эзэн', 'Хугацаа'], rows)

write('controls-soa.csv', ['Хяналт', 'Нэр', 'Хамаарах', 'Odoo дахь хэрэгжилт', 'Төлөв', 'Үлдсэн ажил', 'Хариуцагч', 'Нотолгоо'],
      [[c['code'], mn(c['name']), 'Тийм', mn(c['implementation']), c['status'], mn(c['gap']), c['owner'], mn(c['refs'])]
       for c in DATA['controls']])
print('docs/*.csv дахин үүсгэлээ')
