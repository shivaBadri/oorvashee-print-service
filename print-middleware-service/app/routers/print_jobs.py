from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from ..database import get_db
from ..models import PrintJob
from ..schemas import PrintJobCreate, JobStatusUpdate
from ..security import verify_api_key, verify_printer_key
from ..services.template_service import build_thermal_text

router = APIRouter()

@router.post('/jobs', dependencies=[Depends(verify_api_key)])
def create_job(data: PrintJobCreate, db: Session = Depends(get_db)):
    existing = db.query(PrintJob).filter(PrintJob.idempotency_key == data.idempotency_key).first()
    if existing:
        return {'ok': True, 'duplicate': True, 'job_id': str(existing.id), 'status': existing.status}
    job = PrintJob(
        external_ref=data.external_ref,
        job_type=data.job_type,
        payload=data.payload,
        idempotency_key=data.idempotency_key,
        status='pending'
    )
    db.add(job)
    try:
        db.commit()
        db.refresh(job)
    except IntegrityError:
        db.rollback()
        existing = db.query(PrintJob).filter(PrintJob.idempotency_key == data.idempotency_key).first()
        return {'ok': True, 'duplicate': True, 'job_id': str(existing.id), 'status': existing.status}
    return {'ok': True, 'duplicate': False, 'job_id': str(job.id), 'status': job.status}

@router.post('/jobs/claim', dependencies=[Depends(verify_printer_key)])
def claim_job(printer_name: str = 'POS90', db: Session = Depends(get_db)):
    # Atomic claim: avoids two counters printing same bill.
    result = db.execute(text('''
        UPDATE print_jobs
        SET status='processing', locked_by=:printer_name, locked_at=NOW(), updated_at=NOW()
        WHERE id = (
            SELECT id FROM print_jobs
            WHERE status='pending'
            ORDER BY created_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        RETURNING id, external_ref, job_type, payload, retry_count, reprint_count
    '''), {'printer_name': printer_name}).mappings().first()
    db.commit()
    if not result:
        return {'ok': True, 'job': None}
    payload = dict(result['payload'])
    return {
        'ok': True,
        'job': {
            'id': str(result['id']),
            'external_ref': result['external_ref'],
            'job_type': result['job_type'],
            'payload': payload,
            'print_text': build_thermal_text(payload),
            'retry_count': result['retry_count'],
            'reprint_count': result['reprint_count']
        }
    }

@router.post('/jobs/{job_id}/printed', dependencies=[Depends(verify_printer_key)])
def mark_printed(job_id: str, data: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(404, 'Print job not found')
    job.status = 'printed'
    job.printer_name = data.printer_name or job.printer_name
    job.printed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    db.commit()
    return {'ok': True, 'status': job.status}

@router.post('/jobs/{job_id}/failed', dependencies=[Depends(verify_printer_key)])
def mark_failed(job_id: str, data: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(404, 'Print job not found')
    job.retry_count += 1
    job.error_message = data.error_message or 'Printer failed'
    job.status = 'pending' if job.retry_count < 5 else 'failed'
    job.updated_at = datetime.utcnow()
    db.commit()
    return {'ok': True, 'status': job.status, 'retry_count': job.retry_count}

@router.post('/jobs/reset-stuck', dependencies=[Depends(verify_api_key)])
def reset_stuck(db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(minutes=3)
    count = db.query(PrintJob).filter(PrintJob.status == 'processing', PrintJob.locked_at < cutoff).update({
        PrintJob.status: 'pending',
        PrintJob.locked_by: None,
        PrintJob.locked_at: None,
        PrintJob.updated_at: datetime.utcnow()
    })
    db.commit()
    return {'ok': True, 'reset_count': count}

@router.get('/jobs/{external_ref}', dependencies=[Depends(verify_api_key)])
def get_jobs_by_ref(external_ref: str, db: Session = Depends(get_db)):
    jobs = db.query(PrintJob).filter(PrintJob.external_ref == external_ref).order_by(PrintJob.created_at.desc()).all()
    return {'ok': True, 'jobs': [{'id': str(j.id), 'status': j.status, 'retry_count': j.retry_count, 'created_at': j.created_at.isoformat()} for j in jobs]}
