import html,json,re,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mn_terms import mn
from pathlib import Path
from collections import Counter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from PIL import Image as PILImage
from docx import Document
from docx.shared import Inches,Pt,RGBColor,Cm
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables';OUT.mkdir(exist_ok=True)
DATA=json.loads((ROOT/'project-data.json').read_text(encoding='utf-8'))
BACKUP=json.loads((ROOT/'backup-restore-verification.json').read_text())
AUDIT=json.loads((ROOT/'audit-verification.json').read_text(encoding='utf-8'))
RBAC=json.loads((ROOT/'rbac-verification.json').read_text())
EXERCISE=json.loads((ROOT/'incident-exercise.json').read_text(encoding='utf-8'))
_FONTS=[('C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/arialbd.ttf'),
        ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf','/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]
_reg,_bold=next(f for f in _FONTS if os.path.exists(f[0]))
pdfmetrics.registerFont(TTFont('Arial',_reg))
pdfmetrics.registerFont(TTFont('Arial-Bold',_bold))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyMN',fontName='Arial',fontSize=10.2,leading=14.7,spaceAfter=7,textColor=colors.black))
styles.add(ParagraphStyle(name='SmallMN',parent=styles['BodyMN'],fontSize=8.4,leading=11.3,spaceAfter=4))
styles.add(ParagraphStyle(name='TitleMN',fontName='Arial-Bold',fontSize=21,leading=27,spaceAfter=16,textColor=colors.black))
styles.add(ParagraphStyle(name='HeadingMN',fontName='Arial-Bold',fontSize=12,leading=16,spaceBefore=10,spaceAfter=5,textColor=colors.black,keepWithNext=True))
styles.add(ParagraphStyle(name='TableMN',fontName='Arial',fontSize=8.3,leading=11.2,spaceAfter=0))
styles.add(ParagraphStyle(name='TableHeadMN',parent=styles['TableMN'],fontName='Arial-Bold',textColor=colors.white))
W,H=A4;CW=W-96

def esc(s):return html.escape(str(s)).replace('\n','<br/>')
def p(text):return ('p',mn(text))
def h(text):return ('h',mn(text))
def t(headers,rows,widths=None):return ('table',[mn(x) for x in headers],[[mn(x) for x in r] for r in rows],widths)
def im(name,caption,width=CW):return ('image',name,mn(caption),width)
def page(title,*items):return {'title':mn(title),'items':list(items)}
def risk_score(r):
    l=re.search(r'Likelihood:\s*(\d)',r['description']);i=re.search(r'Impact:\s*(\d)',r['description'])
    return (int(l.group(1)) if l else 0,int(i.group(1)) if i else 0)
def section(text,key,nextkeys):
    match=re.search(re.escape(key)+r':\s*(.*?)(?='+'|'.join(re.escape(x)+':' for x in nextkeys)+r'|$)',text,re.S)
    return match.group(1).strip() if match else ''
def asset_notes(a,key):
    text=html.unescape(re.sub('<[^>]+>','\n',a['description']))
    m=re.search(re.escape(key)+r':\s*([^\n]+)',text);return m.group(1).strip() if m else ''

SOURCES=[
('ISO/IEC 27001:2022','https://www.iso.org/standard/27001'),
('Odoo 19 Access rights','https://www.odoo.com/documentation/19.0/applications/general/users/access_rights.html'),
('Odoo 19 Project management','https://www.odoo.com/documentation/19.0/applications/services/project/project_management.html'),
('OCA Helpdesk source','https://github.com/OCA/helpdesk/tree/19.0/helpdesk_mgmt'),
('OCA Audit Log source','https://github.com/OCA/server-tools/tree/19.0/auditlog'),
('Project repository','https://github.com/MfKero/enkhmend_isms')]

pages=[]
pages.append(page('Энхмэнд эмнэлгийн ISMS төсөл',
    p('Odoo Community 19 ашигласан ISO IEC 27001 2022 сургалтын хэрэгжилтийн тайлан'),
    p('F.NSA338 Мэдээллийн аюулгүй байдлын засаглал менежмент'),
    p('2026 оны 11 дүгээр сарын 16'),
    t(['Гишүүний нэр','Оюутны код','Хариуцсан үүрэг'],[['','',''] for _ in range(4)],[.36,.25,.39]),
    h('Тайлангийн зорилго'),
    p('Энхмэнд эмнэлгийн зохиомол кейс дээр хөрөнгө, эрсдэл, хяналтын mapping, incident, RBAC, audit log-ийг Odoo-д хэрэгжүүлсэн үр дүнг нотолгоотой тайлагнана. Бүх жишээ нь сургалтын өгөгдөл бөгөөд бодит өвчтөний мэдээлэл ашиглаагүй.'),
    p('Төлөв: техникийн сургалтын хэрэгжилт болон шалгалт дууссан. Бодлогын баталгаа, бодит байгууллагын хэрэгжилт, багийн гишүүдийн мэдээллийг баг өөрөө баталгаажуулна.'),
    h('Repository'),p('https://github.com/MfKero/enkhmend_isms')))

