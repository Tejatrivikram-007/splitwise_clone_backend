from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
from sqlalchemy import Enum as SqlEnum
import enum


from .database import Base

user_group_association = Table(
    'user_group_association', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    groups = relationship("Group", secondary=user_group_association, back_populates="members")
    expenses_paid = relationship("Expense", back_populates="payer")
    splits = relationship("ExpenseSplit", back_populates="user")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("User", secondary=user_group_association, back_populates="groups")
    expenses = relationship("Expense", back_populates="group")


class SplitTypeEnum(enum.Enum):
    EQUAL = "EQUAL"
    PERCENTAGE = "PERCENTAGE"
    EXACT = "EXACT"

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Float)
    group_id = Column(Integer, ForeignKey("groups.id"))
    paid_by_id = Column(Integer, ForeignKey("users.id"))  # Make sure this exists
    split_type = Column(SqlEnum(SplitTypeEnum), nullable=False, default=SplitTypeEnum.EQUAL)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", back_populates="expenses_paid")
    splits = relationship("ExpenseSplit", back_populates="expense")

    @property
    def paid_by(self):
        return self.payer

    # @property
    # def split_type_str(self):
    #     return self.split_type.value if self.split_type else None

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    percentage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="splits")
