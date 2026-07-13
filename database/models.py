from datetime import datetime

from sqlalchemy import BigInteger, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .engine import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.name} ({self.telegram_id})>"


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, comment="Длительность в минутах")

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="service")

    def __repr__(self) -> str:
        return f"<Service {self.name}>"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False, comment="Формат YYYY-MM-DD")
    time_slot: Mapped[str] = mapped_column(String(5), nullable=False, comment="Формат HH:MM")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", comment="active / cancelled / completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="appointments")
    service: Mapped["Service"] = relationship(back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment {self.date} {self.time_slot} [{self.status}]>"