pages.append(page('Хэрэгжилтийн үр дүн ба тайлангийн бүтэц',
    p('Odoo-ийн enkhmend_isms database-д 10 хөрөнгө, 10 эрсдэл, 25 control болон SoA, 3 бодлогын ноорог, 5 operational identity, incident-ийн 5 шат бий. Эрхийн 38 шалгалт, 5 веб нэвтрэлт, actor-той audit өөрчлөлт, incident workflow, локал backup сэргээх туршилт хийгдсэн.'),
    t(['Шаардлага','Үр дүн','Нотолгоо'],[
        ['Asset Register','10 хөрөнгө','Inventory ба CSV экспорт'],['Risk Assessment','10 task, 1–5 матриц','Risk Register, Project'],
        ['Controls Mapping ба SoA','25 record','Controls and SoA цэс'],['Incident','5 stage, HT00001 симуляц','incident-exercise.json'],
        ['ISMS бодлого','3 ноорог','Odoo болон тусдаа PDF DOCX'],['RBAC','5 үүрэг, 5 account','38 permission checks'],
        ['Audit Log','6 model-ийн дүрэм','audit logs, old/new values'],['Backup','Тусдаа test DB-д сэргээсэн','8 table, 89 attachment hash']],[.28,.31,.41]),
    h('Унших дараалал'),
    p('3–5 Байгууллага ба орчин; 6–7 хөрөнгө; 8–11 эрсдэл; 12–15 mapping ба SoA; 16–17 incident; 18–20 RBAC ба audit; 21 backup; 22–27 бодлогын баримт бичгүүд; 28 дүгнэлт ба эх сурвалж.'),
    p('SoA-ийн Implemented нь зөвхөн тайлбарласан сургалтын хүрээг илэрхийлнэ. Бодит эмнэлэг ISO 27001-ийн бүх шаардлагыг биелүүлсэн эсвэл certification авсан гэсэн мэдэгдэл биш.')))

pages.append(page('Байгууллагын нөхцөл ба хамрах хүрээ',
    h('Энхмэнд эмнэлгийн кейс'),p('Амбулаторийн үзлэг, лабораторийн шинжилгээ, оношилгооны үйлчилгээтэй эмнэлгийг сургалтын кейсээр сонгосон. Өвчтөний болон шинжилгээний мэдээлэлд нууцлал, бүрэн бүтэн байдал, хүртээмжийн шаардлага өндөр гэж үзсэн. Байгууллагын хэмжээ, салбар, ажилтны тоо, бодит системийн архитектурыг зохиож баталгаатай мэтээр оруулаагүй.'),
    t(['Сонирхогч тал','Хүлээлт ба эрсдэл'],[
        ['Өвчтөн','Мэдээлэл зөвхөн шаардлагатай ажилтанд харагдах, буруу өөрчлөгдөхгүй байх'],
        ['Эмч ба лаборатори','Найдвартай, зөв мэдээллийг хэрэгтэй үед ашиглах'],
        ['Бүртгэл ба санхүү','Үйл ажиллагаа тасалдахгүй, төлбөр ба бүртгэл зөв байх'],
        ['Удирдлага','Эрсдэлийн эзэн, нотолгоо, шийдвэр тодорхой байх'],
        ['IT ба нийлүүлэгч','Үүрэг, хандалт, өөрчлөлтийн хариуцлага тодорхой байх']],[.27,.73]),
    h('Хамрагдах хүрээ'),p('10 мэдээллийн хөрөнгө болон тэдгээрийн metadata, ISMS эрсдэлийн task, incident workflow, сургалтын хэрэглэгчийн эрх, сонгосон audit дүрэм хамрагдана. Odoo нь бүртгэл ба нотолгоог удирдах хэрэгсэл.'),
    h('Хамрагдаагүй хүрээ'),p('Бодит HIS/LIS, эмчилгээний шийдвэр, өвчтөний бүрэн өгөгдөл, physical security inspection, production network change, MFA rollout, offsite backup, certification audit хамрагдаагүй. Энэ ялгааг SoA-д үлдсэн ажил хэлбэрээр тэмдэглэсэн.')))

