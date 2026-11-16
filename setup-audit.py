"""Enable OCA audit rules on the existing Enkhmend training database."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Program Files\Odoo 19.0.20261116\server')
import odoo
from odoo import api
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c',r'C:\Program Files\Odoo 19.0.20261116\server\odoo.conf',
    '-d','enkhmend_isms','--no-http','--logfile',str(ROOT/'audit-setup.log')])
with Registry('enkhmend_isms').cursor() as cr:
    env=api.Environment(cr,odoo.SUPERUSER_ID,{})
    assert env['ir.module.module'].search([('name','=','auditlog')],limit=1).state=='installed'
    rules=[]
    for model,title in [('product.template','Assets'),('product.product','Asset variants'),
                        ('project.task','Risk tasks'),('helpdesk.ticket','Incidents')]:
        model_id=env['ir.model']._get(model).id
        rule=env['auditlog.rule'].search([('model_id','=',model_id)],limit=1)
        vals={'name':'Enkhmend - '+title,'model_id':model_id,'log_type':'full',
            'log_create':True,'log_write':True,'log_unlink':True,'log_read':False,
            'log_export_data':True,'user_ids':[(6,0,[])],'users_to_exclude_ids':[(6,0,[])],
            'fields_to_exclude_ids':[(6,0,[])],'capture_record':True}
        if rule:
            if rule.state=='confirmed': rule.set_to_draft()
            rule.write(vals)
        else: rule=env['auditlog.rule'].create(vals)
        rule.set_to_confirmed()
        rules.append({'id':rule.id,'name':rule.name,'model':model,'state':rule.state,
            'create':rule.log_create,'write':rule.log_write,'delete':rule.log_unlink,
            'read':rule.log_read,'export':rule.log_export_data,'type':rule.log_type})
    cr.commit()
    env.registry.signal_changes()
    (ROOT/'audit-rules.json').write_text(json.dumps(rules,indent=2),encoding='utf-8')
    print('Four full audit rules confirmed. Existing records are preserved.')
