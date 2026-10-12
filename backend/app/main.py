from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import json, os, secrets
from pathlib import Path

from dotenv import load_dotenv
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from .database import Base, engine, get_db, SessionLocal
from .models import Person, Observation, Intervention, HumanReview, CheckInReminder
from .schemas import (LoginRequest, PersonCreate, ObservationInput, InterventionCreate,
                      InterventionUpdate, HumanReviewCreate, ReminderCreate, ReminderUpdate,
                      ChatRequest)
from .ml import predict

BASE_DIR=Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR/'.env')
app=FastAPI(title='ECHO API', version='2.0.0', description='AI-assisted dementia support & caregiver coordination prototype')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_methods=['*'], allow_headers=['*'], allow_credentials=True)
Base.metadata.create_all(bind=engine)
TOKENS={}

ROLES={
    'caregiver': {'label':'Caregiver','permissions':{'read','assess','review','intervene','reminder'}},
    'care_team': {'label':'Care Team','permissions':{'read','assess','review','intervene','reminder','resources'}},
    'admin': {'label':'Administrator','permissions':{'read','assess','review','intervene','reminder','resources','admin'}},
}

RESOURCES=[
 {'id':'r1','name':'ECHO Caregiver Support Desk','category':'Caregiver support','city':'Coimbatore','type':'Community support','phone':'Demo: 1800-000-ECHO','description':'Prototype directory entry for caregiver guidance, peer support and navigation.'},
 {'id':'r2','name':'Memory Support Clinic','category':'Professional support','city':'Coimbatore','type':'Professional service','phone':'Demo: 0422-000-0000','description':'Prototype referral entry for professional assessment and care planning.'},
 {'id':'r3','name':'Home Safety & Mobility Support','category':'Home safety','city':'Coimbatore','type':'Community service','phone':'Demo: 1800-000-SAFE','description':'Prototype support for fall-risk and home-safety planning.'},
 {'id':'r4','name':'Caregiver Counselling Desk','category':'Counselling','city':'Coimbatore','type':'Counselling','phone':'Demo: 1800-000-CARE','description':'Prototype counselling referral for caregiver wellbeing and respite planning.'},
 {'id':'r5','name':'Senior Welfare Information Point','category':'Welfare','city':'Coimbatore','type':'Welfare information','phone':'Demo: 1800-000-WELF','description':'Prototype welfare navigation resource. Verify eligibility with the relevant authority.'},
 {'id':'r6','name':'Community Volunteer Network','category':'Community support','city':'Chennai','type':'Volunteer network','phone':'Demo: 1800-000-VOL','description':'Prototype community resource for practical support and social connection.'},
 {'id':'r7','name':'Professional Support Directory','category':'Professional support','city':'Chennai','type':'Referral directory','phone':'Demo: 1800-000-HELP','description':'Prototype directory for counselling, social work and occupational therapy referrals.'},
]


def auth_user(authorization: str|None=Header(default=None)):
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(401,'Please sign in to the ECHO demo.')
    token=authorization.split(' ',1)[1].strip()
    user=TOKENS.get(token)
    if not user: raise HTTPException(401,'Your demo session has expired. Please sign in again.')
    return user

def require(permission):
    def checker(user=Depends(auth_user)):
        if permission not in user['permissions']: raise HTTPException(403,'This demo role does not have permission for that action.')
        return user
    return checker

@app.post('/api/auth/login')
def login(data:LoginRequest):
    token=secrets.token_urlsafe(24)
    TOKENS[token]={'username':data.username.strip(),'role':data.role,'permissions':ROLES[data.role]['permissions']}
    return {'token':token,'username':data.username.strip(),'role':data.role,'role_label':ROLES[data.role]['label']}

@app.post('/api/auth/logout')
def logout(user=Depends(auth_user), authorization: str|None=Header(default=None)):
    if authorization: TOKENS.pop(authorization.split(' ',1)[1].strip(),None)
    return {'ok':True}

@app.get('/api/auth/me')
def me(user=Depends(auth_user)):
    return {'username':user['username'],'role':user['role'],'role_label':ROLES[user['role']]['label']}

