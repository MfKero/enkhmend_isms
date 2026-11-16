import csv,json,re,sys
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,r'C:\Program Files\Odoo 19.0.20261116\server')
import odoo
from odoo import api
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c',r'C:\Program Files\Odoo 19.0.20261116\server\odoo.conf','-d','enkhmend_isms','--no-http','--logfile',str(ROOT/'completion.log')])

DATA=json.loads((ROOT/'project-data.json').read_text(encoding='utf-8'))
CONTROLS=[tuple(c[k] for k in ['code','name','implementation','status','gap','owner','refs']) for c in DATA['controls']]
POLICIES={k:(v['name'],v['title'],v['sections']) for k,v in DATA['policies'].items()}

def plain(value):
    if not value:return ''
    try:return html.fromstring(value).text_content()
    except Exception:return value

with Registry('enkhmend_isms').cursor() as cr:
    env=api.Environment(cr,odoo.SUPERUSER_ID,{})
    def manual_model(model,label,fields):
        rec=env['ir.model'].search([('model','=',model)],limit=1)
        if not rec:rec=env['ir.model'].create({'name':label,'model':model,'state':'manual'})
        missing=[]
        for name,title,typ in fields:
            if not env['ir.model.fields'].search_count([('model_id','=',rec.id),('name','=',name)]):
                missing.append({'model_id':rec.id,'name':name,'field_description':title,'ttype':typ,'state':'manual'})
        if missing:env['ir.model.fields'].create(missing)
        for role,write in [('viewer',False),('manager',True)]:
            group=env.ref('enkhmend_security.group_'+role)
            acl=env['ir.model.access'].search([('model_id','=',rec.id),('group_id','=',group.id)],limit=1)
            vals={'name':label+' '+role,'model_id':rec.id,'group_id':group.id,
                  'perm_read':True,'perm_write':write,'perm_create':write,'perm_unlink':False}
            if acl:acl.write(vals)
            else:env['ir.model.access'].create(vals)
        return rec
    control_model=manual_model('x_enkhmend_control','Enkhmend Controls and SoA',[
        ('x_code','Annex A Control','char'),('x_implementation','Odoo Implementation','text'),
        ('x_status','Implementation Status','char'),('x_evidence','Evidence and Remaining Work','text'),
        ('x_owner','Owner Role','char'),('x_refs','Linked Evidence','char'),('x_applicable','Applicable','boolean')])
    doc_model=manual_model('x_enkhmend_policy','Enkhmend ISMS Policies',[
        ('x_code','Document Code','char'),('x_version','Version','char'),('x_status','Approval Status','char'),
        ('x_owner','Owner','char'),('x_body','Policy Text','html')])
    def menu_view(model,title,columns,form_fields,sequence):
        viewmodel=env['ir.ui.view']
        views={}
        for typ,arch in [('list','<list>'+''.join('<field name="'+f+'"/>' for f in columns)+'</list>'),
                         ('form','<form><sheet><group>'+''.join('<field name="'+f+'"/>' for f in form_fields)+'</group></sheet></form>')]:
            name=model+'.'+typ
            view=viewmodel.search([('name','=',name)],limit=1)
            if not view:view=viewmodel.create({'name':name,'model':model,'arch':arch})
            else:view.write({'arch':arch})
            views[typ]=view
        action=env['ir.actions.act_window'].search([('res_model','=',model)],limit=1)
        vals={'name':title,'res_model':model,'view_mode':'list,form'}
        if not action:action=env['ir.actions.act_window'].create(vals)
        else:action.write(vals)
        for i,typ in enumerate(['list','form']):
            binding=env['ir.actions.act_window.view'].search([('act_window_id','=',action.id),('view_mode','=',typ)],limit=1)
            vals={'act_window_id':action.id,'view_mode':typ,'view_id':views[typ].id,'sequence':i+1}
            if binding:binding.write(vals)
            else:env['ir.actions.act_window.view'].create(vals)
        root=env.ref('enkhmend_security.root_menu')
        menu=env['ir.ui.menu'].search([('parent_id','=',root.id),('name','=',title)],limit=1)
        vals={'name':title,'parent_id':root.id,'sequence':sequence,'action':'ir.actions.act_window,'+str(action.id)}
        if menu:menu.write(vals)
        else:env['ir.ui.menu'].create(vals)
        return action.id
    control_action=menu_view('x_enkhmend_control','Controls and SoA',
        ['x_code','x_name','x_status','x_owner'],['x_code','x_name','x_applicable','x_status','x_owner','x_implementation','x_evidence','x_refs'],40)
    policy_action=menu_view('x_enkhmend_policy','ISMS Policies',
        ['x_code','x_name','x_version','x_status'],['x_code','x_name','x_version','x_status','x_owner','x_body'],50)
    for code,name,impl,status,gap,owner,refs in CONTROLS:
        vals={'x_code':code,'x_name':name,'x_implementation':impl,'x_status':status,
              'x_evidence':gap,'x_owner':owner,'x_refs':refs,'x_applicable':True}
        record=env['x_enkhmend_control'].search([('x_code','=',code)],limit=1)
        if record:record.write(vals)
        else:env['x_enkhmend_control'].create(vals)
    import html as htmlmod
    for code,(en,mn,sections) in POLICIES.items():
        body='<h2>'+htmlmod.escape(mn)+'</h2>'+''.join('<h3>'+htmlmod.escape(h)+'</h3><p>'+htmlmod.escape(t)+'</p>' for h,t in sections)
        vals={'x_code':code,'x_name':en,'x_version':'1.0','x_status':'Draft - approval pending','x_owner':'ISMS Manager','x_body':body}
        record=env['x_enkhmend_policy'].search([('x_code','=',code)],limit=1)
        if record:record.write(vals)
        else:env['x_enkhmend_policy'].create(vals)

    project=env['project.project'].search([('name','ilike','ISMS Risk Treatment')],limit=1)
    risks=env['project.task'].search([('project_id','=',project.id),('name','=like','EM-R%')])
    stages={}
    for i,name in enumerate(['Identified','Assessed','Treating','Reviewed','Closed']):
        stage=env['project.task.type'].search([('name','=',name),('project_ids','in',project.id)],limit=1)
        if not stage:stage=env['project.task.type'].create({'name':name,'sequence':10+i,'project_ids':[(6,0,[project.id])],'fold':name=='Closed'})
        stages[name]=stage
    risks.write({'stage_id':stages['Assessed'].id,'date_deadline':date(2026,11,16)+timedelta(days=30)})
    legacy=env['project.task.type'].search([('project_ids','in',project.id),('name','ilike','Identified%Assessed%')])
    for stage in legacy:
        if '→' in stage.name and not env['project.task'].search_count([('stage_id','=',stage.id)]):
            stage.write({'project_ids':[(3,project.id)]})
    # Audit the newly added governance records as well.
    for model in ['x_enkhmend_control','x_enkhmend_policy']:
        rule=env['auditlog.rule'].search([('model_id','=',env['ir.model']._get(model).id)],limit=1)
        if not rule:
            rule=env['auditlog.rule'].create({'name':'Enkhmend - '+model,'model_id':env['ir.model']._get(model).id,
                'log_type':'full','log_create':True,'log_write':True,'log_unlink':True,'log_read':False})
        if rule.state!='confirmed':rule.set_to_confirmed()
    cr.commit();env.registry.signal_changes()
    assets=env['product.template'].search([('default_code','=like','EM-AST-%')],order='default_code')
    export={'organization':'Энхмэнд эмнэлэг','database':'enkhmend_isms','date':'2026-11-16',
        'assets':[{'id':a.id,'code':a.default_code,'name':a.name,'description':a.description or ''} for a in assets],
        'risks':[{'id':r.id,'name':r.name,'description':plain(r.description),'html':r.description,'stage':r.stage_id.name,
                  'owner':r.user_ids.mapped('name'),'deadline':str(r.date_deadline)} for r in risks.sorted('name')],
        'controls':[dict(zip(['code','name','implementation','status','gap','owner','refs'],c)) for c in CONTROLS],
        'policies':{k:{'name':v[0],'title':v[1],'sections':v[2]} for k,v in POLICIES.items()},
        'actions':{'controls':control_action,'policies':policy_action},
        'counts':{'assets':len(assets),'risks':len(risks),'controls':env['x_enkhmend_control'].search_count([]),'policies':env['x_enkhmend_policy'].search_count([])}}
    (ROOT/'project-data.json').write_text(json.dumps(export,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'docs').mkdir(exist_ok=True)
    for filename,headers,rows in [
        ('controls-soa.csv',['Control','Description','Implementation','Status','Remaining Work','Owner','Evidence'],CONTROLS),
        ('asset-register.csv',['Code','Asset','Notes'],[(a.default_code,a.name,a.description or '') for a in assets]),
        ('risk-register.csv',['Risk','Stage','Owner','Deadline','Description'],[(r.name,r.stage_id.name,', '.join(r.user_ids.mapped('name')),str(r.date_deadline),plain(r.description)) for r in risks.sorted('name')])]:
        with (ROOT/'docs'/filename).open('w',encoding='utf-8-sig',newline='') as out:
            writer=csv.writer(out);writer.writerow(headers);writer.writerows(rows)
    print(json.dumps(export['counts']))
