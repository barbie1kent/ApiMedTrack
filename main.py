from fastapi import FastAPI, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, sessionmaker
from typing import List
from database import *
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import joinedload
from sqlalchemy import create_engine, text, exc
from datetime import time, date, datetime


SessionLocal = sessionmaker(engine, expire_on_commit=False)

app = FastAPI()

class UserLogin(BaseModel):
    login: str
    password: str


class UserRegister(BaseModel):
    login: str
    password: str
    gender_id: int


class MedicineCreate(BaseModel):
    name: str
    dosage_description: str
    storage_place: str | None = None
    total_stock: float | None = None
    unit: str | None = None


class ReminderCreate(BaseModel):
    medicine_id: int
    start_date: date
    end_date: date | None = None
    time: time
    frequency: int = 1  # По умолчанию один раз в день


class DoseTakenCreate(BaseModel):
    reminder_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


    # авторизация
@app.post("/login")
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        User.login == user_login.login,
        User.password == user_login.password
    ).first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return {
        "id": db_user.id,
        "login": db_user.login,
        "gender_id": db_user.gender_id
    }

    # регистрация
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.login == user.login).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Login already taken")

    new_user = User(
        login=user.login,
        password_hash=user.password,  # В реальности здесь должен быть хэш
        gender_id=user.gender_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user": {"id": new_user.id, "login": new_user.login}}

@app.post("/medicines", status_code=status.HTTP_201_CREATED)
async def create_medicine(medicine_data: MedicineCreate, db: Session = Depends(get_db)):
    # TODO: добавить авторизацию и привязку к пользователю
    new_medicine = Medicine(**medicine_data.dict())
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    return new_medicine


@app.get("/medicines", response_model=list[MedicineCreate])
async def get_medicines(db: Session = Depends(get_db)):
    return db.query(Medicine).all()


@app.get("/medicines/{medicine_id}")
async def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).get(medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


# === НАПОМИНАНИЯ ===

@app.post("/reminders", status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder_data: ReminderCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли лекарство
    medicine = db.query(Medicine).get(reminder_data.medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    new_reminder = Reminder(**reminder_data.dict())
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    return new_reminder


@app.get("/reminders")
async def get_reminders(db: Session = Depends(get_db)):
    return db.query(Reminder).filter(Reminder.is_active == True).all()


# === ПРИЁМ ЛЕКАРСТВ ===

@app.post("/dose-taken", status_code=status.HTTP_201_CREATED)
async def mark_dose_taken(data: DoseTakenCreate, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).get(data.reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    dose_taken = DoseTaken(reminder_id=data.reminder_id)
    db.add(dose_taken)
    db.commit()
    db.refresh(dose_taken)

    # Обновляем остатки лекарства
    if reminder.medicine.total_stock > 0:
        reminder.medicine.total_stock -= 1
        db.commit()

    return dose_taken


@app.get("/stock/{medicine_id}")
async def get_stock(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).get(medicine_id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    return {
        "medicine_id": medicine_id,
        "name": medicine.name,
        "total_stock": medicine.total_stock,
        "unit": medicine.unit
    }
