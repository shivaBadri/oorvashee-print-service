from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class PrintJobCreate(BaseModel):
    external_ref: str = Field(..., description='Order ID or quotation ID')
    job_type: str = Field(default='invoice', pattern='^(invoice|quotation|test)$')
    payload: Dict[str, Any]
    idempotency_key: str

class PrintJobOut(BaseModel):
    id: str
    external_ref: str
    job_type: str
    status: str
    payload: Dict[str, Any]
    retry_count: int
    reprint_count: int

class JobStatusUpdate(BaseModel):
    printer_name: Optional[str] = None
    error_message: Optional[str] = None
