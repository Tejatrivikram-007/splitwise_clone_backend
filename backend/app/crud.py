from sqlalchemy.orm import Session, joinedload
from . import models, schemas
from typing import List, Optional, Dict
import logging
from .schemas import SplitType

logger = logging.getLogger(__name__)

# ---------------------- User CRUD ----------------------
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_name(db: Session, name: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.name == name).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

# ---------------------- Group CRUD ----------------------
def create_group(db: Session, group: schemas.GroupCreate) -> models.Group:
    created_users = []
    for name in group.members:
        existing_user = get_user_by_name(db, name)
        if existing_user:
            created_users.append(existing_user)
        else:
            db_user = models.User(name=name)
            db.add(db_user)
            created_users.append(db_user)
    db.commit()

    db_group = models.Group(name=group.name)
    db.add(db_group)
    db.commit()

    for user in created_users:
        db_group.members.append(user)

    db.commit()
    db.refresh(db_group)
    return db_group

def get_group(db: Session, group_id: int) -> Optional[models.Group]:
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_group_with_members(db: Session, group_id: int) -> Optional[models.Group]:
    return db.query(models.Group).options(
        joinedload(models.Group.members)
    ).filter(models.Group.id == group_id).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100) -> List[models.Group]:
    return db.query(models.Group).offset(skip).limit(limit).all()

def delete_group(db: Session, group_id: int) -> bool:
    db_group = get_group(db, group_id)
    if db_group:
        db.delete(db_group)
        db.commit()
        return True
    return False

# ---------------------- Group Member Operations ----------------------
def add_members_to_group(db: Session, group_id: int, member_ids: List[int]) -> Optional[models.Group]:
    group = get_group_with_members(db, group_id)
    if not group:
        return None
    for user_id in member_ids:
        user = get_user(db, user_id)
        if user and user not in group.members:
            group.members.append(user)
    db.commit()
    db.refresh(group)
    return group

# ---------------------- Expense CRUD ----------------------
def add_expense(db: Session, group_id: int, expense: schemas.ExpenseCreate) -> models.Expense:
    group = get_group_with_members(db, group_id)
    if not group:
        raise ValueError("Group not found")

    payer = get_user(db, expense.paid_by)
    if not payer or payer not in group.members:
        raise ValueError("Payer must be a group member")

    db_expense = models.Expense(
        description=expense.description,
        amount=expense.amount,
        paid_by_id=expense.paid_by,
        group_id=group_id,
        split_type=models.SplitTypeEnum[expense.split_type]
    )
    db.add(db_expense)
    db.commit()

    if expense.split_type == SplitType.EQUAL:
        split_amount = round(expense.amount / len(group.members), 2)
        for member in group.members:
            if member.id != expense.paid_by:
                db.add(models.ExpenseSplit(
                    expense_id=db_expense.id,
                    user_id=member.id,
                    amount=split_amount
                ))

    elif expense.split_type == SplitType.PERCENTAGE:
        member_ids = [m.id for m in group.members]
        for split in expense.splits:
            if split.user_id not in member_ids:
                raise ValueError("All split users must be group members")
            if split.user_id != expense.paid_by:
                amount = round(expense.amount * split.percentage / 100, 2)
                db.add(models.ExpenseSplit(
                    expense_id=db_expense.id,
                    user_id=split.user_id,
                    amount=amount,
                    percentage=split.percentage
                ))

    elif expense.split_type == SplitType.EXACT:
        member_ids = [m.id for m in group.members]
        for split in expense.splits:
            if split.user_id not in member_ids:
                raise ValueError("All split users must be group members")
            if split.user_id != expense.paid_by:
                db.add(models.ExpenseSplit(
                    expense_id=db_expense.id,
                    user_id=split.user_id,
                    amount=split.amount
                ))

    db.commit()
    return get_expense_with_relations(db, db_expense.id)

def get_expense(db: Session, expense_id: int) -> Optional[models.Expense]:
    return db.query(models.Expense).filter(models.Expense.id == expense_id).first()

def get_expense_with_relations(db: Session, expense_id: int) -> Optional[models.Expense]:
    expense = db.query(models.Expense).options(
        joinedload(models.Expense.payer),
        joinedload(models.Expense.group),
        joinedload(models.Expense.splits).joinedload(models.ExpenseSplit.user)
    ).filter(models.Expense.id == expense_id).first()

    if expense:
        logger.debug(f"Expense {expense.id} split_type: {expense.split_type}, value: {expense.split_type.value}")
    return expense

