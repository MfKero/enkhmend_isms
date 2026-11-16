# Энхмэнд эмнэлэг ISMS

Odoo Community 19 дээр ISO/IEC 27001:2022-ийн сонгосон шаардлагыг харуулсан сургалтын төсөл. Бодит өвчтөний мэдээлэл ашиглаагүй.

## Хүлээлгэн өгөх файлууд

- [Тайлан PDF, 28 хуудас](deliverables/Enkhmend-ISMS-Report.pdf)
- [Засварлах Word тайлан](deliverables/Enkhmend-ISMS-Report.docx)
- [Танилцуулга, 12 слайд](deliverables/Enkhmend-ISMS-Presentation.pptx)
- [Мэдээллийн аюулгүй байдлын бодлого](deliverables/POL-01.pdf), [Word](deliverables/POL-01.docx)
- [Хандалтын удирдлагын бодлого](deliverables/POL-02.pdf), [Word](deliverables/POL-02.docx)
- [Эрсдэлийг бууруулах төлөвлөгөө](deliverables/POL-03.pdf), [Word](deliverables/POL-03.docx)
- [Хөрөнгө](docs/asset-register.csv), [эрсдэл](docs/risk-register.csv), [25 control ба SoA](docs/controls-soa.csv)

## Бодит хэрэгжилт

Database: `enkhmend_isms`. Веб: `http://localhost:8069`.

| Бүртгэл | Үр дүн |
|---|---|
| Assets | EM-AST-01–10, owner/classification/location/risk metadata |
| Risks | EM-R01–10, Threat/Vulnerability/Treatment, 6 High ба 4 Medium |
| Risk workflow | Identified, Assessed, Treating, Reviewed, Closed гэсэн тусдаа stage |
| Controls ба SoA | 25 сонгосон control: 4 Implemented, 17 Partial, 4 Planned |
| Policies | 3 Draft, approval pending |
| Incident | HT00001 сургалтын simulation, таван stage, Close |
| Access | 5 operational role, 38 ORM test, 5 HTTP login, Viewer write denied |
| Audit | 6 Full model rule, хэрэглэгчийн бодит write-ээс old/new утга |
| Restore | Тусдаа DB, 8 table count, 89 attachment hash таарсан |

SoA нь сонгосон 25 control-ийн хүрээнд. Бүх 93 control-ийн бүрэн үнэлгээ болон certification биш. Бодлогын баталгаа, бодит ажилтны томилгоо, MFA, offsite backup, external immutable log, дотоод аудит зэрэг ажил үлдсэн. Дэлгэрэнгүйг тайлан ба SoA-д тусгасан.

## Одоогийн компьютерт ашиглах

1. Odoo руу нэвтэрч зүүн дээд app menu-ээс **Enkhmend ISMS** сонго.
2. Assets, Risks, Incident Helpdesk, Controls and SoA, ISMS Policies цэсүүдийг ашигла. Manager болон existing Administrator Audit Logs цэсээр орно.
3. Сургалтын таван account-ийн login болон эрхийг [RBAC.md](RBAC.md)-ээс хар. Нууц үг зөвхөн компьютерийн `.private/users.json` дотор байна.
4. Тайлангийн нүүрний дөрвөн хоосон мөрийг баг өөрөө үнэн зөв бөглөнө.

## Windows source ба шалгалт

Хэрэгжүүлсэн орчин: Windows, `C:\Program Files\Odoo 19.0.20261116`, PostgreSQL 16, `odoo-server-19.0` service. Docker ашиглаагүй. `addons/` дотор OCA 19.0 Helpdesk ба Audit Log эх код бий. [THIRD_PARTY.md](THIRD_PARTY.md)-д upstream commit, license байна.

`install-modules.ps1`-ийг Administrator PowerShell-оор ажиллуулахад config backup хийж, одоогийн addons_path-ийг хадгалан custom зам нэмээд хоёр модулийг суулгана. Энэ компьютер дээр аль хэдийн амжилттай ажилласан. Дахин ажиллуулах шаардлагагүй.

Энэ repository нь үндсэн database-ийн dump агуулдаггүй. Хоосон DB-д бүх evidence ID, хэрэглэгчийн password, screenshot-ийг автоматаар сэргээх turnkey image биш. ORM script-үүд байгаа төсөл/баг/10 хөрөнгө/10 эрсдэлийг шалгадаг бөгөөд буруу орчинд таамгаар өөрчлөхөөс өмнө зогсоно. Өөр компьютерт Odoo-ийн native зам, DB нэр, addons_path болон сургалтын суурь өгөгдлийг өөрийн орчинд тохируулна. Source data `project-data.json`, CSV файлуудад байна.

Script-үүдийн зориулалт:

| Файл | Зориулалт |
|---|---|
| `setup-rbac.py` | Бүлэг, ACL, write guard, menu, synthetic users |
| `setup-audit.py` | Эхний дөрвөн Full audit rule |
| `scripts/finish-isms.py` | Control/policy model, menu, 25/3 record, risk stages, нэмэлт хоёр audit rule |
| `verify-rbac-http.py` | Таван live login, register visibility, Viewer write denial |
| `verify-audit-http.py` | Role-оор write хийж audit actor, old/new шалгах, утгыг сэргээх |
| `scripts/exercise-incident.py` | Simulation ticket-ийн таван live stage transition |
| `scripts/backup-restore.py` | pg_dump, filestore zip, тусдаа DB restore ба count/hash шалгах |
| `scripts/verify-final.py` | 10/10/25/3 counts, 6 audit rule, Close ticket, governance ACL |
| `scripts/build-documents.py` | Source JSON, screenshot-оос PDF/DOCX үүсгэх |
| `scripts/build-presentation.mjs` | Bundled Artifact Tool ашигласан PPTX authoring source, runtime зам нь тухайн компьютерт хамаарна |

Native Odoo Python-аар live шалгах жишээ:

```powershell
& 'C:\Program Files\Odoo 19.0.20261116\python\python.exe' .\verify-rbac-http.py
& 'C:\Program Files\Odoo 19.0.20261116\python\python.exe' .\scripts\verify-final.py
```

Setup script-үүдийг сургалтын орчинд ажиллуулна. `setup-rbac.py` synthetic password-уудыг шинэчилж болно. Backup script нь ижил нэртэй restore-check DB байвал overwrite хийхгүй зогсоно. Байгаа test DB-г хэзээ ч үндсэн database гэж андуурч сонгохгүй.

## Нотолгоо

`screenshots/` нь ажиллаж буй Odoo UI-ээс авсан бодит PNG. JSON файлууд нь туршилтын үр дүн. Audit row-ийг гараар зохиож үүсгээгүй. Backup-ийн 12.19 секунд нь локал dump/restore/count/hash pipeline, бизнесийн баталсан RTO биш. Restored web login, production failover болон offsite recovery хийгдээгүй.

`.private/`, `odoo.conf`, password, database dump, filestore backup, log болон Word lock file Git-д орохгүй.

## Багийн бүрэлдэхүүн

| Нэр | Оюутны код | Хариуцсан үүрэг |
|---|---|---|
| | | |
| | | |
| | | |
| | | |

AI тусламжаар тохиргоо, тест, бодлогын ноорог, тайлан, танилцуулгыг бэлтгэсэн. Баг хэрэгжилтээ шалгаж, ойлгож, өөрийн хувь нэмрийг үнэн зөв тэмдэглэн хамгаална.
