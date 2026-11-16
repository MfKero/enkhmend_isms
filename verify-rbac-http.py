import json
from pathlib import Path
import requests

root=Path(__file__).resolve().parent
credentials=json.loads((root/'.private/users.json').read_text(encoding='utf-8'))
base='http://127.0.0.1:8069'
results=[]
for role,cred in credentials.items():
    session=requests.Session()
    result=session.post(base+'/web/session/authenticate',json={'jsonrpc':'2.0','method':'call','id':1,
        'params':{'db':'enkhmend_isms',**cred}},timeout=30).json()
    assert result.get('result',{}).get('uid'),role+' login failed'
    context=result['result']['user_context']
    def call(model,method,args,kwargs=None):
        return session.post(base+'/web/dataset/call_kw/'+model+'/'+method,json={'jsonrpc':'2.0','method':'call','id':2,
            'params':{'model':model,'method':method,'args':args,'kwargs':{'context':context,**(kwargs or {})}}},timeout=30).json()
    assets=call('product.template','search_read',[[('default_code','=like','EM-AST-%')]],{'fields':['name','default_code'],'limit':20})
    assert len(assets.get('result',[]))==10,role+' asset visibility failed'
    risks=call('project.task','search_count',[[('name','=like','EM-R%')]])
    assert risks.get('result')==10,role+' risk visibility failed'
    tickets=call('helpdesk.ticket','search_read',[[]],{'fields':['name','user_id'],'limit':20})
    assert tickets.get('result'),role+' incident visibility failed'
    if role=='viewer':
        denied=call('product.template','write',[[assets['result'][0]['id']],{'name':assets['result'][0]['name']}])
        assert denied.get('error',{}).get('data',{}).get('name')=='odoo.exceptions.AccessError','Viewer write not denied'
    results.append({'role':role,'login':True,'assets_read':10,'risks_read':10,'incidents_read':True})
(root/'rbac-http-verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Five HTTP logins and register visibility passed; Viewer write rejected by live server.')
