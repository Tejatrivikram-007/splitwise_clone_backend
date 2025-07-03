from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import crud, models, schemas
from .database import SessionLocal, engine
import logging

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
logger = logging.getLogger(__name__)

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------- Debug Endpoints ----------------------
@app.get("/debug/group-members")
def debug_group_members(db: Session = Depends(get_db)):
    groups = db.query(models.Group).all()
    return [
        {"group": group.name, "members": [user.name for user in group.members]}
        for group in groups
    ]

# ---------------------- User Endpoints ----------------------
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user=user)

@app.post("/users/batch", response_model=List[schemas.User])
def create_users(users: List[schemas.UserCreate], db: Session = Depends(get_db)):
    created = []
    for user in users:
        if crud.get_user_by_email(db, email=user.email):
            continue
        created.append(crud.create_user(db, user=user))
    return created

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/{user_id}/balances", response_model=List[schemas.Balance])
def get_user_balances(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_balances(db, user_id=user_id)

@app.get("/users/expenses", response_model=List[schemas.Expense])
def get_user_expenses(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    return expenses

# ---------------------- Group Endpoints ----------------------
@app.post("/groups/", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    return crud.create_group(db, group=group)

@app.get("/groups/", response_model=List[schemas.Group])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_groups(db, skip=skip, limit=limit)

@app.get("/groups/{group_id}", response_model=schemas.Group)
def read_group(group_id: int, db: Session = Depends(get_db)):
    db_group = crud.get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

@app.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    if not crud.delete_group(db, group_id=group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}

@app.get("/groups/{group_id}/expenses", response_model=List[schemas.Expense])
def read_group_expenses(group_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_expenses_by_group(db, group_id=group_id, skip=skip, limit=limit)

@app.post("/groups/{group_id}/expenses")
async def create_expense(group_id: int, expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    # Log the incoming request
    print(f"Incoming expense data: {expense.dict()}")
    
    try:
        db_expense = crud.add_expense(db, group_id=group_id, expense=expense)
        return db_expense
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/groups/{group_id}/expenses", response_model=List[schemas.Expense])
def read_group_expenses(group_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    expenses = crud.get_expenses_by_group(db, group_id=group_id, skip=skip, limit=limit)
    print("Returning expenses:", [{
        'id': e.id,
        'split_type': e.split_type.value if e.split_type else None,
        'description': e.description
    } for e in expenses])
    return expenses

@app.get("/groups/{group_id}/balances", response_model=List[schemas.Balance])
def get_balances(group_id: int, db: Session = Depends(get_db)):
    return crud.get_group_balances(db, group_id=group_id)

# ---------------------- Expense Endpoints ----------------------
@app.get("/expenses/{expense_id}", response_model=schemas.Expense)
def read_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = crud.get_expense(db, expense_id=expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@app.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, expense_update: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    updated_expense = crud.update_expense(db, expense_id=expense_id, expense_update=expense_update)
    if not updated_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return updated_expense

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    if not crud.delete_expense(db, expense_id=expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"ok": True}
