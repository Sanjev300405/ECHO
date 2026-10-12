from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    role: Literal['caregiver','care_team','admin'] = 'caregiver'

class PersonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=45, le=120)
    preferred_language: str = 'en'
    city: str = ''
    consent: bool
    caregiver_name: str = ''
    emergency_contact: str = ''
    notes: str = ''

class ObservationInput(BaseModel):
    person_id: int
    memory_difficulty: int = Field(ge=0, le=4)
    missed_medications: int = Field(ge=0, le=4)
    routine_disruption: int = Field(ge=0, le=4)
    wandering_risk: int = Field(ge=0, le=4)
    fall_risk: int = Field(ge=0, le=4)
    sleep_disruption: int = Field(ge=0, le=4)
    mood_change: int = Field(ge=0, le=4)
    social_withdrawal: int = Field(ge=0, le=4)
    nutrition_concern: int = Field(ge=0, le=4)
    caregiver_burden: int = Field(ge=0, le=4)
    safety_incidents: int = Field(ge=0, le=4)
    adl_support_need: int = Field(ge=0, le=4)
    caregiver_note: str = Field(default='', max_length=1000)

class InterventionCreate(BaseModel):
    person_id: int
    observation_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=180)
    category: str = 'support'
    status: str = 'planned'
    outcome: str = 'not_rated'
    follow_up_date: str = ''
    note: str = ''

class InterventionUpdate(BaseModel):
    status: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_date: Optional[str] = None
    note: Optional[str] = None

class HumanReviewCreate(BaseModel):
    person_id: int
    observation_id: Optional[int] = None
    reviewer: str = 'Care team'
    decision: Literal['accepted','follow_up','rejected','pending'] = 'pending'
    note: str = ''

class ReminderCreate(BaseModel):
    person_id: int
    cadence: Literal['weekly','biweekly','monthly'] = 'weekly'
    next_date: str
    enabled: bool = True
    note: str = 'Periodic ECHO support check-in'

class ReminderUpdate(BaseModel):
    enabled: Optional[bool] = None
    next_date: Optional[str] = None
    note: Optional[str] = None

class ResourceQuery(BaseModel):
    city: str = ''
    category: str = ''

class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = 'en'
    person_id: Optional[int] = None
    history: List[ChatMessage] = Field(default_factory=list, max_length=12)
