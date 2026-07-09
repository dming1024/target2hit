"""SQLAlchemy models for Target2Drug pipeline."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey, Boolean,
)
from database.session import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String(64), primary_key=True)
    gene_symbol = Column(String(32), nullable=False, index=True)
    disease = Column(String(128))
    status = Column(String(32), default="pending")
    config = Column(JSON)
    current_module = Column(String(64))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class Compound(Base):
    __tablename__ = "compounds"
    id = Column(String(64), primary_key=True)
    smiles = Column(Text, nullable=False)
    inchi_key = Column(String(64), index=True)
    source = Column(String(64))
    molecular_weight = Column(Float)
    logp = Column(Float)
    hbd = Column(Integer)
    hba = Column(Integer)
    rotatable_bonds = Column(Integer)


class ScreeningResult(Base):
    __tablename__ = "screening_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False, index=True)
    compound_id = Column(String(64), ForeignKey("compounds.id"))
    ai_score = Column(Float)
    mode = Column(String(16))
    rank = Column(Integer)


class DockingResult(Base):
    __tablename__ = "docking_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False, index=True)
    compound_id = Column(String(64), ForeignKey("compounds.id"))
    binding_energy = Column(Float)
    pose_file = Column(String(256))
    rank = Column(Integer)


class RankingResult(Base):
    __tablename__ = "ranking_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False, index=True)
    compound_id = Column(String(64), ForeignKey("compounds.id"))
    final_score = Column(Float)
    ai_score = Column(Float)
    dock_score = Column(Float)
    drug_likeness = Column(Float)
    sa_score = Column(Float)
    pains_flag = Column(Boolean)
    novelty = Column(Float)
    rank = Column(Integer)