@app.on_event('startup')
def seed_demo():
    db=SessionLocal()
    try:
        if db.query(Person).count()==0:
            p=Person(name='Lakshmi (Demo)', age=72, preferred_language='ta', city='Coimbatore', consent=True, caregiver_name='Anita', emergency_contact='Demo contact', notes='Demo profile for the ARDSICON prototype.')
            db.add(p); db.commit(); db.refresh(p)
            feature_names=['memory_difficulty','missed_medications','routine_disruption','wandering_risk','fall_risk','sleep_disruption','mood_change','social_withdrawal','nutrition_concern','caregiver_burden','safety_incidents','adl_support_need']
            sets=[(2,1,1,0,1,2,1,1,1,2,0,1),(2,1,2,1,1,2,2,1,1,2,1,2),(3,2,2,2,2,2,2,2,1,3,1,2)]
            for vals in sets:
                data=dict(zip(feature_names,vals)); r=predict(data)
                o=Observation(person_id=p.id,**data,echo_score=r['echo_score'],priority=r['priority'],confidence=r['confidence'],explanation_json=json.dumps(r['top_factors']),recommendations_json=json.dumps(r['recommendations']),caregiver_note='Demo observation for showing the longitudinal care loop.')
                db.add(o); db.commit(); db.refresh(o)
                if vals==sets[-1]:
                    review=HumanReview(person_id=p.id,observation_id=o.id,reviewer='Demo Care Team',decision='accepted',note='Demo human review: support-priority result accepted for coordination.')
                    db.add(review)
                    db.add(Intervention(person_id=p.id,observation_id=o.id,title='Wandering safety plan',category='Safety',status='completed',outcome='better',follow_up_date=(datetime.utcnow()+timedelta(days=7)).date().isoformat(),note='Demo intervention outcome: fewer safety concerns reported.'))
                    db.add(Intervention(person_id=p.id,observation_id=o.id,title='Structured daily routine',category='Routine',status='in_progress',outcome='same',follow_up_date=(datetime.utcnow()+timedelta(days=5)).date().isoformat(),note='Continue predictable routine and visual cues.'))
            db.add(CheckInReminder(person_id=p.id,cadence='weekly',next_date=(datetime.utcnow()+timedelta(days=7)).date().isoformat(),note='Weekly support-priority check-in'))
            db.commit()
    finally: db.close()

@app.get('/api/health')
def health(): return {'status':'ok','service':'ECHO API','time':datetime.utcnow().isoformat()+'Z'}

@app.get('/api/dashboard')
def dashboard(db:Session=Depends(get_db), user=Depends(require('read'))):
    people=db.query(Person).count(); obs=db.query(Observation).count(); high=db.query(Observation).filter(Observation.priority=='high').count()
    pending_reviews=db.query(Observation).filter(~Observation.id.in_(db.query(HumanReview.observation_id).filter(HumanReview.decision.in_(['accepted','rejected'])))).count()
    today=datetime.utcnow().date().isoformat()
    due_followups=db.query(Intervention).filter(Intervention.follow_up_date!='',Intervention.follow_up_date<=today,Intervention.outcome=='not_rated').count()
    latest=db.query(Observation).order_by(Observation.created_at.desc()).limit(8).all()
    return {'people':people,'observations':obs,'high_priority_records':high,'pending_reviews':pending_reviews,'due_followups':due_followups,'latest':[serialize_obs(x) for x in latest]}

@app.get('/api/people')
def list_people(db:Session=Depends(get_db), user=Depends(require('read'))):
    return [serialize_person(p) for p in db.query(Person).order_by(Person.created_at.desc()).all()]

