import json,time
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
creds=json.loads((ROOT/'.private/users.json').read_text(encoding='utf-8'))
session=requests.Session();base='http://127.0.0.1:8069'
auth=session.post(base+'/web/session/authenticate',json={'jsonrpc':'2.0','method':'call','id':1,'params':{'db':'enkhmend_isms',**creds['responder']}},timeout=30).json()['result']
def call(model,method,args,kwargs=None):
    data=session.post(base+'/web/dataset/call_kw/'+model+'/'+method,json={'jsonrpc':'2.0','method':'call','id':2,
        'params':{'model':model,'method':method,'args':args,'kwargs':{'context':auth['user_context'],**(kwargs or {})}}},timeout=30).json()
    assert 'error' not in data,(model,method,data.get('error',{}).get('message'))
    return data['result']
ticket=call('helpdesk.ticket','search_read',[[('name','ilike','ТУРШИЛТ')]],{'fields':['id','name','team_id','description'],'limit':1})[0]
stages=call('helpdesk.ticket.stage','search_read',[[('team_ids','in',[ticket['team_id'][0]])]],{'fields':['id','name','closed'],'order':'sequence,id'})
ordered=['Incident','Report','Investigate','Resolve','Close'];byname={s['name']:s for s in stages}
assert set(ordered).issubset(byname)
events=[]
for name in ordered:
    call('helpdesk.ticket','write',[[ticket['id']],{'stage_id':byname[name]['id']}])
    read=call('helpdesk.ticket','read',[[ticket['id']]],{'fields':['stage_id','closed']})[0]
    assert read['stage_id'][0]==byname[name]['id']
    events.append({'stage':name,'stage_id':byname[name]['id'],'actor_id':auth['uid'],'verified_at_utc':datetime.now(timezone.utc).isoformat(),'closed':read['closed']})
summary='<h3>Сургалтын симуляцийн үр дүн</h3><p>2026-11-16-нд Incident Responder account-аар Incident, Report, Investigate, Resolve, Close гэсэн таван шатанд вебээр бодитоор шилжүүлж шалгасан. Энэ нь workflow-ийн техникийн туршилт бөгөөд бодит халдлагыг шалгасан эсвэл өвчтөний мэдээлэл сэргээсэн гэсэн үг биш.</p><p>Root cause hypothesis: хэрэглэгчид хэрэгцээнээс өргөн export эрхтэй байж болзошгүй гэсэн сургалтын таамаглал. Containment болон recovery нь төлөвлөсөн ажиллагаа. Бодит сүлжээ, өвчтөний мэдээлэл, бусдын account дээр өөрчлөлт хийгээгүй.</p><p>Lessons learned: үе шат бүрд эзэн, нотолгоо, шийдвэрийг ялгаж баримтжуулах; ангиллын шошго болон бодит эрхийн хоригийг андуурахгүй; audit log-ийг гаднын хамгаалалттай санд хадгалах ажлыг үргэлжлүүлэх.</p>'
original=ticket['description'] or ''
if 'Сургалтын симуляцийн үр дүн' not in original:
    call('helpdesk.ticket','write',[[ticket['id']],{'description':original+summary}])
(ROOT/'incident-exercise.json').write_text(json.dumps({'ticket_id':ticket['id'],'ticket':ticket['name'],'events':events,'exercise_only':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('Five workflow transitions verified through the live responder account; training ticket closed.')
