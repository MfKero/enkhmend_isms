import json,sys,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'C:\Program Files\Odoo 19.0.20261116\server')
import odoo
from odoo import api
from odoo.modules.registry import Registry
from odoo.exceptions import AccessError
odoo.tools.config.parse_config(['-c',r'C:\Program Files\Odoo 19.0.20261116\server\odoo.conf','-d','enkhmend_isms','--no-http','--logfile',str(ROOT/'final-verification.log')])
with Registry('enkhmend_isms').cursor() as cr:
    env=api.Environment(cr,odoo.SUPERUSER_ID,{})
    counts={'assets':env['product.template'].search_count([('default_code','=like','EM-AST-%')]),'risks':env['project.task'].search_count([('name','=like','EM-R%')]),'controls':env['x_enkhmend_control'].search_count([]),'policies':env['x_enkhmend_policy'].search_count([])}
    assert counts=={'assets':10,'risks':10,'controls':25,'policies':3},counts
    rules=env['auditlog.rule'].search([('state','=','confirmed')]);assert len(rules)==6
    export=[]
    for rule in rules:
        assert rule.log_type=='full' and rule.log_create and rule.log_write and rule.log_unlink and rule.log_export_data
        export.append({'id':rule.id,'name':rule.name,'model':rule.model_id.model,'state':rule.state,'create':rule.log_create,'write':rule.log_write,'delete':rule.log_unlink,'export':rule.log_export_data,'read':rule.log_read,'type':rule.log_type})
    (ROOT/'audit-rules.json').write_text(json.dumps(export,ensure_ascii=False,indent=2),encoding='utf-8')
    risks=env['project.task'].search([('name','=like','EM-R%')]);assert set(risks.mapped('stage_id.name'))=={'Assessed'}
    ticket=env['helpdesk.ticket'].search([('name','ilike','ТУРШИЛТ')],limit=1);assert ticket.stage_id.name=='Close' and ticket.stage_id.closed
    creds=json.loads((ROOT/'.private/users.json').read_text(encoding='utf-8'))
    tests=[]
    for role,cred in creds.items():
        user=env['res.users'].search([('login','=',cred['login'])],limit=1)
        assert user and not user.has_group('base.group_system')
        for model,count in [('x_enkhmend_control',25),('x_enkhmend_policy',3)]:
            assert env[model].with_user(user).search_count([])==count
            try:env[model].with_user(user).check_access('write');allowed=True
            except AccessError:allowed=False
            assert allowed==(role=='manager'),(role,model,allowed)
            tests.append({'role':role,'model':model,'read_count':count,'write_allowed':allowed})
    data=json.loads((ROOT/'project-data.json').read_text(encoding='utf-8'))
    fields=['x_code','x_name','x_implementation','x_status','x_evidence','x_owner','x_refs']
    controls=env['x_enkhmend_control'].search([],order='x_code')
    with (ROOT/'docs/controls-soa.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['Control','Description','Implementation','Status','Remaining Work','Owner','Evidence']);w.writerows([[c[k] for k in fields] for c in controls])
    result={'counts':counts,'audit_rules':6,'risk_stage':'Assessed','incident_stage':'Close','governance_permissions':tests,'status':'pass'}
    (ROOT/'final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: 10 assets, 10 risks, 25 controls, 3 policies, 6 full audit rules, closed simulation, ten governance ACL checks.')
