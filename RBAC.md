# Энхмэнд ISMS - хэрэглэгчийн эрх

Тохиргоо: `enkhmend_isms`, Odoo Community 19.

| Үүрэг | Login | Хөрөнгө | Эрсдэл | Incident | Audit Log |
|---|---|---|---|---|---|
| Viewer | viewer@enkhmend.test | Унших | Унших | Унших | Эрхгүй |
| Asset Officer | asset@enkhmend.test | Үүсгэх, засах | Унших | Унших | Эрхгүй |
| Risk Analyst | analyst@enkhmend.test | Унших | Удирдах | Унших | Эрхгүй |
| Incident Responder | responder@enkhmend.test | Унших | Унших | Багийн ticket үүсгэх, засах | Эрхгүй |
| ISMS Manager | manager@enkhmend.test | Үүсгэх, засах | Удирдах | Удирдах | Унших |

Техникийн Administrator хэрэглэгч хэвээр. Дээрх таван operational хэрэглэгч Settings administration эсвэл superuser эрхгүй.

Нууц үгүүд: `.private/users.json`. Энэ хавтас Git-д орохгүй. Бодит эмнэлгийн мэдээлэлтэй системд эдгээр сургалтын identity-г ашиглахгүй.

Нэвтэрсний дараа **Enkhmend ISMS** цэсээр хөрөнгө, эрсдэл, incident руу орно. Менежерт Audit Logs цэс нэмэгдэнэ. Assets, Asset variants, Risk tasks, Incidents, Controls, Policies гэсэн зургаан Full audit дүрэм идэвхтэй. Create/write/delete/export бүртгэнэ; read болон login үйлдэл эдгээр дүрэмд хамрагдахгүй.

`audit-verification.json`: Asset Officer, Risk Analyst, Incident Responder хэрэглэгчдийн вебээр хийсэн бодит өөрчлөлтүүдээс actor, цаг, өмнөх/дараах утгатай audit log үүссэнийг шалгасан үр дүн. Туршилтын дараа description-уудыг анхны утгад нь сэргээсэн; өөрчлөх болон сэргээх хоёр үйлдэл хоёулаа логтой үлдэнэ. Audit мөрийг гараар зохиож үүсгээгүй.

`setup-rbac.py` нь Odoo ORM ашиглан бүлэг, ACL, record rule, меню болон хэрэглэгч үүсгэдэг. `rbac-verification.json` нь бодит унших/засах эрхийн 38 шалгалтын үр дүн. `rbac-http-verification.json` нь ажиллаж буй веб серверээр хийсэн нэвтрэлт, мэдээлэл харах шалгалт.

Эрсдэлийн task-уудыг Risk Analyst, сургалтын incident-ийг Incident Responder-т оноосон. Хэрэглэгч бүрээр шалгахдаа тусдаа private/incognito browser ашиглавал одоогийн Administrator session хэвээр үлдэнэ.

Хязгаар: хөрөнгийн write ACL нь product model-д үйлчилнэ; тусдаа эмнэлгийн medical-record системийн эрхийг удирдахгүй. Ангилал нь одоогоор internal notes дахь шошго. Нэмэлт Odoo бүлэг олговол эрхийг дахин шалгана. Role-ийн write guard нь тусгай operational хэрэглэгчдэд үйлчилж, өмнөх Administrator болон хамааралгүй хэрэглэгчдийн эрхийг өөрчлөхгүй.
