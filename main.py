from fastapi import FastAPI, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, sessionmaker
from typing import List
from database import *
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import joinedload
from sqlalchemy import create_engine, text, exc
from datetime import time, date, datetime
from typing import Optional

SessionLocal = sessionmaker(engine, expire_on_commit=False)

app = FastAPI()

class UserLogin(BaseModel):
    login: str
    password: str


class UserRegister(BaseModel):
    login: str
    password: str
    gender_id: int

class FullMedicineReminderCreate(BaseModel):
    name: str
    amount: float
    unit: str
    start_date: date
    end_date: date | None = None
    time: str  # Формат "HH:MM"
    storage_place: str | None = None
    description: str | None = None
    total_stock: float | None = None

    @classmethod
    def validate_time(cls, v):
        if not v:
            return v
        try:
            hours, minutes = map(int, v.split(':'))
            return f"{hours:02}:{minutes:02}"
        except ValueError:
            raise ValueError("Time must be in format 'HH:MM'")

class FullMedicineReminderUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    unit: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    time: Optional[str] = None
    storage_place: Optional[str] = None
    description: Optional[str] = None
    total_stock: Optional[float] = None


class FullMedicineReminderUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    unit: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    time: Optional[str] = None  # Формат "HH:MM"
    storage_place: Optional[str] = None
    description: Optional[str] = None
    total_stock: Optional[float] = None

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
        password=user.password,
        gender_id=user.gender_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user": {"id": new_user.id, "login": new_user.login}}

# Лекарства
@app.post("/users/{user_id}/medicine-reminder", status_code=status.HTTP_201_CREATED)
async def create_full_medicine_reminder(
    user_id: int,
    data: FullMedicineReminderCreate,
    db: Session = Depends(get_db)
):
    # Создаем лекарство
    new_medicine = Medicine(
        user_id=user_id,
        name=data.name,
        amount=data.amount,
        unit=data.unit,
        storage_place=data.storage_place,
        total_stock=data.total_stock,
        description=data.description
    )
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)

    # Создаем напоминание
    new_reminder = Reminder(
        medicine_id=new_medicine.id,
        start_date=data.start_date,
        end_date=data.end_date,
        time=data.time,
        frequency=1  # Заглушка, можно позже сделать выбор частоты
    )
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)

    return {
        "message": "Лекарство и напоминание созданы",
        "medicine": new_medicine,
        "reminder": new_reminder
    }

# обновление
@app.put("/users/{user_id}/medicine-reminder/{medicine_id}", status_code=200)
async def update_full_medicine_reminder(
    user_id: int,
    medicine_id: int,
    data: FullMedicineReminderUpdate,
    db: Session = Depends(get_db)
):
    # Ищем лекарство по ID и проверяем, принадлежит ли пользователю
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id, Medicine.user_id == user_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Лекарство не найдено или не принадлежит вам")

    reminder = db.query(Reminder).filter(Reminder.medicine_id == medicine_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")

    # Обновляем только те поля, которые переданы
    for key, value in data.dict(exclude_unset=True).items():
        if hasattr(medicine, key):
            setattr(medicine, key, value)
        if hasattr(reminder, key):
            setattr(reminder, key, value)

    db.commit()
    db.refresh(medicine)
    db.refresh(reminder)

    return {
        "message": "Данные успешно обновлены",
        "medicine": medicine,
        "reminder": reminder
    }

# удаление
@app.delete("/users/{user_id}/medicine-reminder/{medicine_id}", status_code=200)
async def delete_full_medicine_reminder(
    user_id: int,
    medicine_id: int,
    db: Session = Depends(get_db)
):
    # Проверяем, что лекарство принадлежит пользователю
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id, Medicine.user_id == user_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Лекарство не найдено или не принадлежит вам")

    # Мягкое удаление напоминаний
    reminders = db.query(Reminder).filter(Reminder.medicine_id == medicine_id).all()
    if not reminders:
        raise HTTPException(status_code=404, detail="Напоминания не найдены")

    for r in reminders:
        r.is_active = False

    db.commit()

    return {"message": "Напоминания удалены (мягкое удаление)"}

# получение карточек
@app.get("/users/{user_id}/medicine-cards", status_code=200)
async def get_all_medicine_cards(user_id: int, db: Session = Depends(get_db)):
    medicines = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    if not medicines:
        raise HTTPException(status_code=404, detail="Карточки не найдены")

    result = []
    for med in medicines:
        reminder = db.query(Reminder).filter(Reminder.medicine_id == med.id).first()
        if reminder and reminder.is_active:
            result.append({
                "medicine_id": med.id,
                "name": med.name,
                "amount": med.amount,
                "unit": med.unit,
                "time": reminder.time,
                "total_stock": med.total_stock,
                "storage_place": med.storage_place
            })

    return result
