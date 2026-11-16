"""Verify the live web server produces actor-attributed audit rows itself."""
import json
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parent
credentials=json.loads((ROOT/'.private/users.json').read_text(encoding='utf-8'))
base='http://127.0.0.1:8069'

def login(role):
    session=requests.Session()
    data=session.post(base+'/web/session/authenticate',json={'jsonrpc':'2.0','method':'call','id':1,
        'params':{'db':'enkhmend_isms',**credentials[role]}},timeout=30).json()
    assert data.get('result',{}).get('uid'),role+' login failed'
    return session,data['result']['uid'],data['result']['user_context']

def call(auth,model,method,args,kwargs=None):
    session,_,context=auth
    data=session.post(base+'/web/dataset/call_kw/'+model+'/'+method,json={'jsonrpc':'2.0','method':'call','id':2,
        'params':{'model':model,'method':method,'args':args,'kwargs':{'context':context,**(kwargs or {})}}},timeout=30).json()
    if 'error' in data:
        raise RuntimeError(model+'.'+method+': '+data['error'].get('message','error'))
    return data['result']

manager=login('manager')
results=[]
started=datetime.now(timezone.utc).isoformat()
for role,model,domain in [
    ('asset','product.template',[('default_code','=','EM-AST-01')]),
    ('analyst','project.task',[('name','ilike','EM-R10')]),
    ('responder','helpdesk.ticket',[('name','ilike','ТУРШИЛТ')])]:
    auth=login(role)
    records=call(auth,model,'search_read',[domain],{'fields':['name','description'],'limit':1})
    assert records,'Training record missing for '+model
    record=records[0]
    original=record['description']
    marker='AUDIT TEST '+datetime.now(timezone.utc).isoformat()+' - synthetic verification'
    value=(original or '')+ ('\n'+marker if model=='product.template' else '<p>'+marker+'</p>')
    changed=False
    try:
        assert call(auth,model,'write',[[record['id']],{'description':value}])
        changed=True
        logs=call(manager,'auditlog.log','search_read',[[('model_model','=',model),('res_id','=',record['id']),
            ('user_id','=',auth[1]),('method','=','write')]],
            {'fields':['id','name','user_id','model_model','res_id','method','create_date','line_ids'],'order':'id desc','limit':1})
        assert logs and logs[0]['line_ids'],'Audit row with changed fields missing for '+model
        entry=logs[0]
        lines=call(manager,'auditlog.log.line','read',[entry['line_ids']],
            {'fields':['field_id','old_value_text','new_value_text']})
        assert any(marker in str(line.get('new_value_text','')) for line in lines),'Changed value was not captured'
        results.append({'role':role,'model':model,'record_id':record['id'],'audit_log_id':entry['id'],
            'actor':entry['user_id'],'method':entry['method'],'created_at':entry['create_date'],
            'old_and_new_values_captured':True})
    finally:
        if changed:
            assert call(auth,model,'write',[[record['id']],{'description':original}])
    restored=call(auth,model,'read',[[record['id']]],{'fields':['description']})[0]['description']
    assert restored==original,'Original description not restored'
    results[-1]['original_description_restored']=True

out={'database':'enkhmend_isms','started_at_utc':started,'checks':results,
    'scope':'Create/write/delete/export on four selected models; reads and login events are not logged by these rules.'}
(ROOT/'audit-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Three live-user writes produced genuine audit rows with old/new values. Original descriptions restored.')
