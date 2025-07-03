import math
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class SplitType(str, Enum):
    EQUAL = "EQUAL"
    PERCENTAGE = "PERCENTAGE"
    EXACT = "EXACT"

class UserBase(BaseModel):
    """Base schema for user data"""
    name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    """Schema for creating new users"""
    pass

class User(UserBase):
    """Complete user schema with all fields"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class GroupBase(BaseModel):
    """Base schema for group data"""
    name: str = Field(..., min_length=1, max_length=100)

class GroupCreate(GroupBase):
    """Schema for creating new groups"""
    members: List[str] = Field(..., min_items=2)

    @validator('members')
    def validate_members(cls, v):
        """Ensure group has at least 2 unique members"""
        if len(v) < 2:
            raise ValueError("Group must have at least 2 members")
        if len(v) != len(set(v)):
            raise ValueError("Group members must be unique")
        return v

class Group(GroupBase):
    """Complete group schema with all fields"""
    id: int
    members: List[User]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ExpenseSplitBase(BaseModel):
    """Base schema for expense splits"""
    user_id: int = Field(..., gt=0)
    amount: Optional[float] = Field(None, gt=0)
    percentage: Optional[float] = Field(None, ge=0, le=100)

    @validator('percentage')
    def validate_percentage(cls, v):
        """Validate percentage is between 0-100"""
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

class ExpenseSplit(ExpenseSplitBase):
    """Complete expense split schema with all fields"""
    id: int
    user: User
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ExpenseCreate(BaseModel):
    """Schema for creating new expenses"""
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    paid_by: int = Field(..., gt=0, description="ID of user who paid")
    split_type: SplitType
    splits: List[ExpenseSplitBase] = Field(default_factory=list)

    @validator('splits')
    def validate_splits(cls, v, values):
        """Validate splits based on split type"""
        if 'split_type' not in values:
            return v
            
        split_type = values['split_type']
        amount = values.get('amount', 0)
        
        if split_type == SplitType.PERCENTAGE:
            if not v:
                raise ValueError("Splits must be provided for percentage split type")
            if not all(s.percentage is not None for s in v):
                raise ValueError("All splits must have percentage for percentage split type")
            if not math.isclose(sum(s.percentage for s in v), 100, rel_tol=1e-9):
                raise ValueError("Total percentage must equal 100")
                
        elif split_type == SplitType.EXACT:
            if not v:
                raise ValueError("Splits must be provided for exact split type")
            if not all(s.amount is not None for s in v):
                raise ValueError("All splits must have amount for exact split type")
            if not math.isclose(sum(s.amount for s in v), amount, rel_tol=1e-9):
                raise ValueError("Sum of exact amounts must equal expense amount")
            
        elif split_type == SplitType.EQUAL:
            if not v:
                raise ValueError("Splits must be provided for equal split type")
            if not all(s.amount is not None for s in v):
                raise ValueError("All splits must have amount for equal split type")
            if not math.isclose(sum(s.amount for s in v), amount, rel_tol=1e-9):
                raise ValueError("Sum of equal amounts must equal expense amount")
                
        return v

class Expense(ExpenseCreate):
    """Complete expense schema with all fields"""
    id: int
    created_at: datetime
    updated_at: datetime
    paid_by: User
    splits: List[ExpenseSplit]
    group_id: int

    class Config:
        orm_mode = True

    @validator('splits', always=True)
    def validate_splits(cls, v, values):
        """Skip validation for existing expenses to avoid the sum check"""
        return v

class ExpenseUpdate(BaseModel):
    """Schema for updating expenses"""
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    paid_by: Optional[int] = Field(None, gt=0)
    split_type: Optional[SplitType] = None
    splits: Optional[List[ExpenseSplitBase]] = None

    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @validator('splits')
    def validate_splits(cls, v, values):
        """Validate splits if provided"""
        if v is None or 'split_type' not in values or values['split_type'] is None:
            return v
            
        split_type = values['split_type']
        amount = values.get('amount')
        
        if split_type == SplitType.PERCENTAGE:
            if not all(s.percentage is not None for s in v):
                raise ValueError("All splits must have percentage for percentage split type")
            if not math.isclose(sum(s.percentage for s in v), 100, rel_tol=1e-9):
                raise ValueError("Total percentage must equal 100")
                
        elif split_type == SplitType.EXACT and amount is not None:
            if not all(s.amount is not None for s in v):
                raise ValueError("All splits must have amount for exact split type")
            if not math.isclose(sum(s.amount for s in v), amount, rel_tol=1e-9):
                raise ValueError("Sum of exact amounts must equal expense amount")
        
        elif split_type == SplitType.EQUAL and amount is not None:
            if not all(s.amount is not None for s in v):
                raise ValueError("All splits must have amount for equal split type")
            if not math.isclose(sum(s.amount for s in v), amount, rel_tol=1e-9):
                raise ValueError("Sum of equal amounts must equal expense amount")
            
        return v

class Balance(BaseModel):
    """Schema for balance between users"""
    user_id: int
    owes_to: int
    amount: float = Field(..., ge=0)

    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is not negative"""
        if v < 0:
            raise ValueError("Balance amount cannot be negative")
        return v

    class Config:
        orm_mode = True

class GroupMembersUpdate(BaseModel):
    """Schema for updating group members"""
    member_ids: List[int] = Field(..., min_items=1)

    @validator('member_ids')
    def validate_member_ids(cls, v):
        """Validate member IDs are unique"""
        if len(v) != len(set(v)):
            raise ValueError("Member IDs must be unique")
        return v

class UserBalances(BaseModel):
    """Schema for user's complete balance summary"""
    total_owed: float = Field(..., ge=0)
    total_owed_to: float = Field(..., ge=0)
    balances: List[Balance] = Field(default_factory=list)

    @validator('balances')
    def validate_balances(cls, v):
        """Ensure no duplicate balances"""
        balance_keys = {(b.user_id, b.owes_to) for b in v}
        if len(balance_keys) != len(v):
            raise ValueError("Duplicate balances found")
        return v