def get_expenses_by_group(db: Session, group_id: int, skip: int = 0, limit: int = 100) -> List[models.Expense]:
    expenses = db.query(models.Expense).options(
        joinedload(models.Expense.payer),
        joinedload(models.Expense.group),
        joinedload(models.Expense.splits).joinedload(models.ExpenseSplit.user)
    ).filter(models.Expense.group_id == group_id).offset(skip).limit(limit).all()

    # Convert SQLAlchemy model to dict that matches Pydantic model
    result = []
    for expense in expenses:
        expense_dict = {
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'paid_by': expense.payer,
            'split_type': expense.split_type.value,
            'created_at': expense.created_at,
            'updated_at': expense.updated_at,
            'group_id': expense.group_id,
            'splits': [{
                'id': split.id,
                'user_id': split.user_id,
                'amount': split.amount,
                'percentage': split.percentage,
                'created_at': split.created_at,
                'updated_at': split.updated_at,
                'user': split.user
            } for split in expense.splits]
        }
        result.append(expense_dict)
    
    return result

def update_expense(db: Session, expense_id: int, expense_update: schemas.ExpenseUpdate) -> Optional[models.Expense]:
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None

    update_data = expense_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        if field == "split_type":
            setattr(db_expense, "split_type", models.SplitTypeEnum[value.value])
        elif field != "splits":
            setattr(db_expense, field, value)

    if "splits" in update_data:
        db.query(models.ExpenseSplit).filter(
            models.ExpenseSplit.expense_id == expense_id
        ).delete()

        for split in update_data["splits"]:
            db.add(models.ExpenseSplit(
                expense_id=expense_id,
                user_id=split["user_id"],
                amount=split.get("amount"),
                percentage=split.get("percentage")
            ))

    db.commit()
    db.refresh(db_expense)
    return get_expense_with_relations(db, expense_id)

def delete_expense(db: Session, expense_id: int) -> bool:
    expense = get_expense(db, expense_id)
    if expense:
        db.delete(expense)
        db.commit()
        return True
    return False

# ---------------------- Balance Calculations ----------------------
def get_group_balances(db: Session, group_id: int) -> List[schemas.Balance]:
    group = get_group_with_members(db, group_id)
    if not group:
        return []

    # Initialize balances dictionary
    balances = {member.id: 0.0 for member in group.members}

    # Calculate net balances for each member
    expenses = db.query(models.Expense).options(
        joinedload(models.Expense.splits)
    ).filter(models.Expense.group_id == group_id).all()

    for expense in expenses:
        payer_id = expense.paid_by_id
        total_shared = 0.0
        
        # Calculate total amount owed by others
        for split in expense.splits:
            if split.user_id != payer_id:
                balances[split.user_id] += split.amount
                total_shared += split.amount
        
        # The payer gets credited with the total shared amount
        balances[payer_id] -= total_shared

    # Convert to list of Balance objects
    result = []
    members = {member.id: member for member in group.members}
    
    # First find who owes and who is owed
    debtors = {uid: amount for uid, amount in balances.items() if amount > 0}
    creditors = {uid: -amount for uid, amount in balances.items() if amount < 0}

    # Simplify the balances (only show who owes whom)
    for debtor_id, debt_amount in debtors.items():
        for creditor_id, credit_amount in creditors.items():
            if credit_amount > 0 and debt_amount > 0:
                transfer = min(debt_amount, credit_amount)
                result.append(schemas.Balance(
                    user_id=debtor_id,
                    owes_to=creditor_id,
                    amount=round(transfer, 2)
                ))
                debt_amount -= transfer
                credit_amount -= transfer
                creditors[creditor_id] = credit_amount
                if debt_amount <= 0:
                    break

    return result

def get_user_balances(db: Session, user_id: int) -> schemas.UserBalances:
    user = db.query(models.User).options(
        joinedload(models.User.groups)
    ).filter(models.User.id == user_id).first()

    if not user:
        return schemas.UserBalances(total_owed=0, total_owed_to=0, balances=[])

    total_owed = 0.0
    total_owed_to = 0.0
    all_balances: List[schemas.Balance] = []

    for group in user.groups:
        group_balances = get_group_balances(db, group.id)
        for balance in group_balances:
            if balance.user_id == user_id:
                total_owed += balance.amount
                all_balances.append(balance)
            elif balance.owes_to == user_id:
                total_owed_to += balance.amount
                all_balances.append(balance)

    return schemas.UserBalances(
        total_owed=round(total_owed, 2),
        total_owed_to=round(total_owed_to, 2),
        balances=all_balances
    )
