from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import sessionmaker, relationship, DeclarativeBase
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Time

class Base(DeclarativeBase):
    pass

class Gender(Base):
    __tablename__ = 'gender'

    id = Column(Integer, primary_key=True, index=True)
    userGender = Column(String(15), nullable=False)

    users = relationship("User", back_populates="gender")

class ReseptionRate(Base):
    __tablename__ = 'reseptionRate'

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(String, nullable=False)

    medicines = relationship("Medicine", back_populates="reseptionRate")

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(20), nullable=False)
    password = Column(String(10), nullable=False)
    genderId = Column(Integer, ForeignKey('gender.id'), nullable=False)

    gender = relationship("Gender", back_populates = "users")
    medicines = relationship("Medicine", back_populates = "user")
    medicineSchedules = relationship("MedicineSchedule", back_populates = "user")

class Medicine(Base):
    __tablename__ = 'medicine'

    id = Column(Integer, primary_key=True, index=True)
    dose = Column(String(30), nullable=False)
    reseptionRateId = Column(Integer, ForeignKey('reseptionRate.id'), nullable=False)
    takingTime = Column(Time, nullable=False)
    storageLocation = Column(String(30), nullable=False)
    additionalInformation = Column(String(100), nullable=False)
    medicineDictionaryId = Column(Integer, ForeignKey('medicineDictionary.id'), nullable=False)
    userId = Column(Integer, ForeignKey('user.id'), nullable=False)

    reseptionRate = relationship("ReseptionRate", back_populates = "medicines")
    user = relationship("User", back_populates = "medicines")
    medicineDictionary = relationship("MedicineDictionary", back_populates= "medicines")
    medicineSchedules = relationship("MedicineSchedule", back_populates= "medicine")

class MedicineSchedule(Base):
    __tablename__ = 'medicineSchedule'

    id = Column(Integer, primary_key=True, index=True)
    dose = Column(Numeric(10, 2), nullable=False)
    takingTime = Column(Time, nullable=False)
    frequency = Column(String(10), nullable=False)
    userId = Column(Integer, ForeignKey('user.id'), nullable=False)
    medicineId = Column(Integer, ForeignKey('medicine.id'), nullable=False)
    unitMeasurementId = Column(Integer, ForeignKey('unitMeasurement.id'), nullable=False)

    user = relationship("User", back_populates="medicineSchedules")
    medicine = relationship("Medicine", back_populates="medicineSchedules")
    unitMeasurement = relationship("UnitMeasurement", back_populates="medicineSchedules")

class UnitMeasurement(Base):
    __tablename__ = 'unitMeasurement'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)

    medicineSchedules = relationship("MedicineSchedule", back_populates="unitMeasurement")

class MedicineDictionary(Base):
    __tablename__ = 'medicineDictionary'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)

    medicines = relationship("Medicine", back_populates="medicineDictionary")


engine = create_engine("postgresql://danya:CgfWvT6YGGY0NWqCffHY8GXsu8IcJBy5@dpg-ctlh1pt2ng1s73b75epg-a.frankfurt-postgres.render.com/medtrack_10p4", echo=True)


Base.metadata.create_all(bind=engine)


