from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON
import datetime

Base = declarative_base()

class Claim(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    claim_id = Column(String, unique=True, nullable=False)
    type = Column(String)
    details = Column(Text)
    policy_id = Column(Integer, ForeignKey('policies.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    documents = relationship('Document', back_populates='claim')
    policy = relationship('Policy', back_populates='claims')

class Policy(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True)
    policy_id = Column(String, unique=True, nullable=False)
    coverage = Column(String)
    status = Column(String)
    claims = relationship('Claim', back_populates='policy')

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    doc_id = Column(String, nullable=False)
    content = Column(Text)
    claim_id = Column(Integer, ForeignKey('claims.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    claim = relationship('Claim', back_populates='documents')
    __table_args__ = (UniqueConstraint('doc_id', 'claim_id', name='_doc_claim_uc'),)

class AgenticMemory(Base):
    __tablename__ = 'agentic_memory'
    id = Column(Integer, primary_key=True)
    agent_name = Column(String)
    info = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow) 