"""Provision and verify five operational training roles in enkhmend_isms.

Uses existing Odoo ORM and configuration. Never grants Settings administration.
"""
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')
PRIVATE = ROOT / '.private'
PRIVATE.mkdir(exist_ok=True)
sys.path.insert(0, r'C:\Program Files\Odoo 19.0.20261116\server')
import odoo
from odoo import api
from odoo.exceptions import AccessError
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c',r'C:\Program Files\Odoo 19.0.20261116\server\odoo.conf',
    '-d','enkhmend_isms','--no-http','--logfile',str(ROOT/'rbac-setup.log')])

with Registry('enkhmend_isms').cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    avatar_storage_patch=patch.object(type(env['ir.attachment']),'_storage',lambda self:'db')
    avatar_storage_patch.start()
    def save(model, key, vals):
        xmlid = 'enkhmend_security.' + key
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            record.write(vals)
        else:
            record = env[model].create(vals)
            env['ir.model.data'].create({'module':'enkhmend_security','name':key,
                'model':model,'res_id':record.id,'noupdate':True})
        return record

    # Resolve the user's existing project and team before changing any access.
    projects = env['project.project'].search([('name','ilike','ISMS Risk Treatment')])
    teams = env['helpdesk.ticket.team'].search([('name','ilike','Энхмэнд')])
    assert len(projects)==1, 'Expected one Enkhmend risk project'
    assert len(teams)==1, 'Expected one Enkhmend Helpdesk team'
    project, team = projects, teams
    typo = env['product.template'].search([('default_code','=','EM-AS5-05')])
    if len(typo)==1 and not env['product.template'].search_count([('default_code','=','EM-AST-05')]):
        typo.write({'default_code':'EM-AST-05'})
    assets = env['product.template'].search([('default_code','=like','EM-AST-%')])
    risks = env['project.task'].search([('project_id','=',project.id),('name','=like','EM-R%')])
    if len(assets)<10 or len(risks)<10:
        print('Matching asset codes:',len(assets),'Matching risk tasks:',len(risks))
        print('Product references:',env['product.template'].search([]).mapped('default_code'))
        print('Project task titles:',env['project.task'].search([('project_id','=',project.id)]).mapped('name'))
        raise AssertionError('Existing asset/risk register not found')

    category=save('ir.module.category','category',{'name':'Enkhmend ISMS'})
    privilege=save('res.groups.privilege','privilege',{'name':'Enkhmend ISMS Role','category_id':category.id})
    groups={}
    specs=[('viewer','Viewer',[]),('asset','Asset Officer',[]),
           ('analyst','Risk Analyst',['project.group_project_user']),
           ('responder','Incident Responder',['helpdesk_mgmt.group_helpdesk_user_team']),
           ('manager','ISMS Manager',['project.group_project_manager','helpdesk_mgmt.group_helpdesk_manager','auditlog.group_auditlog_user'])]
    for role,name,extra in specs:
        implied=[env.ref('base.group_user').id]+[env.ref(x).id for x in extra]
        if role!='viewer': implied.append(groups['viewer'].id)
        if role=='manager': implied.extend(groups[x].id for x in ['asset','analyst','responder'])
        groups[role]=save('res.groups','group_'+role,{'name':name,'privilege_id':privilege.id,
            'implied_ids':[(6,0,implied)]})

    # Explicit minimal product ACLs; no broad Inventory user/manager grants.
    for model in ['product.template','product.product','project.project','project.task','helpdesk.ticket']:
        save('ir.model.access','read_'+model.replace('.','_'),{'name':'Enkhmend read '+model,
            'model_id':env['ir.model']._get(model).id,'group_id':groups['viewer'].id,
            'perm_read':True,'perm_write':False,'perm_create':False,'perm_unlink':False})
    for model in ['product.template','product.product']:
        save('ir.model.access','asset_'+model.replace('.','_'),{'name':'Enkhmend asset maintenance '+model,
            'model_id':env['ir.model']._get(model).id,'group_id':groups['asset'].id,
            'perm_read':True,'perm_write':True,'perm_create':True,'perm_unlink':False})

    # Read access to this case's tasks and tickets, including follower-only projects.
    for model,domain in [('project.project',[('id','=',project.id)]),
                         ('project.task',[('project_id','=',project.id)]),
                         ('helpdesk.ticket',[('team_id','=',team.id)])]:
        save('ir.rule','read_rule_'+model.replace('.','_'),{'name':'Enkhmend case read '+model,
            'model_id':env['ir.model']._get(model).id,'groups':[(6,0,[groups['viewer'].id])],
            'domain_force':repr(domain),'perm_read':True,'perm_write':False,'perm_create':False,'perm_unlink':False})

    # Global, conditional write guards stop additive ACLs (notably To-do) from
    # accidentally making the Viewer or unrelated roles able to edit records.
    allowed={'product.template':['asset','manager'],'product.product':['asset','manager'],
             'project.task':['analyst','manager'],'project.project':['manager'],
             'helpdesk.ticket':['responder','manager']}
    for model,roles in allowed.items():
        allowed_expr=' or '.join('user.has_group("enkhmend_security.group_'+r+'")' for r in roles)
        domain='[(0,"=",1)] if user.has_group("enkhmend_security.group_viewer") and not ('+allowed_expr+') else [(1,"=",1)]'
        save('ir.rule','write_guard_'+model.replace('.','_'),{'name':'Enkhmend role write guard '+model,
            'model_id':env['ir.model']._get(model).id,'groups':[(6,0,[])],'domain_force':domain,
            'perm_read':False,'perm_write':True,'perm_create':True,'perm_unlink':True})

    credentials_path=PRIVATE/'users.json'
    credentials=json.loads(credentials_path.read_text(encoding='utf-8')) if credentials_path.exists() else {}
    users={}
    # No outgoing mail during synthetic account creation. Existing passwords are preserved.
    # Store generated training avatars in PostgreSQL; the Windows service owns
    # the existing filestore, so no filesystem ACL or global setting is changed.
    with patch.object(type(env['mail.mail']),'send',lambda self,*a,**k: True):
        for role,name,_ in specs:
            login=role+'@enkhmend.test'
            existing=env['res.users'].search([('login','=',login)],limit=1)
            vals={'name':name+' - Enkhmend','login':login,'email':False,
                'tz':'Asia/Ulaanbaatar','notification_type':'inbox',
                'group_ids':[(6,0,[env.ref('base.group_user').id,groups[role].id])],
                'company_id':env.company.id,'company_ids':[(6,0,[env.company.id])]}
            if not existing:
                password=secrets.token_urlsafe(20)
                vals['password']=password
                credentials[role]={'login':login,'password':password}
                # Save before commit so an interrupted rerun never loses generated credentials.
                credentials_path.write_text(json.dumps(credentials,indent=2),encoding='utf-8')
                users[role]=env['res.users'].with_context(no_reset_password=True).create(vals)
            else:
                vals.pop('login')
                existing.write(vals)
                users[role]=existing
        env['mail.mail'].search([('state','=','outgoing'),('email_to','ilike','@enkhmend.test')]).write({'state':'cancel'})

    team.write({'user_ids':[(4,users['manager'].id),(4,users['responder'].id)],
                'user_id':users['manager'].id,'show_in_portal':False})
    tickets=env['helpdesk.ticket'].search([('team_id','=',team.id)])
    tickets.write({'user_id':users['responder'].id})
    risks.write({'user_ids':[(6,0,[users['analyst'].id])]})
    project.message_subscribe(partner_ids=[u.partner_id.id for u in users.values()])

    # An operational menu exposes the case without granting Inventory or Settings administration.
    root_menu=save('ir.ui.menu','root_menu',{'name':'Enkhmend ISMS','sequence':6,
        'group_ids':[(6,0,[groups['viewer'].id])]})
    for suffix,model,title,fields in [
        ('asset','product.template','Enkhmend Assets',['default_code','name','description']),
        ('risk','project.task','Enkhmend Risks',['name','project_id','user_ids','stage_id','date_deadline','description'])]:
        list_fields=fields[:-1]
        save('ir.ui.view',suffix+'_list',{'name':'enkhmend.'+suffix+'.list','model':model,
            'arch':'<list>'+''.join('<field name="'+f+'"/>' for f in list_fields)+'</list>'})
        form=save('ir.ui.view',suffix+'_form',{'name':'enkhmend.'+suffix+'.form','model':model,
            'arch':'<form><sheet><group>'+''.join('<field name="'+f+'"/>' for f in fields)+'</group></sheet><chatter/></form>'})
        domain=[('default_code','=like','EM-AST-%')] if suffix=='asset' else [('project_id','=',project.id)]
        action=save('ir.actions.act_window',suffix+'_action',{'name':title,'res_model':model,'view_mode':'list,form',
            'domain':repr(domain),'context':repr({'default_project_id':project.id} if suffix=='risk' else {})})
        for seq,typ in [(1,'list'),(2,'form')]:
            save('ir.actions.act_window.view',suffix+'_'+typ+'_binding',{'sequence':seq,'view_mode':typ,
                'view_id':env.ref('enkhmend_security.'+suffix+'_'+typ).id,'act_window_id':action.id})
        save('ir.ui.menu',suffix+'_menu',{'name':title,'parent_id':root_menu.id,'sequence':10 if suffix=='asset' else 20,
            'action':'ir.actions.act_window,'+str(action.id)})
    incident_action=save('ir.actions.act_window','incident_action',{'name':'Enkhmend Incidents','res_model':'helpdesk.ticket',
        'view_mode':'kanban,list,form','domain':repr([('team_id','=',team.id)]),'context':repr({'default_team_id':team.id})})
    save('ir.ui.menu','incident_menu',{'name':'Incident Helpdesk','parent_id':root_menu.id,'sequence':30,
        'action':'ir.actions.act_window,'+str(incident_action.id)})
    save('ir.ui.menu','audit_menu',{'name':'Audit Logs','parent_id':root_menu.id,'sequence':40,
        'group_ids':[(6,0,[groups['manager'].id])],
        'action':'ir.actions.act_window,'+str(env.ref('auditlog.action_auditlog_log_tree').id)})

    checks=[]
    def check(name,passed):
        assert passed,name
        checks.append({'check':name,'passed':True})
    def expect_denied(label,record,user,values):
        try:
            with cr.savepoint(): record.with_user(user).write(values)
        except AccessError: check(label,True)
        else: raise AssertionError(label+' unexpectedly succeeded')
    for role,u in users.items():
        check(role+' is not Settings administrator',not u.has_group('base.group_system') and not u.has_group('base.group_erp_manager'))
        check(role+' can read assets',bool(assets[:1].with_user(u).read(['name'])))
        check(role+' can read risks',bool(risks[:1].with_user(u).read(['name'])))
        check(role+' can read incident',bool(tickets[:1].with_user(u).read(['name'])))
    for role in ['viewer','analyst','responder']:
        expect_denied(role+' cannot edit assets',assets[:1],users[role],{'description':assets[0].description})
    for role in ['viewer','asset','responder']:
        expect_denied(role+' cannot edit risks',risks[:1],users[role],{'description':risks[0].description})
    for role in ['viewer','asset','analyst']:
        expect_denied(role+' cannot edit incident',tickets[:1],users[role],{'description':tickets[0].description})
    for role,record in [('asset',assets[:1]),('analyst',risks[:1]),('responder',tickets[:1])]:
        record.with_user(users[role]).write({'description':record.description})
        check(role+' authorized write succeeds',True)
    for role in ['viewer','asset','analyst','responder']:
        check(role+' cannot read audit logs',not env['auditlog.log'].with_user(users[role]).has_access('read'))
    check('manager can read audit logs',env['auditlog.log'].with_user(users['manager']).has_access('read'))
    check('manager cannot edit audit logs',not env['auditlog.log'].with_user(users['manager']).has_access('write'))
    cr.commit()
    env.registry.signal_changes()
    avatar_storage_patch.stop()
    result={'database':'enkhmend_isms','checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,
        'users':[{'role':r,'login':u.login,'id':u.id} for r,u in users.items()]}
    (ROOT/'rbac-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Created five operational roles and users. '+str(len(checks))+' permission checks passed.')
    print('Passwords are only in .private/users.json; no credentials printed.')