pages.append(page('ISMS засаглал ба модулийн сонголт',
    t(['Clause','Кейс дээрх хэрэгжилт'],[
        ['4 Context','Хамрах хүрээ, талууд, өгөгдөл, эрсдэлийн таамаглал тодорхойлсон'],
        ['5 Leadership','5 operational role; бодлогын албан баталгаа хүлээгдэж байна'],
        ['6 Planning','10 эрсдэл, score, treatment, 25 control-ийн SoA'],
        ['7 Support','Хөрөнгийн owner, баримт бичиг, identity; сургалтын ирц дутуу'],
        ['8 Operation','Бодит Odoo бүртгэл, ACL, workflow, audit rules'],
        ['9 Evaluation','Integration болон HTTP шалгалт; байгууллагын дотоод аудит хийгдээгүй'],
        ['10 Improvement','Симуляцийн lessons learned, treatment backlog, үлдсэн ажил']],[.23,.77]),
    h('Модуль ба ISO холбоо'),
    t(['Модуль','Яагаад сонгосон','Control'],[
        ['Inventory products','Хөрөнгийг owner, ангилал, байршилтай бүртгэх','A.5.9 A.5.12'],
        ['Project','Эрсдэл ба treatment-ийн явц, эзэн, хугацаа','A.5.2 A.8.8'],
        ['OCA Helpdesk','Incident-ийг мэдээлэх, шалгах, хаах','A.5.24–A.5.28'],
        ['Users, groups, ACL, rules','Үүргийн эрхийг ялгах','A.5.15 A.5.16 A.8.3'],
        ['OCA Audit Log','Actor, цаг, өмнөх/дараах утга','A.8.15 A.8.16'],
        ['Custom manual models','SoA ба бодлогыг Odoo-д хөтлөх','A.5.1 болон selected controls']],[.25,.49,.26])))

pages.append(page('Техникийн орчин ба архитектур',
    p('Windows дээр өмнө суусан Odoo Community 19 болон PostgreSQL 16-г ашигласан. Даалгавар Docker эсвэл native суулгалтыг зөвшөөрсөн тул native орчныг сонгосон. Үндсэн database нь enkhmend_isms, хэрэглэгчийн веб хаяг нь localhost:8069. Өмнөх isms_demo орчин нь энэ тайлангийн өгөгдлийн эх үүсвэр биш.'),
    t(['Давхарга','Сургалтын орчин'],[
        ['Хөтөч','Brave-ээр Odoo веб интерфэйс'],['Application','Odoo 19, Inventory, Project, OCA Helpdesk, Audit Log'],
        ['Өгөгдөл','PostgreSQL enkhmend_isms, filestore attachments'],['Governance records','x_enkhmend_control, x_enkhmend_policy'],
        ['Access','5 operational role, тусдаа existing Administrator'],['Evidence','PNG screenshots, CSV, JSON verification, report, slides']],[.25,.75]),
    h('Тохиргооны шийдвэр'),p('OCA модулиудыг Enkhmend-ISMS/addons-д байрлуулж, үндсэн addons_path-ийг хадгалан зам нэмсэн. Odoo application service нь odoo-server-19.0. PostgreSQL_For_Odoo нь database service тул application restart-ийн сонголтоос тусгаарласан. Config backup хийж суулгасан.'),
    h('Нууцын хамгаалалт'),p('Хэрэглэгчийн нууц үг, database credential, dump, filestore backup нь .private/ болон орон нутгийн config-д байна. Git-д орохгүй. Тайлан, screenshot-д нууц үг үзүүлээгүй. Odoo 19-ийн native Windows орчныг сургалтын локал орчин гэж үзнэ.')))

