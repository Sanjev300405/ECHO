from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Person(Base):
    __tablename__='people'
    id=Column(Integer, primary_key=True)
    name=Column(String(120), nullable=False)
    age=Column(Integer, nullable=False)
    preferred_language=Column(String(10), default='en')
    city=Column(String(120), default='')
    consent=Column(Boolean, default=False)
    caregiver_name=Column(String(120), default='')
    emergency_contact=Column(String(120), default='')
    notes=Column(Text, default='')
    created_at=Column(DateTime, default=datetime.utcnow)
    observations=relationship('Observation', back_populates='person', cascade='all, delete-orphan')
    interventions=relationship('Intervention', back_populates='person', cascade='all, delete-orphan')
    reviews=relationship('HumanReview', back_populates='person', cascade='all, delete-orphan')
    reminders=relationship('CheckInReminder', back_populates='person', cascade='all, delete-orphan')

class Observation(Base):
    __tablename__='observations'
    id=Column(Integer, primary_key=True)
    person_id=Column(Integer, ForeignKey('people.id'), nullable=False)
    memory_difficulty=Column(Integer, default=0)
    missed_medications=Column(Integer, default=0)
    routine_disruption=Column(Integer, default=0)
    wandering_risk=Column(Integer, default=0)
    fall_risk=Column(Integer, default=0)
    sleep_disruption=Column(Integer, default=0)
    mood_change=Column(Integer, default=0)
    social_withdrawal=Column(Integer, default=0)
    nutrition_concern=Column(Integer, default=0)
    caregiver_burden=Column(Integer, default=0)
    safety_incidents=Column(Integer, default=0)
    adl_support_need=Column(Integer, default=0)
    echo_score=Column(Float, nullable=False)
    priority=Column(String(20), nullable=False)
    confidence=Column(Float, default=0)
    explanation_json=Column(Text, default='[]')
    recommendations_json=Column(Text, default='[]')
    caregiver_note=Column(Text, default='')
    created_at=Column(DateTime, default=datetime.utcnow)
    person=relationship('Person', back_populates='observations')

class Intervention(Base):
    __tablename__='interventions'
    id=Column(Integer, primary_key=True)
    person_id=Column(Integer, ForeignKey('people.id'), nullable=False)
    observation_id=Column(Integer, ForeignKey('observations.id'), nullable=True)
    title=Column(String(180), nullable=False)
    category=Column(String(80), default='support')
    status=Column(String(30), default='planned')
    outcome=Column(String(30), default='not_rated')
    follow_up_date=Column(String(20), default='')
    note=Column(Text, default='')
    created_at=Column(DateTime, default=datetime.utcnow)
    updated_at=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    person=relationship('Person', back_populates='interventions')

class HumanReview(Base):
    __tablename__='human_reviews'
    id=Column(Integer, primary_key=True)
    person_id=Column(Integer, ForeignKey('people.id'), nullable=False)
    observation_id=Column(Integer, ForeignKey('observations.id'), nullable=True)
    reviewer=Column(String(120), default='Care team')
    decision=Column(String(30), default='pending')
    note=Column(Text, default='')
    created_at=Column(DateTime, default=datetime.utcnow)
    person=relationship('Person', back_populates='reviews')

class CheckInReminder(Base):
    __tablename__='checkin_reminders'
    id=Column(Integer, primary_key=True)
    person_id=Column(Integer, ForeignKey('people.id'), nullable=False)
    cadence=Column(String(30), default='weekly')
    next_date=Column(String(20), nullable=False)
    enabled=Column(Boolean, default=True)
    note=Column(Text, default='Weekly ECHO support check-in')
    created_at=Column(DateTime, default=datetime.utcnow)
    person=relationship('Person', back_populates='reminders')
