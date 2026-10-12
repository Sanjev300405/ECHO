from pathlib import Path
import joblib, json
import numpy as np
import pandas as pd
import shap

BASE = Path(__file__).resolve().parents[1]
MODEL = joblib.load(BASE/'model'/'echo_xgb.joblib')
FEATURES = json.loads((BASE/'model'/'features.json').read_text())
EXPLAINER = shap.TreeExplainer(MODEL)
LABELS = ['low','moderate','high']

DISPLAY = {
'memory_difficulty':'Memory difficulty','missed_medications':'Missed medications','routine_disruption':'Routine disruption',
'wandering_risk':'Wandering risk','fall_risk':'Fall risk','sleep_disruption':'Sleep disruption','mood_change':'Mood/behaviour change',
'social_withdrawal':'Social withdrawal','nutrition_concern':'Nutrition concern','caregiver_burden':'Caregiver burden',
'safety_incidents':'Safety incidents','adl_support_need':'Daily-living support need'}

REC_RULES = [
 ('wandering_risk',2,'wandering_plan'), ('fall_risk',2,'fall_prevention'), ('missed_medications',2,'medication_reminder'),
 ('memory_difficulty',2,'memory_aids'), ('routine_disruption',2,'structured_routine'), ('caregiver_burden',2,'caregiver_respite'),
 ('social_withdrawal',2,'social_connection'), ('nutrition_concern',2,'nutrition_support'), ('sleep_disruption',2,'sleep_routine'),
 ('mood_change',2,'behaviour_log'), ('safety_incidents',1,'home_safety_review'), ('adl_support_need',2,'daily_living_support')]

def predict(payload: dict):
    row = pd.DataFrame([{f:int(payload[f]) for f in FEATURES}], columns=FEATURES)
    proba = MODEL.predict_proba(row)[0]
    cls = int(np.argmax(proba))
    shap_values = EXPLAINER.shap_values(row)
    contrib = shap_values[0,:,cls]
    factors = sorted([
        {'feature': f, 'label': DISPLAY[f], 'value': int(row.iloc[0][f]), 'impact': float(contrib[i])}
        for i,f in enumerate(FEATURES)
    ], key=lambda x: abs(x['impact']), reverse=True)[:5]
    # ECHO Score = interpretable support burden index from observations, separate from class probability.
    weights=np.array([1.4,1.0,1.2,1.8,1.5,0.8,0.9,0.7,1.0,1.2,1.7,1.3])
    score=float(np.dot(row.iloc[0].to_numpy(),weights)/(4*weights.sum())*100)
    recs=[key for feat,threshold,key in REC_RULES if int(row.iloc[0][feat])>=threshold]
    if not recs: recs=['maintain_routine','regular_checkin']
    safety=[]
    if payload['wandering_risk']>=3: safety.append('urgent_wandering_safety')
    if payload['fall_risk']>=3: safety.append('urgent_fall_safety')
    if payload['safety_incidents']>=3: safety.append('urgent_safety_review')
    return {
      'priority': LABELS[cls], 'confidence': round(float(proba[cls])*100,1), 'echo_score': round(score,1),
      'probabilities': {LABELS[i]:round(float(p)*100,1) for i,p in enumerate(proba)},
      'top_factors': factors, 'recommendations': recs[:6], 'safety_flags': safety,
      'disclaimer':'Decision-support prototype trained on synthetic data. It does not diagnose dementia or replace clinical judgement.'
    }
