import json
import time
import requests
from printer import print_bill

with open('config.json', 'r') as f:
    CONFIG = json.load(f)

BASE_URL = CONFIG['PRINT_SERVICE_URL'].rstrip('/')
PRINTER_KEY = CONFIG['PRINTER_CLIENT_API_KEY']
PRINTER_NAME = CONFIG.get('PRINTER_NAME', 'POS90')
POLL_SECONDS = float(CONFIG.get('POLL_SECONDS', 1.0))

HEADERS = {'x-printer-key': PRINTER_KEY}

def claim_job():
    url = f'{BASE_URL}/api/print/jobs/claim'
    r = requests.post(url, params={'printer_name': PRINTER_NAME}, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get('job')

def mark_printed(job_id):
    url = f'{BASE_URL}/api/print/jobs/{job_id}/printed'
    requests.post(url, headers=HEADERS, json={'printer_name': PRINTER_NAME}, timeout=10).raise_for_status()

def mark_failed(job_id, error):
    url = f'{BASE_URL}/api/print/jobs/{job_id}/failed'
    requests.post(url, headers=HEADERS, json={'printer_name': PRINTER_NAME, 'error_message': str(error)[:500]}, timeout=10).raise_for_status()

print('Oorvashee Local Printer Service started...')
print(f'Printer: {PRINTER_NAME} | Server: {BASE_URL}')

while True:
    try:
        job = claim_job()
        if not job:
            time.sleep(POLL_SECONDS)
            continue
        print(f"Printing job {job['id']} / {job['external_ref']}")
        print_bill(job['print_text'], CONFIG)
        mark_printed(job['id'])
        print(f"Printed successfully: {job['id']}")
    except Exception as e:
        print('Printer service error:', e)
        try:
            if 'job' in locals() and job:
                mark_failed(job['id'], e)
        except Exception as fail_error:
            print('Could not update failed status:', fail_error)
        time.sleep(3)