assetsrows=[[a['code'],a['name'],asset_notes(a,'Owner'),asset_notes(a,'Classification'),asset_notes(a,'Location'),asset_notes(a,'Risk')] for a in DATA['assets']]
pages.append(page('Мэдээллийн хөрөнгийн бүртгэл',
    p('Inventory-ийн product model дээр EM-AST-01–10 кодтой 10 хөрөнгө бий. Мэдээллийн санг физик барааны тоо хэмжээгээр хянаагүй. Эзэмшигч, ангилал, байршил, эрсдэлийг internal notes-д хадгалсан.'),
    t(['Код','Хөрөнгө','Эзэмшигч','Ангилал','Байршил','Risk'],assetsrows,[.15,.24,.18,.16,.17,.10]),
    h('Бүртгэлийн чанар'),p('EM-AS5-05 гэж бичигдсэн нэг reference-ийг EM-AST-05 болгож зассан. Код бүр нэг хөрөнгийг танина. Owner нь албан үүргийн нэр бөгөөд бодит ажилтны томилгоо хараахан биш.'),
    h('Ангиллын тайлбар'),p('Restricted нь хамгийн хязгаарлагдмал, Confidential нь зөвшөөрөгдсөн ажилтанд зориулсан мэдээлэл. Ангилал нь техникийн record rule-тэй автоматаар холбогдоогүй. Production-д ангиллын дагуу хандалт, encryption, хадгалалт, устгалын журам нэмнэ.')))
pages.append(page('Хөрөнгийн бодит бүртгэлийн нотолгоо',
    im('02-assets.png','Зураг 1. enkhmend_isms дотор 10 хөрөнгө бүртгэгдсэн жагсаалт.',CW),
    im('03-asset-detail.png','Зураг 2. Өвчтөний мэдээллийн сангийн owner, classification, location, risk metadata.',CW),
    p('Эдгээр зураг нь ажиллаж буй Odoo интерфэйсийн өөрчлөлтгүй screenshot. Бодит өвчтөний өгөгдөл агуулаагүй. Эх PNG файлууд screenshots хавтсанд бий.')))

matrix=[]
for l in range(5,0,-1):
    row=[str(l)]
    for i in range(1,6):
        ids=[re.match(r'EM-R\d+',r['name']).group(0) for r in DATA['risks'] if risk_score(r)==(l,i)]
        row.append(str(l*i)+(' / '+', '.join(ids) if ids else ''))
    matrix.append(row)
pages.append(page('Эрсдэлийн үнэлгээний аргачлал',
    p('Likelihood ба Impact тус бүр 1–5. Risk Score нь үржвэр. 1–5 Low, 6–14 Medium, 15–25 High. Уг үнэлгээ нь сургалтын нөхцөлийн таамаглал бөгөөд бодит эмнэлгийн статистик, vulnerability assessment-ийн дүн биш.'),
    t(['Оноо','Likelihood','Impact'],[['1','Маш ховор','Маш бага'],['2','Ховор','Бага'],['3','Тохиолдож болзошгүй','Дунд'],['4','Магадлал өндөр','Ноцтой'],['5','Маш өндөр эсвэл давтагддаг','Маш ноцтой']],[.13,.43,.44]),
    h('Таван түвшний матриц'),t(['L / I','1','2','3','4','5'],matrix,[.10,.13,.13,.13,.20,.31]),
    h('Үр дүн ба хэрэглээ'),p('Эхний үнэлгээгээр 6 High, 4 Medium эрсдэл гарсан. Treatment хэрэгжээгүй байхад residual оноог таамгаар бууруулаагүй. Project-ийн stage нь ажлын явц, High/Medium/Low нь эрсдэлийн түвшин тул хооронд нь ялгана.')))

for part in range(2):
    items=[]
    for r in DATA['risks'][part*5:(part+1)*5]:
        l,i=risk_score(r)
        threat=section(r['description'],'Threat',['Vulnerability','Likelihood'])
        vuln=section(r['description'],'Vulnerability',['Likelihood','Impact'])
        items += [h(r['name']),p('Аюул (Threat): '+threat),p('Эмзэг байдал (Vulnerability): '+vuln),p(f'Магадлал {l} × Нөлөөлөл {i} = {l*i} оноо, түвшин: '+('High' if l*i>=15 else 'Medium')+'. Эзэн: Risk Analyst. Үе шат: Assessed.')]
    pages.append(page('Эрсдэлийн дэлгэрэнгүй бүртгэл '+str(part+1),*items))

treatrows=[]
for r in DATA['risks']:
    treatment=section(r['description'],'Treatment Plan',['Related ISO Controls','Completion Evidence','Assessment Basis'])
    if not treatment:treatment=section(r['description'],'Treatment',['Related Controls','Likelihood','Assessment Basis'])
    treatment=re.sub(r'\s+',' ',treatment)
    treatrows.append([re.match(r'EM-R\d+',r['name']).group(0),treatment,'Risk Analyst','2026-12-16'])
