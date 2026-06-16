# Oorvashee Separate Print Middleware Integration

This package avoids major changes to the live Oorvashee backend. It adds a separate production-safe print service.

## Parts

1. `print-middleware-service/`  
   Deploy this as a new Railway service. It stores print jobs and manages status.

2. `local-printer-service/`  
   Run this on the store billing PC connected to POS-90/ST-500 printer.

3. `integration-snippets/`  
   Copy only the small trigger function into existing Oorvashee backend after order/payment success.

## Final Flow

Oorvashee Backend confirms payment/order  
→ sends invoice payload to Print Middleware  
→ Print Middleware stores pending job  
→ Store PC Local Printer claims job  
→ bill prints  
→ job marked printed

## Railway Setup for Print Middleware

Create new Railway service from `print-middleware-service`.

Add env:

```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
PRINT_SERVICE_API_KEY=use-a-strong-secret-for-main-backend
PRINTER_CLIENT_API_KEY=use-a-different-strong-secret-for-local-printer
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health check:

```txt
https://your-print-service.railway.app/health
```

## Existing Oorvashee Backend Change

Add env in existing backend:

```env
PRINT_SERVICE_URL=https://your-print-service.railway.app
PRINT_SERVICE_API_KEY=same-as-PRINT_SERVICE_API_KEY-in-print-service
```

Copy `integration-snippets/send_to_print_service.py` into your backend, then call:

```python
send_order_to_print_service(confirmed_order)
```

Call it only after Razorpay success / order confirmed.

## Local Printer Setup

On billing PC:

```bash
cd local-printer-service
pip install -r requirements.txt
python main.py
```

First keep `DRY_RUN: true` in `config.json`. After testing, change to:

```json
"DRY_RUN": false
```

Set exact Windows printer name:

```json
"WINDOWS_PRINTER_NAME": "POS-90"
```

## Production Safety Included

- Separate service, no disturbance to main website
- Idempotency key to avoid duplicate printing from Razorpay retries
- Atomic job claiming with PostgreSQL `FOR UPDATE SKIP LOCKED`
- Failed print retry up to 5 times
- Stuck job reset endpoint
- Printer API key separate from backend API key
- Website order flow does not fail if print service is down

## Test Checklist

1. Deploy print middleware.
2. Open `/health`.
3. Run local printer in DRY_RUN mode.
4. Send one paid order from backend.
5. Confirm job is claimed.
6. Confirm print text appears.
7. Change DRY_RUN to false.
8. Test real POS print.
9. Test duplicate webhook; bill should not duplicate.
10. Test printer off; job should retry.
