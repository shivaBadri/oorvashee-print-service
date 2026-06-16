import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import Base

class PrintJob(Base):
    __tablename__ = 'print_jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_ref = Column(String(255), nullable=False)  # order id / quotation id
    job_type = Column(String(50), nullable=False, default='invoice')
    status = Column(String(30), nullable=False, default='pending')  # pending, processing, printed, failed
    payload = Column(JSONB, nullable=False)
    idempotency_key = Column(String(255), nullable=False)
    printer_name = Column(String(100), nullable=True)
    locked_by = Column(String(100), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    reprint_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    printed_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint('idempotency_key', name='uq_print_jobs_idempotency_key'),)