@app.post('/api/people')
def create_person(data:PersonCreate, db:Session=Depends(get_db), user=Depends(require('assess'))):
    if not data.consent: raise HTTPException(400,'Consent is required before creating a care profile.')
    p=Person(**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return serialize_person(p)

@app.get('/api/people/{person_id}')
def get_person(person_id:int, db:Session=Depends(get_db), user=Depends(require('read'))):
    p=db.get(Person,person_id)
    if not p: raise HTTPException(404,'Profile not found')
    history=db.query(Observation).filter(Observation.person_id==person_id).order_by(Observation.created_at.asc()).all()
    return {**serialize_person(p),'history':[serialize_obs(o) for o in history]}

@app.post('/api/assess')
def assess(data:ObservationInput, db:Session=Depends(get_db), user=Depends(require('assess'))):
    p=db.get(Person,data.person_id)
    if not p or not p.consent: raise HTTPException(404,'Consented profile not found')
    payload=data.model_dump(); payload.pop('person_id'); note=payload.pop('caregiver_note','')
    result=predict(payload)
    o=Observation(person_id=p.id,**payload,echo_score=result['echo_score'],priority=result['priority'],confidence=result['confidence'],explanation_json=json.dumps(result['top_factors']),recommendations_json=json.dumps(result['recommendations']),caregiver_note=note)
    db.add(o); db.commit(); db.refresh(o)
    return {'observation_id':o.id,**result}

@app.post('/api/reviews')
def create_review(data:HumanReviewCreate, db:Session=Depends(get_db), user=Depends(require('review'))):
    p=db.get(Person,data.person_id)
    if not p or not p.consent: raise HTTPException(404,'Consented profile not found')
    if data.observation_id:
        o=db.get(Observation,data.observation_id)
        if not o or o.person_id!=p.id: raise HTTPException(404,'Observation not found for this profile')
    payload=data.model_dump(); payload['reviewer']=data.reviewer or user['username']
    review=HumanReview(**payload); db.add(review); db.commit(); db.refresh(review)
    return serialize_review(review)

@app.post('/api/interventions')
def create_intervention(data:InterventionCreate, db:Session=Depends(get_db), user=Depends(require('intervene'))):
    p=db.get(Person,data.person_id)
    if not p or not p.consent: raise HTTPException(404,'Consented profile not found')
    if not data.observation_id: raise HTTPException(400,'Link the intervention to a reviewed ECHO observation.')
    review=db.query(HumanReview).filter(HumanReview.observation_id==data.observation_id,HumanReview.decision=='accepted').order_by(HumanReview.created_at.desc()).first()
    if not review: raise HTTPException(409,'Human review is required before activating a significant intervention.')
    item=Intervention(**data.model_dump()); db.add(item); db.commit(); db.refresh(item)
    return serialize_intervention(item)

@app.patch('/api/interventions/{intervention_id}')
def update_intervention(intervention_id:int, data:InterventionUpdate, db:Session=Depends(get_db), user=Depends(require('intervene'))):
    item=db.get(Intervention,intervention_id)
    if not item: raise HTTPException(404,'Intervention not found')
    for key,value in data.model_dump(exclude_unset=True).items(): setattr(item,key,value)
    db.commit(); db.refresh(item)
    return serialize_intervention(item)

@app.get('/api/people/{person_id}/interventions')
def list_interventions(person_id:int, db:Session=Depends(get_db), user=Depends(require('read'))):
    return [serialize_intervention(x) for x in db.query(Intervention).filter(Intervention.person_id==person_id).order_by(Intervention.created_at.desc()).all()]

@app.get('/api/people/{person_id}/timeline')
def person_timeline(person_id:int, db:Session=Depends(get_db), user=Depends(require('read'))):
    p=db.get(Person,person_id)
    if not p: raise HTTPException(404,'Profile not found')
    observations=db.query(Observation).filter(Observation.person_id==person_id).order_by(Observation.created_at.asc()).all()
    interventions=db.query(Intervention).filter(Intervention.person_id==person_id).order_by(Intervention.created_at.asc()).all()
    reviews=db.query(HumanReview).filter(HumanReview.person_id==person_id).order_by(HumanReview.created_at.asc()).all()
    reminders=db.query(CheckInReminder).filter(CheckInReminder.person_id==person_id).order_by(CheckInReminder.next_date.asc()).all()
    return {'person':serialize_person(p),'observations':[serialize_obs(o) for o in observations],'interventions':[serialize_intervention(i) for i in interventions],'reviews':[serialize_review(r) for r in reviews],'reminders':[serialize_reminder(r) for r in reminders]}

@app.get('/api/people/{person_id}/changes')
def changes(person_id:int, db:Session=Depends(get_db), user=Depends(require('read'))):
    obs=db.query(Observation).filter(Observation.person_id==person_id).order_by(Observation.created_at.desc()).limit(2).all()
    if len(obs)<2: return {'has_previous':False,'changes':[]}
    latest,previous=obs[0],obs[1]
    fields=['memory_difficulty','missed_medications','routine_disruption','wandering_risk','fall_risk','sleep_disruption','mood_change','social_withdrawal','nutrition_concern','caregiver_burden','safety_incidents','adl_support_need']
    changes=[]
    for f in fields:
        a=getattr(previous,f); b=getattr(latest,f)
        if a!=b: changes.append({'feature':f,'previous':a,'current':b,'delta':b-a})
    return {'has_previous':True,'previous_score':previous.echo_score,'current_score':latest.echo_score,'score_delta':round(latest.echo_score-previous.echo_score,1),'changes':changes}

@app.get('/api/people/{person_id}/summary')
def care_summary(person_id:int, db:Session=Depends(get_db), user=Depends(require('read'))):
    p=db.get(Person,person_id)
    if not p: raise HTTPException(404,'Profile not found')
    obs=db.query(Observation).filter(Observation.person_id==person_id).order_by(Observation.created_at.desc()).limit(8).all()
    latest=obs[0] if obs else None
    previous=obs[1] if len(obs)>1 else None
    interventions=db.query(Intervention).filter(Intervention.person_id==person_id).order_by(Intervention.created_at.desc()).limit(10).all()
    reviews=db.query(HumanReview).filter(HumanReview.person_id==person_id).order_by(HumanReview.created_at.desc()).limit(5).all()
    return {'generated_at':datetime.utcnow().isoformat()+'Z','profile':serialize_person(p),'current':serialize_obs(latest) if latest else None,'previous':serialize_obs(previous) if previous else None,'score_delta':round(latest.echo_score-previous.echo_score,1) if latest and previous else None,'interventions':[serialize_intervention(i) for i in interventions],'reviews':[serialize_review(r) for r in reviews],'notice':'Support-coordination summary only; not a medical diagnosis or medical record.'}

@app.get('/api/reminders/{person_id}')
def list_reminders(person_id:int, db:Session=Depends(get_db), user=Depends(require('read'))):
    return [serialize_reminder(x) for x in db.query(CheckInReminder).filter(CheckInReminder.person_id==person_id).order_by(CheckInReminder.next_date.asc()).all()]

@app.post('/api/reminders')
def create_reminder(data:ReminderCreate, db:Session=Depends(get_db), user=Depends(require('reminder'))):
    if not db.get(Person,data.person_id): raise HTTPException(404,'Profile not found')
    r=CheckInReminder(**data.model_dump()); db.add(r); db.commit(); db.refresh(r); return serialize_reminder(r)

@app.patch('/api/reminders/{reminder_id}')
def update_reminder(reminder_id:int,data:ReminderUpdate,db:Session=Depends(get_db),user=Depends(require('reminder'))):
    r=db.get(CheckInReminder,reminder_id)
    if not r: raise HTTPException(404,'Reminder not found')
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(r,k,v)
    db.commit(); db.refresh(r); return serialize_reminder(r)

@app.get('/api/resources')
def resources(city:str='',category:str='',user=Depends(require('read'))):
    c=city.strip().lower(); cat=category.strip().lower()
    result=[r for r in RESOURCES if (not c or c in r['city'].lower()) and (not cat or cat==r['category'].lower())]
    return result

CHAT_LANGUAGE_NAMES={'en':'English','ta':'Tamil','hi':'Hindi','ml':'Malayalam','te':'Telugu','kn':'Kannada'}
OBSERVATION_FIELDS=['memory_difficulty','missed_medications','routine_disruption','wandering_risk','fall_risk','sleep_disruption','mood_change','social_withdrawal','nutrition_concern','caregiver_burden','safety_incidents','adl_support_need']

def _chat_context(db, person_id):
    if not person_id:return None,None,[],[]
    person=db.get(Person,person_id)
    if not person or not person.consent:return None,None,[],[]
    observations=db.query(Observation).filter(Observation.person_id==person_id).order_by(Observation.created_at.desc()).limit(5).all()
    interventions=db.query(Intervention).filter(Intervention.person_id==person_id).order_by(Intervention.created_at.desc()).limit(8).all()
    return person,observations[0] if observations else None,observations,interventions

def _build_chat_context(person,latest,observations,interventions):
    if not person:return {'profile_selected':False}
    def op(o): return {'date':o.created_at.isoformat(),'echo_score':o.echo_score,'priority':o.priority,'confidence':o.confidence,'factors':json.loads(o.explanation_json or '[]'),'recommendations':json.loads(o.recommendations_json or '[]'),'observations':{f:getattr(o,f) for f in OBSERVATION_FIELDS}}
    return {'profile_selected':True,'person':{'id':person.id,'name':person.name,'age':person.age,'preferred_language':person.preferred_language,'city':person.city},'latest_checkin':op(latest) if latest else None,'recent_checkins':[op(o) for o in observations],'recent_interventions':[{'title':i.title,'category':i.category,'status':i.status,'outcome':i.outcome,'follow_up_date':i.follow_up_date,'note':i.note} for i in interventions]}

def _get_openai_client():
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key or key=='your_api_key_here' or OpenAI is None:return None
    return OpenAI(api_key=key,base_url=os.getenv('OPENAI_BASE_URL') or None)

def local_chat_reply(message,language,person,latest,interventions):
    m=message.lower(); name=person.name if person else 'the selected person'; score=f"{latest.echo_score:.1f}" if latest else 'not available'; priority=latest.priority if latest else 'not available'
    top=', '.join(x['label'] for x in json.loads(latest.explanation_json or '[]')[:3]) if latest else ''
    if language=='ta':
        if any(x in m for x in ['மதிப்பெண்','score','echoscore']): return f"{name} அவர்களின் தற்போதைய ECHO Score {score}. ஆதரவு முன்னுரிமை {priority}. இது நோயறிதல் அல்ல; பதிவுசெய்யப்பட்ட ஆதரவு தேவைகளை விளக்கும் குறியீடு. முக்கிய காரணிகள்: {top or 'தரவு இல்லை'}."
        if any(x in m for x in ['பாதுகாப்பு','விழும்','தவறிச்','safe','wandering','fall']): return 'பாதுகாப்பு கவலை இருந்தால் தற்போதைய பாதுகாப்புத் திட்டத்தைப் பின்பற்றவும், உடனடி அபாயங்களை குறைக்கவும், தேவையானபோது தகுதியான நிபுணரை அணுகவும். உடனடி ஆபத்து அல்லது கடுமையான காயம் இருந்தால் உள்ளூர் அவசர சேவையை அணுகவும்.'
        if any(x in m for x in ['அழுத்தம்','caregiver','stress']): return 'பராமரிப்பாளர் அழுத்தம் ஒரு முக்கிய ஆதரவு தேவையாகும். பணிகளைப் பகிர்ந்து கொள்ளவும், இடைவெளிகளை திட்டமிடவும், ஆலோசனை அல்லது சமூக ஆதரவை அணுகவும். ECHO காலப்போக்கில் caregiver burden-ஐ கண்காணிக்க உதவும்.'
        if any(x in m for x in ['நினைவு','memory','repeated','forget']): return 'தெளிவான காலண்டர்கள், பெயரிடப்பட்ட பொருட்கள், ஒரே நேரத்தில் ஒரு எளிய வழிமுறை மற்றும் அமைதியான மீளுரைப்பை முயற்சிக்கலாம். புதிய அல்லது மோசமாகும் மாற்றங்கள் இருந்தால் தகுதியான நிபுணரிடம் பேசவும்.'
        if any(x in m for x in ['intervention','outcome','helped']): return 'சமீபத்திய ஆதரவு நடவடிக்கைகள்: ' + ('; '.join(f"{i.title} ({i.status}, முடிவு: {i.outcome})" for i in interventions[:4]) if interventions else 'இன்னும் நடவடிக்கைகள் இல்லை') + '. முடிவுகளைப் பார்த்து ஆதரவை தொடரவோ மதிப்பாய்வு செய்யவோலாம்.'
        return f"ECHO Score, பாதுகாப்பு, பராமரிப்பாளர் ஆதரவு, interventions மற்றும் recovery tracking பற்றி நான் உதவ முடியும். தற்போதைய ECHO Score: {score}. ECHO ஒரு ஆதரவு ஒருங்கிணைப்பு கருவி; நோயறிதல் கருவி அல்ல."
    if language=='hi':
        if any(x in m for x in ['स्कोर','score','echoscore']): return f"{name} का वर्तमान ECHO Score {score} है और support priority {priority} है। यह निदान नहीं है; यह दर्ज की गई सहायता आवश्यकताओं का संकेतक है। मुख्य कारक: {top or 'डेटा उपलब्ध नहीं है'}."
        if any(x in m for x in ['सुरक्षित','सुरक्षा','wandering','fall','safe']): return 'सुरक्षा चिंता होने पर मौजूदा सुरक्षा योजना का पालन करें, तत्काल जोखिम कम करें और जरूरत पड़ने पर योग्य पेशेवर से संपर्क करें। तत्काल खतरे या गंभीर चोट में स्थानीय आपातकालीन सेवा लें।'
        if any(x in m for x in ['तनाव','caregiver','stress']): return 'देखभालकर्ता का तनाव एक महत्वपूर्ण सहायता आवश्यकता है। काम साझा करें, नियमित ब्रेक रखें और परामर्श या सामुदायिक सहायता से जुड़ें। ECHO समय के साथ caregiver burden को ट्रैक कर सकता है।'
        if any(x in m for x in ['याद','memory','repeated','forget']): return 'दिखने वाले कैलेंडर, लेबल किए गए सामान, एक समय में एक सरल निर्देश और शांत दोहराव मदद कर सकते हैं। नए या बढ़ते बदलावों पर योग्य पेशेवर से बात करें।'
        if any(x in m for x in ['intervention','outcome','helped']): return 'हाल की सहायता कार्रवाइयाँ: ' + ('; '.join(f"{i.title} ({i.status}, परिणाम: {i.outcome})" for i in interventions[:4]) if interventions else 'अभी कोई कार्रवाई दर्ज नहीं है') + '. परिणामों के आधार पर सहायता जारी या समीक्षा करें।'
        return f"मैं ECHO Score, सुरक्षा, caregiver support, interventions और recovery tracking समझाने में मदद कर सकता हूँ। वर्तमान ECHO Score {score} है। ECHO एक support-coordination tool है, diagnostic system नहीं।"
    if language in ('ml','te','kn'):
        # Keep the fallback short and transparent; cloud AI can provide full-language conversational replies when configured.
        return {'ml':f"ECHO Score: {score}. ഇത് support-priority സൂചികയാണ്, രോഗനിർണയം അല്ല. സുരക്ഷ, caregiver support, interventions എന്നിവയെക്കുറിച്ച് സഹായിക്കാം.", 'te':f"ECHO Score: {score}. ఇది support-priority సూచిక మాత్రమే, నిర్ధారణ కాదు. భద్రత, caregiver support మరియు interventions గురించి నేను సహాయం చేయగలను.", 'kn':f"ECHO Score: {score}. ಇದು support-priority ಸೂಚಕ ಮಾತ್ರ, ರೋಗನಿರ್ಣಯವಲ್ಲ. ಸುರಕ್ಷತೆ, caregiver support ಮತ್ತು interventions ಕುರಿತು ಸಹಾಯ ಮಾಡಬಹುದು."}[language]
    if any(x in m for x in ['score','echoscore']):
        return f"The current ECHO Score for {name} is {score}, with a {priority} support priority. It is a support-priority indicator based on recorded observations, not a diagnosis. The main contributing factors are: {top or 'not available'}."
    if any(x in m for x in ['safe','wandering','fall','safety']): return 'For safety concerns, use the current safety plan, reduce immediate hazards, keep routines predictable, and seek professional help when concerns are significant or worsening. If there is immediate danger or serious injury, use local emergency services.'
    if any(x in m for x in ['caregiver','stress','stressed']): return 'Caregiver strain is an important support need. Consider sharing tasks, planning regular breaks, using simple observation notes, and connecting with counselling or community support. ECHO can help track caregiver burden over time.'
    if any(x in m for x in ['memory','repeated','forget']): return 'Helpful approaches include visible calendars, labelled items, one-step prompts, calm repetition and a predictable routine. If memory or behaviour changes are new or worsening, discuss them with a qualified professional.'
    if any(x in m for x in ['intervention','outcome','better','helped']): return 'Recent support actions include: ' + ('; '.join(f"{i.title} ({i.status}, outcome: {i.outcome})" for i in interventions[:4]) if interventions else 'none recorded yet') + '. Use their outcomes to decide what to continue or review with the care team.'
    return f"I can help explain ECHO observations, the current support-priority result for {name}, safety planning, caregiver support, interventions and recovery tracking. The current ECHO Score is {score}. ECHO is a support-coordination tool, not a diagnostic system."

def _echo_system_instructions(language,context):
    language_name=CHAT_LANGUAGE_NAMES.get(language,'English')
    return f"""You are ECHO Care Assistant, an AI caregiver-support and care-coordination assistant. Reply entirely in {language_name}. Use supplied ECHO observations as recorded support information, never as a diagnosis. Explain ECHO Score as a support-priority indicator, not disease severity. Never change prescribed medication. For emergencies advise appropriate local emergency/professional help. Be concise, calm and person-centred. CURRENT CONTEXT:\n{json.dumps(context,ensure_ascii=False,indent=2)}"""

@app.post('/api/chat')
def chat(data:ChatRequest, db:Session=Depends(get_db), user=Depends(require('read'))):
    language=data.language if data.language in CHAT_LANGUAGE_NAMES else 'en'
    person,latest,observations,interventions=_chat_context(db,data.person_id)
    client=_get_openai_client()
    if client is None:
        return {'reply':local_chat_reply(data.message,language,person,latest,interventions),'language':language,'model':'ECHO Local Safety Fallback','provider':'local-fallback','person':serialize_person(person) if person else None,'disclaimer':'ECHO provides support decision assistance, not a medical diagnosis.'}
    messages=[{'role':x.role,'content':x.content.strip()} for x in data.history[-10:] if x.content.strip()]
    messages.append({'role':'user','content':data.message.strip()})
    try:
        system_message={'role':'system','content':_echo_system_instructions(language,_build_chat_context(person,latest,observations,interventions))}
        response=client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL','gemini-3.5-flash-lite'),
            messages=[system_message, *messages],
            max_tokens=700,
        )
        reply=(response.choices[0].message.content or '').strip()
        if not reply:
            raise RuntimeError('Gemini returned an empty chat response')
        return {'reply':reply,'language':language,'model':os.getenv('OPENAI_MODEL','gemini-3.5-flash-lite'),'provider':'gemini-openai-compatible','person':serialize_person(person) if person else None,'disclaimer':'ECHO provides support decision assistance, not a medical diagnosis.'}
    except Exception as exc:
        print(f'ECHO AI error: {type(exc).__name__}: {exc}')
        return {'reply':local_chat_reply(data.message,language,person,latest,interventions),'language':language,'model':'ECHO Local Safety Fallback','provider':'local-fallback','person':serialize_person(person) if person else None,'disclaimer':'Cloud AI was unavailable; this response came from the local safety fallback.'}

