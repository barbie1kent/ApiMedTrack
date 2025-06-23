from sqlalchemy import Column, Integer, String, Float, Time, Date, DateTime, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.orm import relationship, DeclarativeBase, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, text, exc
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Gender(Base):
    __tablename__ = 'gender'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(10), nullable=False)

    users = relationship("User", back_populates="gender")


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    gender_id = Column(Integer, ForeignKey('gender.id'))

    gender = relationship("Gender", back_populates="users")
    medicines = relationship("Medicine", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")


class Medicine(Base):
    __tablename__ = 'medicine'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    storage_place = Column(String(100))
    amount = Column(Float)  # Количество препарата
    unit = Column(String(20))  # Единица измерения (таблетки, мл и т.д.)
    total_stock = Column(Float)  # Оставшееся количество
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="medicines")
    reminders = relationship("Reminder", back_populates="medicine")


class Reminder(Base):
    __tablename__ = 'reminder'

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey('medicine.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    time = Column(Time, nullable=False)
    frequency = Column(Integer, nullable=False, default=1)  # Сколько раз в день
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(frequency >= 1, name='check_frequency_positive'),
    )

    medicine = relationship("Medicine", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
    doses_taken = relationship("DoseTaken", back_populates="reminder")


class DoseTaken(Base):
    __tablename__ = 'dose_taken'

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey('reminder.id'), nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow)

    reminder = relationship("Reminder", back_populates="doses_taken")


engine = create_engine("postgresql://medtrack_t2oh_user:0mKKVcwdqFndUfE8e1FHB9i3L6eZBXQK@dpg-d1caigbe5dus73fc9a40-a.frankfurt-postgres.render.com/medtrack_t2oh", echo=True)


Base.metadata.create_all(bind=engine)