pages.append(page('Эрсдэлийн treatment төлөвлөгөө',
    p('Бүх эрсдэлийг Assessed шатанд байрлуулж, Risk Analyst-д оноосон. Хугацааг 2026-12-16 гэж сургалтын backlog-д өгсөн. Энэ нь бодит эмнэлгийн баталсан төсөв, үүрэг амлалт биш.'),
    t(['Risk','Төлөвлөсөн арга хэмжээ','Owner','Хугацаа'],treatrows,[.13,.57,.15,.15]),
    p('Completion evidence цугларч, residual үнэлгээг review хийж, эзэмшигч шийдвэрлэсний дараа л Closed болгоно. Backup-ийн локал restore шалгалтын дүнг A.8.13 ба A.5.30-д нэмж баримтжуулсан.')))

for part,(start,end) in enumerate([(0,8),(8,17),(17,25)]):
    rows=[]
    for c in DATA['controls'][start:end]:
        rows.append([c['code']+'\n'+c['name'],c['implementation'],c['status']+'\n'+c['gap']])
    pages.append(page('ISO Controls Mapping '+str(part+1),
        p('Сонгосон Annex A control бүрийг эмнэлгийн кейс, Odoo хэрэгжилт, баталгаажсан хүрээ болон үлдсэн ажлаар холбов. Стандартын бүрэн эхийг орлуулахгүй.'),
        t(['Control','Odoo хэрэгжилт','Төлөв ба үлдсэн ажил'],rows,[.23,.42,.35])))

statuscounts=Counter(c['status'] for c in DATA['controls'])
pages.append(page('Statement of Applicability',
    p('Сонгосон 25 control бүгд энэ кейст хамаарна. Сургалтын техникийн хүрээнд Implemented 4, Partial 17, Planned 4. Энэ нь ISO Annex A-ийн бүх 93 control-ийн бүрэн SoA биш; даалгаврын сонгосон хяналтын хүрээний SoA юм.'),
    t(['Control','Хамаарах','Төлөв','Нотолгоо'],[[c['code'],'Тийм',c['status'],c['refs']] for c in DATA['controls']],[.16,.14,.23,.47]),
    p('Хэрэгжилтийн тайлбар болон хэрэгжээгүй хэсгийн үндэслэлийг өмнөх гурван mapping хуудсанд болон Odoo Controls and SoA form-д дэлгэрүүлсэн. Удирдлага бодит байгууллагад хэрэглэхийн өмнө хяналтуудын сонголт, хамрах хүрээ, exception-ийг батална.')))

pages.append(page('Incident management журам ба туршилт',
    p('HT00001 нь Өвчтөний мэдээлэл рүү сэжигтэй хандалт гэсэн зохиомол ticket. EM-AST-01, EM-R01-тэй холбоотой. High priority, Incident Responder owner-той. Бодит incident биш гэдгийг нэр болон тайлбарт тодорхой бичсэн.'),
    t(['Stage','Шийдвэр ба ажил','Сургалтын шалгалт'],[
        ['Incident','Өртсөн asset, илрүүлсэн цаг, шинж тэмдгийг бүртгэх','Stage сонгогдсоныг HTTP-ээр шалгасан'],
        ['Report','Багт мэдээлж эзэн томилох, priority тогтоох','Responder identity-гаар шилжүүлсэн'],
        ['Investigate','Лог, эрх, цагийг шалгаж нотолгоо хадгалах','Техникийн stage transition шалгасан'],
        ['Resolve','Containment/recovery арга хэмжээ, шалгалт','Бодит containment хийсэн гэж мэдэгдээгүй'],
        ['Close','Review, lessons learned, follow-up','Closed flag ба audit old/new утга батлагдсан']],[.18,.45,.37]),
    h('Нотолгоо ба хязгаар'),p('Таван stage transition-ийг ажиллаж буй веб сервер дээр Responder хэрэглэгчээр гүйцэтгэсэн. Audit болон chatter нь шилжилтийн actor, цагийг хадгалсан. Тайланд үзүүлсэн root cause нь кейсийн таамаглал. Бодит сүлжээ, өвчтөний мэдээлэл, бусдын account-д containment эсвэл restore ажиллагаа хийгээгүй.'),
    h('Дараагийн сайжруулалт'),p('Бодит холбоо барих хариуцагч, escalation, severity ба SLA, evidence custody, close approval-ийг баталж нэмнэ. Одоогийн OCA stage тохиргоо нь зөвхөн нэг алхмаар шилжүүлэх эсвэл resolution заавал бөглүүлэх бүх бизнесийн хоригийг хэрэгжүүлээгүй.')))
