import os,tempfile,time,hmac,hashlib,json,copy
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    os.environ.update(CRM_DATA=tmp,CRM_ADMIN_PASSWORD='test-admin-password-long',CRM_SESSION_SECRET='s'*40,CRM_INGEST_TOKEN='i'*40,CRM_SECURE_COOKIE='0',CHATWOOT_WEBHOOK_SECRET='cw-secret',CRM_LIVE_POSTBACK='0')
    from app import app,dbconn,state,prepare_event
    from fastapi.testclient import TestClient
    c=TestClient(app); assert c.get('/api/state').status_code==401
    assert c.post('/api/login',json={'password':'wrong'}).status_code==401
    assert c.post('/api/login',json={'password':os.environ['CRM_ADMIN_PASSWORD']}).status_code==200
    data=c.get('/api/state').json(); assert data['db']['clients']==[]
    auth={'Authorization':'Bearer '+os.environ['CRM_INGEST_TOKEN']}
    hdr={'X-CSRF-Token':data['csrf']}
    p={'event_id':'t1','name':'Demo buyer','company':'Test Water','phone':'+15550101000','source':'TikTok 广告','channel':'网站表单','tiktokLead':'test-lead','message':'RO 200 units'}
    assert c.post('/webhooks/leads',json=p).status_code==401
    r=c.post('/webhooks/leads',json=p,headers=auth); assert r.status_code==200,r.text
    assert c.post('/webhooks/leads',json=p,headers=auth).json()['duplicate']
    p.update(event_id='t2',message='Please quote'); assert c.post('/webhooks/leads',json=p,headers=auth).status_code==200
    new=c.get('/api/state').json(); assert len(new['db']['clients'])==1 and len(new['db']['messages'])==2
    assert c.put('/api/state',headers=hdr,json={'rev':data['rev'],'db':data['db']}).status_code==409
    payload={'event':'message_created','id':10,'message_type':'incoming','content':'Test WhatsApp inquiry','account':{'id':1},'conversation':{'id':2,'channel':'Channel::Whatsapp','meta':{'sender':{'id':3,'name':'Demo buyer','phone_number':'+15550101000'}}},'content_attributes':{'referral':{'ctwa_clid':'test-click'}}}
    raw=json.dumps(payload).encode();ts=str(int(time.time()));sig='sha256='+hmac.new(b'cw-secret',ts.encode()+b'.'+raw,hashlib.sha256).hexdigest();wh={'X-Chatwoot-Timestamp':ts,'X-Chatwoot-Signature':sig,'Content-Type':'application/json'}
    assert c.post('/webhooks/chatwoot',content=raw,headers={**wh,'X-Chatwoot-Signature':'bad'}).status_code==401
    assert c.post('/webhooks/chatwoot',content=raw,headers=wh).status_code==200
    assert c.post('/webhooks/chatwoot',content=raw,headers=wh).json()['duplicate']
    new=c.get('/api/state').json(); assert len(new['db']['clients'])==1 and len(new['db']['messages'])==3 and new['db']['clients'][0]['ctwa']=='test-click'; assert new['db']['clients'][0]['source']=='TikTok 广告'
    d=copy.deepcopy(new['db']);x=d['clients'][0];x['confirm']='已确认';x['quality']='有效 B2B';x['stage']='报价';x['history'].append({'time':'2026-11-19T00:00:00Z','text':'确认有效询盘'})
    e={'id':'ev1','dedup':'TikTok|有效线索|'+x['id'],'clientId':x['id'],'name':x['name'],'platform':'TikTok','kind':'有效线索','idType':'lead_id','idValue':'test-lead','value':0,'orderRef':'','time':'2026-11-19T00:00:00Z','status':'pending','demo':False};d['events'].append(e)
    r=c.put('/api/state',headers=hdr,json={'rev':new['rev'],'db':d});assert r.status_code==200,r.text
    assert c.post('/api/events/ev1/send',headers=hdr).status_code==409
    new=c.get('/api/state').json();bad=copy.deepcopy(new['db']);bad['events'].append({**e,'id':'ev2'});assert c.put('/api/state',headers=hdr,json={'rev':new['rev'],'db':bad}).status_code==400
    bad=copy.deepcopy(new['db']);bad['clients']=[];assert c.put('/api/state',headers=hdr,json={'rev':new['rev'],'db':bad}).status_code==409
    assert c.put('/api/state',json={'rev':new['rev'],'db':new['db']}).status_code==403
    with dbconn() as con:assert con.execute('SELECT count(*) FROM audit').fetchone()[0]>=4
    assert c.post('/api/logout',headers=hdr).status_code==200;assert c.get('/api/state').status_code==401
    print('PASS: auth, wrong password, CSRF, lead ingestion, retry dedup, contact dedup, signed Chatwoot ingress, unknown-source preservation, optimistic locking, history retention, event uniqueness, real-send lock, logout, audit.')
