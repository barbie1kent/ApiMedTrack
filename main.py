from fastapi import FastAPI, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, sessionmaker
from typing import List
from database import *
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import joinedload
from sqlalchemy import create_engine, text, exc
from datetime import time


SessionLocal = sessionmaker(engine, expire_on_commit=False)

app = FastAPI()

class UserLogin(BaseModel):
    login: str
    password: str

class UserReg(BaseModel):
    login: str
    password: str
    genderId: int

class AddMedicineNameRequest(BaseModel):
    name: str

class MedicineRequest(BaseModel):
    name: str
    frequency: str
    period: str
    time: str
    dose: str
    storageLocation: str
    info: str

class AddMedicineFrequencyRequest(BaseModel):
    frequency: str

class AddMedicinePeriodRequest(BaseModel):
    period: str
    time: str
    dose: str

class AddMedicineStorageLocationRequest(BaseModel):
    storageLocation: str

class AddMedicineInfoRequest(BaseModel):
    info: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/addMedicineInfo", status_code=status.HTTP_201_CREATED)
async def add_medicine_info(add_medicine_info_request: AddMedicineInfoRequest, db: Session = Depends(get_db)):
    new_medicine_info = Medicine(
        additionalInformation=add_medicine_info_request.info
    )
    db.add(new_medicine_info)
    db.commit()
    db.refresh(new_medicine_info)
    return new_medicine_info

@app.post("/addMedicineStorageLocation", status_code=status.HTTP_201_CREATED)
async def add_medicine_storage_location(add_medicine_storage_location_request: AddMedicineStorageLocationRequest, db: Session = Depends(get_db)):
    new_medicine_storage_location = Medicine(
        storageLocation=add_medicine_storage_location_request.storageLocation
    )
    db.add(new_medicine_storage_location)
    db.commit()
    db.refresh(new_medicine_storage_location)
    return new_medicine_storage_location

@app.post("/addMedicinePeriod", status_code=status.HTTP_201_CREATED)
async def add_medicine_period(add_medicine_period_request: AddMedicinePeriodRequest, db: Session = Depends(get_db)):
    new_medicine_period = MedicineSchedule(
        period=add_medicine_period_request.period,
        takingTime=add_medicine_period_request.time,
        dose=add_medicine_period_request.dose
    )
    db.add(new_medicine_period)
    db.commit()
    db.refresh(new_medicine_period)
    return new_medicine_period

@app.post("/addMedicineFrequency", status_code=status.HTTP_201_CREATED)
async def add_medicine_frequency(add_medicine_frequency_request: AddMedicineFrequencyRequest, db: Session = Depends(get_db)):
    new_medicine_frequency = ReseptionRate(rate=add_medicine_frequency_request.frequency)
    db.add(new_medicine_frequency)
    db.commit()
    db.refresh(new_medicine_frequency)
    return new_medicine_frequency

# добавление лекарства
@app.post("/addMedicine", status_code=status.HTTP_201_CREATED)
async def add_medicine(medicine_request: MedicineRequest, db: Session = Depends(get_db)):
    new_medicine_name = MedicineDictionary(name=medicine_request.name)
    db.add(new_medicine_name)
    db.commit()
    db.refresh(new_medicine_name)

    new_medicine = Medicine(
        medicineDictionaryId=new_medicine_name.id,
        frequency=medicine_request.frequency,
        period=medicine_request.period,
        time=medicine_request.time,
        dose=medicine_request.dose,
        storageLocation=medicine_request.storageLocation,
        info=medicine_request.info
    )
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    return new_medicine

    # добавление названия лекарства
@app.post("/addMedicineName", status_code=status.HTTP_201_CREATED)
async def add_medicine_name(add_medicine_name_request: AddMedicineNameRequest, db: Session = Depends(get_db)):
    new_medicine_name = MedicineDictionary(name=add_medicine_name_request.name)
    db.add(new_medicine_name)
    db.commit()
    db.refresh(new_medicine_name)
    return new_medicine_name

    # авторизация
@app.post("/login", status_code=status.HTTP_200_OK)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.login == user_login.login, User.password == user_login.password).first()

    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid login or password")

    return {
        "id": db_user.id,
        "login": db_user.login,
        "genderId": db_user.genderId
    }

    # регистрация
@app.post("/register", response_model=UserReg, status_code=status.HTTP_201_CREATED)
def create_user(user: UserReg, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register user with login: {user.login}")

    # Проверка логина
    if not user.login:
        logger.warning("Login is empty")
        raise HTTPException(status_code=400, detail="Login cannot be empty")

    # Проверка пароля
    if not user.password:
        logger.warning("Password is empty")
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    # Проверка гендера (если гендер не обязателен, можно пропустить)
    if user.genderId is not None and user.genderId < 0:
        logger.warning(f"Invalid genderId: {user.genderId}")
        raise HTTPException(status_code=400, detail="Invalid genderId")

    db_user = db.query(User).filter(User.login == user.login).first()
    if db_user:
        logger.warning(f"Login already registered: {user.login}")
        raise HTTPException(status_code=400, detail="Login already registered")

    try:
        new_user = User(login=user.login, password=user.password, genderId=user.genderId)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully: {user.login}")
        return new_user
    except exc.IntegrityError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=400, detail=f"Database error: {e}")

'''@app.post("/add_medicine/", response_model=AddMedicineRequest, status_code=201)
def add_medicine(medicine: AddMedicineRequest, db: Session = Depends(get_db)):
    try:
        new_medicine = Medicine(name=medicine.name, dose=medicine.dose, reseptionRateId=medicine.reseptionRateId,
                                takingTime=medicine.takingTime, storageLocation=medicine.storageLocation,
                                additionalInformation=medicine.additionalInformation,
                                medicineDictionaryId=medicine.medicineDictionaryId, userId=medicine.userId)
        db.add(new_medicine)
        db.commit()
        db.refresh(new_medicine)
        return medicine  # Возвращаем данные о добавленном лекарстве
    except exc.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {e}")'''


'''@app.post("/add_medicine_name/", status_code=201)
def add_medicine_name(medicine_name: AddMedicineNameRequest, db: Session = Depends(get_db)):
    try:
        new_medicine_name = MedicineDictionary(name=medicine_name.name)
        db.add(new_medicine_name)
        db.commit()
        db.refresh(new_medicine_name)
        return {"message": "Название лекарства добавлено", "id": new_medicine_name.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")'''

'''@app.post("/medicines/", response_model=dict, status_code=201)
async def create_medicine(medicine: MedicineCreate, db: SessionLocal = Depends(get_db)):
    try:
        # Проверка существования пользователя
        user_check = await db.execute(select(User).where(User.id == medicine.userId)).scalar_one_or_none()
        if user_check is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Добавление лекарства
        stmt = insert(Medicine).values(
            dose=medicine.dose,
            frequency=medicine.frequency,
            takingTime=medicine.taking_time,
            storageLocation=medicine.storage_location,
            additionalInformation=medicine.additional_information,
            userId=medicine.userId,
            medicineDictionaryId=1
        )
        result = await db.execute(stmt)
        await db.commit()
        return {"message": "Medicine added successfully", "medicine_id": result.inserted_primary_key[0]}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")'''