pages.append(page('Incident урсгалын бодит нотолгоо',
    im('09-incident-workflow.png','Зураг 3. Incident Report Investigate Resolve Close гэсэн таван Kanban stage.',CW),
    im('10-incident-detail.png','Зураг 4. HT00001 дээр Responder, High priority, Close төлөв болон шилжилтийн мөр харагдана.',CW),
    p('Техникийн workflow simulation дууссан. Энэ screenshot нь эмнэлгийн бодит үйл явдлын шалгалт хийсэн тухай нотолгоо биш.')))

pages.append(page('Үүрэгт суурилсан хандалтын удирдлага',
    t(['Үүрэг','Хөрөнгө','Эрсдэл','Incident','Audit'],[
        ['Viewer','Унших','Унших','Унших','Эрхгүй'],['Asset Officer','Үүсгэх засах','Унших','Унших','Эрхгүй'],
        ['Risk Analyst','Унших','Task удирдах','Унших','Эрхгүй'],['Incident Responder','Унших','Унших','Багийн ticket засах','Эрхгүй'],
        ['ISMS Manager','Үүсгэх засах','Удирдах','Удирдах','Унших']],[.23,.19,.19,.22,.17]),
    h('Хэрэгжилтийн зарчим'),p('Таван role нь res.groups, ACL болон conditional global write guard-аар ялгарсан. To-do module-ийн additive ACL нь Viewer-д санамсаргүй task write олгох эрсдэлийг record rule-ээр хаасан. Өмнөх Administrator хадгалагдсан, operational хэрэглэгчдийн хэнд ч Settings administration олгоогүй.'),
    h('Шалгалтын үр дүн'),p('38 ORM permission check тэнцсэн. Таван хэрэглэгчээр HTTP authentication хийж, 10 asset, 10 risk болон incident харагдсаныг шалгасан. Viewer-ийн бодит write хүсэлт live server дээр AccessError өгсөн. Зөвшөөрөгдсөн Asset Officer, Risk Analyst, Responder write үйлдлүүд амжилттай.'),
    h('Хязгаар'),p('Эрх нь сургалтын product/task/ticket model-ийн хүрээнд. Product-ийн write ACL нь бүх product-д үйлчилж болно. Өвчтөний medical record тусгаарлах row-level загвар, бодит HIS identity integration, MFA хамрагдаагүй. Нэмэлт бүлэг олгох бүрд нийлмэл эрхийг дахин шалгана.')))
pages.append(page('Хэрэглэгч ба Viewer эрхийн нотолгоо',
    im('11-users.png','Зураг 5. Таван synthetic operational identity. Existing Administrator-ийг шүүлтүүрээр хассан.',CW),
    im('12-viewer-permissions.png','Зураг 6. Viewer role, бусад application administration олгоогүй байдал.',CW),
    p('Нууц үгүүд зураг болон тайланд ороогүй. Хэрэглэгчийн үүрэг, тестийн дэлгэрэнгүй үр дүн нь rbac-verification.json болон rbac-http-verification.json-д бий.')))

pages.append(page('Audit Log хэрэгжилт ба нотолгоо',
    p('Full log дүрмүүд product.template, product.product, project.task, helpdesk.ticket, x_enkhmend_control, x_enkhmend_policy model-д идэвхтэй. Сонгосон model-ийн create, write, delete, export-ийг бүртгэнэ. Read болон login event нь эдгээр дүрэмд хамрагдахгүй.'),
    t(['Actor','Model','Шалгасан log ID'],[[e['actor'][1],e['model'],str(e['audit_log_id'])] for e in AUDIT['checks']],[.38,.39,.23]),
    im('08-audit-detail.png','Зураг 7. Responder-ийн Resolve-оос Close руу шилжилтийн old/new утга, actor, HTTP request.',CW),
    p('Audit row-ийг гараар зохиож үүсгээгүй. Хэрэглэгчдийн HTTP write үйлдлээс модуль өөрөө үүсгэсэн. Description-ийг түр өөрчилж шалгасны дараа анхны утгад нь сэргээсэн бөгөөд хоёр өөрчлөлт хоёулаа логтой үлдсэн. DB administrator-аас хамгаалсан immutable log гэж үзэхгүй.')))

