from sys import path
import json
import time
from typing import List
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


# database connection
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

DATABASE_URL = "sqlite:///./data.db"

engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[str] = mapped_column(String(50), nullable=True)
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")

app = FastAPI()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def home(db: Session = Depends(get_db)):
    return {"users": db.query(User).all()}


#region agent log
with open("/Users/ramez/Desktop/ramezdev/python-space-game/.cursor/debug.log", "a", encoding="utf-8") as _f:
    _f.write(json.dumps({
        "sessionId": "debug-session",
        "runId": "initial",
        "hypothesisId": "A",
        "location": "backend_apis/server.py:module",
        "message": "module import start",
        "data": {"__name__": __name__},
        "timestamp": int(time.time() * 1000)
    }) + "\n")
#endregion

#region agent log
with open("/Users/ramez/Desktop/ramezdev/python-space-game/.cursor/debug.log", "a", encoding="utf-8") as _f:
    _f.write(json.dumps({
        "sessionId": "debug-session",
        "runId": "initial",
        "hypothesisId": "B",
        "location": "backend_apis/server.py:engine",
        "message": "engine created",
        "data": {"echo": True},
        "timestamp": int(time.time() * 1000)
    }) + "\n")
#endregion

app = FastAPI()

#region agent log
with open("/Users/ramez/Desktop/ramezdev/python-space-game/.cursor/debug.log", "a", encoding="utf-8") as _f:
    _f.write(json.dumps({
        "sessionId": "debug-session",
        "runId": "initial",
        "hypothesisId": "C",
        "location": "backend_apis/server.py:app",
        "message": "fastapi app created",
        "data": {"path_shadow": True},
        "timestamp": int(time.time() * 1000)
    }) + "\n")
#endregion

path = "(/Users/ramez/Desktop/ramezdev/python-space-game)"




@app.get("/")
def home():
    return {"message": "Hello, FastAPI!"}

@app.delete("/")
def delete():
    return {"message": "Server Msg has been deleted successfully"}

@app.put("/")
def put_placeholder():
    return {"message": "PUT endpoint not implemented yet"}


class Sqlalchemy:
    def connectDB(DB,self):
        return {"DB": [str] }


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: mapped_column[Optional[str]]
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")
    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"

# Create the tables once the models are defined.
Base.metadata.create_all(engine)

