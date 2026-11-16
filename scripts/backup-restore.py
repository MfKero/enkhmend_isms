import configparser,hashlib,json,os,shutil,subprocess,time,zipfile
from datetime import datetime,timezone
from pathlib import Path
import psycopg2
from psycopg2 import sql
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'.private';PRIVATE.mkdir(exist_ok=True)
cfg=configparser.ConfigParser(interpolation=None);cfg.read(r'C:\Program Files\Odoo 19.0.20261116\server\odoo.conf')
c=cfg['options'];db='enkhmend_isms';restore='enkhmend_restore_check_20261116'
pg=Path(r'C:\Program Files\Odoo 19.0.20261116\PostgreSQL\bin')
dump=PRIVATE/'enkhmend_isms.dump'; filestore=Path(c['data_dir'])/'filestore'/db
procenv=os.environ.copy();procenv['PGPASSWORD']=c['db_password']
common=['-h',c['db_host'],'-p',c['db_port'],'-U',c['db_user']]
started=time.monotonic()
subprocess.run([str(pg/'pg_dump.exe'),*common,'-Fc','--no-owner','-f',str(dump),db],env=procenv,check=True,capture_output=True)
listing=subprocess.run([str(pg/'pg_restore.exe'),'--list',str(dump)],check=True,capture_output=True,text=True)
assert 'TABLE DATA public product_template' in listing.stdout
archive=PRIVATE/'enkhmend-filestore.zip'
files=list(filestore.rglob('*')) if filestore.exists() else []
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
    for f in files:
        if f.is_file():out.write(f,f.relative_to(filestore))
connargs=dict(host=c['db_host'],port=c['db_port'],user=c['db_user'],password=c['db_password'])
admin=psycopg2.connect(dbname='postgres',**connargs);admin.autocommit=True
with admin.cursor() as cursor:
    cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s',(restore,))
    if cursor.fetchone():raise RuntimeError('Restore-check database already exists; do not overwrite it.')
    cursor.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(sql.Identifier(restore)))
subprocess.run([str(pg/'pg_restore.exe'),*common,'--no-owner','--no-privileges','-d',restore,str(dump)],env=procenv,check=True,capture_output=True)
source=psycopg2.connect(dbname=db,**connargs);target=psycopg2.connect(dbname=restore,**connargs)
counts={}
tables=['product_template','project_task','helpdesk_ticket','res_users','auditlog_rule','auditlog_log','x_enkhmend_control','x_enkhmend_policy']
for table in tables:
    a=source.cursor();b=target.cursor()
    query=sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))
    a.execute(query);b.execute(query);first=a.fetchone()[0];second=b.fetchone()[0]
    assert first==second,(table,first,second);counts[table]={'source':first,'restored':second}
restore_data=PRIVATE/'restore-data';dest=restore_data/'filestore'/restore
dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:z.extractall(dest)
with target.cursor() as cursor:
    cursor.execute('SELECT store_fname,checksum FROM ir_attachment WHERE store_fname IS NOT NULL')
    attachments=cursor.fetchall()
    for name,checksum in attachments:
        file=dest/name
        assert file.is_file(),'Missing restored attachment'
        assert hashlib.sha1(file.read_bytes()).hexdigest()==checksum,'Attachment hash mismatch'
elapsed=round(time.monotonic()-started,2)
out={'source_database':db,'restore_database':restore,'checked_at_utc':datetime.now(timezone.utc).isoformat(),
     'elapsed_seconds':elapsed,'tables':counts,'filestore_files':sum(f.is_file() for f in files),
     'attachments_verified':len(attachments),'database_dump_sha256':hashlib.sha256(dump.read_bytes()).hexdigest(),
     'filestore_zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
     'scope':'Local backup and restore validation. Not offsite backup, business RTO approval, or full disaster recovery.'}
(ROOT/'backup-restore-verification.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
source.close();target.close();admin.close()
print('Backup restored to a separate test database; eight table counts and all filestore attachment hashes verified.')
