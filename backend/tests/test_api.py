from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def auth(role='caregiver'):
    r=client.post('/api/auth/login',json={'username':'Test User','role':role})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['token']}"}

def test_health():
    r=client.get('/api/health'); assert r.status_code==200; assert r.json()['status']=='ok'

def test_login_and_model_info():
    r=client.get('/api/model-info',headers=auth()); assert r.status_code==200; assert r.json()['accuracy']>0.80

def test_resources():
    r=client.get('/api/resources?city=Coimbatore',headers=auth()); assert r.status_code==200; assert len(r.json())>=1

def test_chat_local_fallback():
    r=client.post('/api/chat',headers=auth(),json={'message':'Why is the score changing?','language':'en','person_id':1,'history':[]})
    assert r.status_code==200; assert 'ECHO Score' in r.json()['reply']
