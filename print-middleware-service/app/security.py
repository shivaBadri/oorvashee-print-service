import os
from fastapi import Header, HTTPException, status

API_KEY = os.getenv('PRINT_SERVICE_API_KEY')
PRINTER_KEY = os.getenv('PRINTER_CLIENT_API_KEY')

async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid print service API key')
    return True

async def verify_printer_key(x_printer_key: str = Header(None)):
    if not PRINTER_KEY or x_printer_key != PRINTER_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid printer client key')
    return True
