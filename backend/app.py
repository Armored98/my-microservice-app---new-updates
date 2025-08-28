
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os, time, jwt

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from passlib.context import CryptContext

# ---------- Env ----------
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Majed1234!")
DB_NAME = os.getenv("DB_NAME", "todos")
DB_HOST = os.getenv("DB_HOST", "10.96.80.4")
DB_PORT = os.getenv("DB_PORT", "5432")
JWT_SECRET = os.getenv("JWT_SECRET", "please-change-me")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- Models ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    todos = relationship("Todo", back_populates="owner", cascade="all,delete")

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    owner = relationship("User", back_populates="todos")

# ---------- Schemas ----------
class SignupIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    token: str
    expires_at: datetime

class TodoIn(BaseModel):
    task: str

class TodoOut(BaseModel):
    id: int
    task: str

# ---------- App ----------
app = FastAPI()

@app.on_event("startup")
def startup():
    # Retry DB to avoid crashloops if DB isn't immediately ready
    deadline = time.time() + 30
    last_err = None
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            Base.metadata.create_all(bind=engine)
            return
        except Exception as e:
            last_err = e
            time.sleep(2)
    raise RuntimeError(f"DB not ready: {last_err}")

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def issue_token(user_id: int) -> TokenOut:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRES_HOURS)
    payload = {"sub": str(user_id), "exp": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return TokenOut(token=token, expires_at=exp)

def get_current_user(authorization: Optional[str] = Header(None),
                     db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        uid = int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid/expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/signup", response_model=TokenOut)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=email, password_hash=pwd.hash(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return issue_token(user.id)

@app.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    user = db.query(User).filter_by(email=email).first()
    if not user or not pwd.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return issue_token(user.id)

@app.get("/todos", response_model=List[TodoOut])
def list_todos(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Todo).filter_by(user_id=current.id).order_by(Todo.id.desc()).all()
    return [TodoOut(id=r.id, task=r.task) for r in rows]

@app.post("/todos", response_model=TodoOut, status_code=201)
def add_todo(body: TodoIn, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = body.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="task required")
    t = Todo(task=task, user_id=current.id)
    db.add(t); db.commit(); db.refresh(t)
    return TodoOut(id=t.id, task=t.task)

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(Todo).filter_by(id=todo_id, user_id=current.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(t); db.commit()
    return {"ok": True}
