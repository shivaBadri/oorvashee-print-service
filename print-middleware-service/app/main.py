from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers.print_jobs import router as print_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title='Oorvashee Print Middleware Service', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/health')
def health():
    return {'ok': True, 'service': 'oorvashee-print-middleware'}

app.include_router(print_router, prefix='/api/print', tags=['Print Jobs'])