pages.append(page('Backup ба сэргээх туршилт',
    p('Үндсэн enkhmend_isms database-ийг pg_dump custom format-аар нөөцөлж, filestore-ийг тусад нь zip болгосон. Үндсэн database-ийг overwrite хийгээгүй. enkhmend_restore_check_20261116 гэсэн тусдаа test database-д pg_restore хийсэн.'),
    t(['Хүснэгт','Эх','Сэргээсэн'],[[name,str(c['source']),str(c['restored'])] for name,c in BACKUP['tables'].items()],[.62,.19,.19]),
    p('Filestore-ийн '+str(BACKUP['filestore_files'])+' файл нөөцлөгдсөн. Store_fname-тэй '+str(BACKUP['attachments_verified'])+' attachment бүрийн SHA-1 checksum сэргээсэн файлтай таарсан. Dump болон filestore zip-ийн SHA-256-ийг verification JSON-д хадгалсан.'),
    p('Локал dump, restore, count/hash pipeline '+str(BACKUP['elapsed_seconds'])+' секунд үргэлжилсэн. Энэ хугацаа нь эмнэлгийн үйлчилгээний батлагдсан RTO биш. Бүрэн restored web login, failover, offsite хадгалалт, retention rotation болон тогтмол recovery rehearsal нэмэлтээр шаардлагатай.'),
    p('Backup файлууд .private/ дотор хадгалагдсан бөгөөд Git-д ороогүй. Нотолгоо: backup-restore-verification.json.')))

for code,policy in DATA['policies'].items():
    for part in range(2):
        items=[p(code+'  · Хувилбар 1.0 · Эзэмшигч: ISMS Manager · Төлөв: ноорог, батлагдаагүй')]
        for title,text in policy['sections'][part*4:(part+1)*4]:items += [h(title),p(text)]
        pages.append(page(policy['title']+' '+str(part+1),*items))

pages.append(page('Дүгнэлт үлдсэн ажил ба эх сурвалж',
    p('Төслийн сургалтын техникийн хүрээнд хөрөнгө, эрсдэл, selected controls/SoA, гурван policy draft, таван identity, workflow ба audit нотолгоо Odoo-д бүрдсэн. Локал backup сэргээх count/hash шалгалт тэнцсэн. Эдгээр үр дүнг байгууллагын бүх хамгаалалт бүрэн хэрэгжсэн гэсэн мэдэгдлээс тусгаарласан.'),
    h('Бодит байгууллагад хэрэглэхийн өмнө'),p('Бодлогыг батлах; ажилтны бодит томилгоо, сургалт, эрхийн тогтмол review; MFA/TLS; HIS/LIS access integration; endpoint хамгаалалт; vulnerability scan; external immutable logging; offsite backup; бизнесийн RTO/RPO ба full recovery exercise; дотоод аудит болон management review шаардлагатай.'),
    h('Багийн мэдээлэл ба хувь нэмэр'),p('Хэрэглэгчийн хүсэлтээр гишүүний нэр, оюутны код, хариуцсан үүргийг хоосон үлдээсэн. Commit-ийн author нь бодит гишүүний хувь нэмрийг автоматаар нотлохгүй. Баг өөрийн гүйцэтгэсэн ажлыг үнэн зөв бөглөж хамгаална.'),
    h('AI хэрэглээ'),p('Codex-оор сургалтын өгөгдөл, ORM тохиргоо, тест, policy draft, тайлан ба танилцуулга бэлтгүүлсэн. Screenshot нь ажиллаж буй Odoo UI-ээс авсан бодит зураг. AI-аар хуурамч Odoo дэлгэц эсвэл audit мөр үүсгээгүй.'),
    h('Эх сурвалж'),*[p(name+'\n'+url) for name,url in SOURCES]))

assert len(pages)==28,len(pages)

