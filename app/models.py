from datetime import datetime
from enum import Enum

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from . import db, login_manager


class Role(Enum):
    ADMIN = "admin"
    Cadastrador = "cadastrador"

    @classmethod
    def choices(cls):
        return [(role.value, role.name.title()) for role in cls]


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), default=Role.Cadastrador, nullable=False)
    active = db.Column(db.Boolean, default=True)

    appointments = db.relationship("Appointment", back_populates="assigned_user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class AppointmentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"

    @classmethod
    def choices(cls):
        return [(status.value, status.name.title()) for status in cls]


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    full_name = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    neighborhood = db.Column(db.String(120))
    zipcode = db.Column(db.String(10))
    reference_point = db.Column(db.String(255))
    notes = db.Column(db.Text)

    reason = db.Column(db.String(120), nullable=False)

    equipment = db.Column(db.String(150))
    registrant_name = db.Column(db.String(150))
    registrant_cpf = db.Column(db.String(14))

    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False)

    visit_date = db.Column(db.Date)
    visit_cadastrador = db.Column(db.String(150))

    assigned_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_user = db.relationship("User", back_populates="appointments")

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "cpf": self.cpf,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "phone": self.phone,
            "address": self.address,
            "neighborhood": self.neighborhood,
            "zipcode": self.zipcode,
            "reference_point": self.reference_point,
            "notes": self.notes,
            "reason": self.reason,
            "equipment": self.equipment,
            "registrant_name": self.registrant_name,
            "registrant_cpf": self.registrant_cpf,
            "status": self.status.value,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "visit_cadastrador": self.visit_cadastrador,
            "assigned_user_id": self.assigned_user_id,
            "assigned_user": self.assigned_user.full_name if self.assigned_user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
