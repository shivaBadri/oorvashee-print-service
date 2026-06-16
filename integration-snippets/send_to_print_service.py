"""
Add this small function in existing Oorvashee FastAPI backend.
Call it only AFTER order/payment is confirmed.
"""
import os
import requests
from datetime import datetime

PRINT_SERVICE_URL = os.getenv('PRINT_SERVICE_URL')
PRINT_SERVICE_API_KEY = os.getenv('PRINT_SERVICE_API_KEY')

def send_order_to_print_service(order: dict):
    if not PRINT_SERVICE_URL or not PRINT_SERVICE_API_KEY:
        # Do not break website order flow if print env is missing.
        return {'ok': False, 'skipped': True, 'reason': 'print env missing'}

    order_id = str(order.get('id') or order.get('order_id'))
    idempotency_key = f"order:{order_id}:invoice:v1"

    payload = {
        'external_ref': order_id,
        'job_type': 'invoice',
        'idempotency_key': idempotency_key,
        'payload': {
            'order_id': order_id,
            'invoice_no': order.get('invoice_no') or order_id,
            'date': datetime.now().strftime('%d-%m-%Y %I:%M %p'),
            'payment_status': order.get('payment_status', 'PAID'),
            'store': {'name': 'Oorvashee Saree House'},
            'customer': {
                'name': order.get('customer_name', ''),
                'phone': order.get('customer_phone', '')
            },
            'items': order.get('items', []),
            'totals': {
                'subtotal': order.get('subtotal', 0),
                'discount': order.get('discount', 0),
                'gst': order.get('gst', 0),
                'total': order.get('total', 0)
            }
        }
    }

    try:
        r = requests.post(
            f"{PRINT_SERVICE_URL.rstrip('/')}/api/print/jobs",
            json=payload,
            headers={'x-api-key': PRINT_SERVICE_API_KEY},
            timeout=5
        )
        return r.json()
    except Exception as e:
        # Important: Never fail order/payment because printer failed.
        return {'ok': False, 'error': str(e)}