def pdf_table(headers,rows,widths):
    if widths is None:widths=[1/len(headers)]*len(headers)
    data=[[Paragraph(esc(x),styles['TableHeadMN']) for x in headers]]+[[Paragraph(esc(x),styles['TableMN']) for x in row] for row in rows]
    table=Table(data,colWidths=[CW*x for x in widths],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#203C56')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F2F6F9')]),
        ('GRID',(0,0),(-1,-1),.45,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return table
def footer(canvas,doc):
    canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#56616B'))
    canvas.drawString(48,24,'Энхмэнд эмнэлэг  ISMS сургалтын төсөл')
    canvas.drawRightString(W-48,24,str(doc.page))
def create_pdf(path,specs):
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=42,title='Энхмэнд эмнэлгийн ISMS төсөл',author='Сургалтын баг')
    story=[]
    for n,spec in enumerate(specs):
        if n:story.append(PageBreak())
        story.append(Paragraph(esc(spec['title']),styles['TitleMN']))
        for item in spec['items']:
            if item[0]=='p':story.append(Paragraph(esc(item[1]),styles['BodyMN']))
            elif item[0]=='h':story.append(Paragraph(esc(item[1]),styles['HeadingMN']))
            elif item[0]=='table':story.extend([pdf_table(item[1],item[2],item[3]),Spacer(1,9)])
            elif item[0]=='image':
                f=ROOT/'screenshots'/item[1]
                iw,ih=PILImage.open(f).size
                width=item[3];height=width*ih/iw
                if height>330:width=width*330/height;height=330
                story.extend([Image(str(f),width=width,height=height),Paragraph(esc(item[2]),styles['SmallMN']),Spacer(1,5)])
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

def style_doc(doc):
    sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(1.6);sec.bottom_margin=Cm(1.6);sec.left_margin=Cm(1.7);sec.right_margin=Cm(1.7)
    for name in ['Normal','Title','Heading 1','Heading 2']:
        s=doc.styles[name];s.font.name='Arial';s.font.color.rgb=RGBColor(0,0,0)
        s._element.get_or_add_rPr().rFonts.set(qn('w:ascii'),'Arial');s._element.rPr.rFonts.set(qn('w:hAnsi'),'Arial')
        for attr in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:
            s._element.rPr.rFonts.attrib.pop(qn('w:'+attr),None)
        for border in list(s._element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    normal=doc.styles['Normal'];normal.font.size=Pt(10);normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.12
    doc.styles['Title'].font.size=Pt(20);doc.styles['Heading 2'].font.size=Pt(11)
    foot=sec.footer.paragraphs[0];foot.text='Энхмэнд эмнэлэг  ISMS сургалтын төсөл    ';foot.style=doc.styles['Normal'];foot.runs[0].font.size=Pt(8)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');foot._p.append(fld)
def create_docx(path,specs):
    doc=Document();style_doc(doc)
    for n,spec in enumerate(specs):
        if n:doc.add_page_break()
        doc.add_paragraph(spec['title'],'Title')
        for item in spec['items']:
            if item[0]=='p':doc.add_paragraph(item[1])
            elif item[0]=='h':doc.add_paragraph(item[1],'Heading 2')
            elif item[0]=='table':
                headers,rows,widths=item[1:];table=doc.add_table(rows=1,cols=len(headers));table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
                for i,text in enumerate(headers):table.rows[0].cells[i].text=str(text)
                for row in rows:
                    cells=table.add_row().cells
                    for i,text in enumerate(row):cells[i].text=str(text)
                for ri,row in enumerate(table.rows):
                    for ci,cell in enumerate(row.cells):
                        cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                        if widths:cell.width=Cm(17.6*widths[ci])
                        tcPr=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
                        for edge in ['top','left','bottom','right']:
                            el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
                        tcPr.append(borders)
                        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'203C56' if ri==0 else 'F2F6F9' if ri%2 else 'FFFFFF');tcPr.append(shade)
                        for para in cell.paragraphs:
                            para.paragraph_format.space_after=Pt(3);para.paragraph_format.space_before=Pt(3)
                            for run in para.runs:run.font.size=Pt(8);run.bold=ri==0;run.font.color.rgb=RGBColor(255,255,255) if ri==0 else RGBColor(0,0,0)
                repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
                doc.add_paragraph('')
            elif item[0]=='image':
                doc.add_picture(str(ROOT/'screenshots'/item[1]),width=Inches(6.65))
                cap=doc.add_paragraph(item[2]);cap.paragraph_format.space_after=Pt(4)
                for run in cap.runs:run.font.size=Pt(8)
    doc.save(path)

create_pdf(OUT/'Enkhmend-ISMS-Report.pdf',pages)
create_docx(OUT/'Enkhmend-ISMS-Report.docx',pages)
for code,policy in DATA['policies'].items():
    specs=[]
    for part in range(2):
        items=[p(code+'  · Хувилбар 1.0 · Эзэмшигч: ISMS Manager · Төлөв: ноорог, батлагдаагүй')]
        for title,text in policy['sections'][part*4:(part+1)*4]:items.extend([h(title),p(text)])
        specs.append(page(policy['title']+' '+str(part+1),*items))
    create_pdf(OUT/(code+'.pdf'),specs);create_docx(OUT/(code+'.docx'),specs)
(ROOT/'report-pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print('Report and three policy documents created as PDF and editable DOCX.')