@app.get('/api/model-info')
def model_info(user=Depends(require('read'))):
    return json.loads((BASE_DIR/'model'/'metrics.json').read_text())

def serialize_person(p):
    return {'id':p.id,'name':p.name,'age':p.age,'preferred_language':p.preferred_language,'city':p.city,'consent':p.consent,'caregiver_name':p.caregiver_name,'emergency_contact':p.emergency_contact,'notes':p.notes,'created_at':p.created_at.isoformat()}

def serialize_intervention(x):
    return {'id':x.id,'person_id':x.person_id,'observation_id':x.observation_id,'title':x.title,'category':x.category,'status':x.status,'outcome':x.outcome,'follow_up_date':x.follow_up_date,'note':x.note,'created_at':x.created_at.isoformat(),'updated_at':x.updated_at.isoformat() if x.updated_at else None}

def serialize_review(x):
    return {'id':x.id,'person_id':x.person_id,'observation_id':x.observation_id,'reviewer':x.reviewer,'decision':x.decision,'note':x.note,'created_at':x.created_at.isoformat()}

def serialize_reminder(x):
    return {'id':x.id,'person_id':x.person_id,'cadence':x.cadence,'next_date':x.next_date,'enabled':x.enabled,'note':x.note,'created_at':x.created_at.isoformat()}

def serialize_obs(o):
    return {'id':o.id,'person_id':o.person_id,'echo_score':o.echo_score,'priority':o.priority,'confidence':o.confidence,'top_factors':json.loads(o.explanation_json or '[]'),'recommendations':json.loads(o.recommendations_json or '[]'),'caregiver_note':o.caregiver_note,'created_at':o.created_at.isoformat(),**{k:getattr(o,k) for k in OBSERVATION_FIELDS}}
