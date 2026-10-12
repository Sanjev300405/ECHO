from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / 'data'
MODEL_DIR = BASE / 'model'
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

FEATURES = [
    'memory_difficulty','missed_medications','routine_disruption','wandering_risk',
    'fall_risk','sleep_disruption','mood_change','social_withdrawal',
    'nutrition_concern','caregiver_burden','safety_incidents','adl_support_need'
]

rng = np.random.default_rng(42)
n = 6000
# 0-4 ordinal observations; use correlated latent vulnerability to make the synthetic task realistic.
latent = np.clip(rng.normal(1.6, 0.9, n), 0, 4)
rows = {}
for i, f in enumerate(FEATURES):
    noise = rng.normal(0, 0.9 + (i % 3) * 0.12, n)
    rows[f] = np.clip(np.rint(latent * (0.65 + 0.08*(i%4)) + noise), 0, 4).astype(int)

df = pd.DataFrame(rows)
# Weighted care-support score, not a clinical dementia score.
weights = np.array([1.4,1.0,1.2,1.8,1.5,0.8,0.9,0.7,1.0,1.2,1.7,1.3])
raw = (df[FEATURES].values * weights).sum(axis=1) / (4 * weights.sum()) * 100
raw += rng.normal(0, 4.0, n)
raw = np.clip(raw, 0, 100)
priority = pd.cut(raw, bins=[-1, 34, 64, 101], labels=[0,1,2]).astype(int)
df['support_priority'] = priority
df['synthetic_echo_score'] = raw.round(1)

df.to_csv(DATA_DIR / 'synthetic_echo_data.csv', index=False)
X = df[FEATURES]
y = df['support_priority']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
model = XGBClassifier(
    n_estimators=220, max_depth=4, learning_rate=.06, subsample=.9, colsample_bytree=.9,
    objective='multi:softprob', num_class=3, eval_metric='mlogloss', random_state=42, n_jobs=2
)
model.fit(X_train, y_train)
pred = model.predict(X_test)
metrics = {
    'accuracy': float(accuracy_score(y_test, pred)),
    'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
    'classification_report': classification_report(y_test, pred, output_dict=True),
    'feature_names': FEATURES,
    'samples': n,
    'disclaimer': 'Synthetic-data prototype for support-priority decision support; not clinical diagnosis.'
}
joblib.dump(model, MODEL_DIR / 'echo_xgb.joblib')
(MODEL_DIR / 'metrics.json').write_text(json.dumps(metrics, indent=2))
(MODEL_DIR / 'features.json').write_text(json.dumps(FEATURES, indent=2))
print(json.dumps({'accuracy': metrics['accuracy'], 'rows': n, 'model': str(MODEL_DIR/'echo_xgb.joblib')}, indent=2))
