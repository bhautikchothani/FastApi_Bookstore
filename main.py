from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Book
from app.database import DATABASE_URL
from app.routes import routes
# from fastapi_jwt_auth import AuthJWT

# auth_jwt = AuthJWT(secret_key="", algorithms=["HS256"])


app = FastAPI()
app.include_router(router=routes)
Base.metadata.create_all(bind=engine)

