from sqlalchemy import Integer, Column, Float, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from model_tuning_workspace.evaluations.db import Base


class EvalRunModel(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True)
    ai_model = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    total_time_seconds = Column(Float)
    system_message = Column(String)
    accuracy_percentage = Column(Float)

    # Relationships
    case_results = relationship("CaseResultModel", back_populates="eval_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EvalRun(id={self.id}, model={self.ai_model}, accuracy={self.accuracy_percentage}%)>"


class CaseResultModel(Base):
    __tablename__ = "case_results"

    id = Column(Integer, primary_key=True)
    eval_run_id = Column(Integer, ForeignKey('eval_runs.id', ondelete="CASCADE"))
    case_id = Column(String, nullable=False)
    user_msg = Column(String, nullable=False)
    llm_output = Column(String)
    passed = Column(Boolean, nullable=False)
    execution_time_seconds = Column(Float)

    __table_args__ = (
        Index('ix_case_results_case_id', 'case_id'),
        Index('ix_case_results_passed', 'passed'),
    )

    eval_run = relationship("EvalRunModel", back_populates="case_results")
    validator_results = relationship("ValidatorResultModel", back_populates="case_result", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CaseResult(id={self.id}, case_id={self.case_id}, passed={self.passed})>"


class ValidatorResultModel(Base):
    __tablename__ = "validator_results"

    id = Column(Integer, primary_key=True)
    case_result_id = Column(Integer, ForeignKey('case_results.id', ondelete="CASCADE"))
    validator_type = Column(String, nullable=False)
    validator_description = Column(String)
    passed = Column(Boolean, nullable=False)
    details = Column(String)

    # Add index for validator type queries
    __table_args__ = (Index('ix_validator_results_validator_type', 'validator_type'),)

    # Relationships
    case_result = relationship("CaseResultModel", back_populates="validator_results")

    def __repr__(self):
        return f"<ValidatorResult(id={self.id}, type={self.validator_type}, passed={self.passed})>"
