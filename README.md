# Splitwise Clone


A simplified Splitwise clone with group expense tracking and balance calculation. This project allows users to create groups, add expenses, and track balances within groups and across all groups a user belongs to.

## Features

- Create groups with multiple users
- Add expenses to groups with equal, percentage-based, or exact splits
- View balances within groups
- View personal balances across all groups

## Technologies

- **Backend:** Python, FastAPI, PostgreSQL  
  FastAPI is used for building a fast and scalable REST API. PostgreSQL is the relational database for storing users, groups, expenses, and balances.
- **Frontend:** React, TailwindCSS  
  React is used for building a dynamic user interface. TailwindCSS provides utility-first CSS styling.
- **Deployment:** Docker, Docker Compose  
  Containerization and orchestration for easy deployment and environment consistency.

## Project Components

### Frontend Components

- **GroupForm.jsx**  
  This component allows users to create a new group by specifying a group name, adding members, and selecting an admin. It manages form state, validates inputs, and submits the group creation request to the backend API. It ensures groups have at least two members and handles dynamic member addition/removal.

- **UserBalances.jsx**  
  Displays the balances for a specific user across all groups. It fetches the user's balances from the backend and shows who owes the user and whom the user owes, along with the amounts. It provides a clear summary of the user's financial standing within the app.

- **GroupBalance.jsx**  
  Shows detailed information about a specific group's expenses and balances. It fetches group details and expenses, calculates each member's spending, what they owe or are owed, and simplifies balances to show net amounts owed between members. This component helps users understand the group's financial status and pending settlements.

- **ExpenseForm.jsx**  
  Allows users to add a new expense to a selected group. Supports multiple split types: equal, percentage-based, and exact amounts. It dynamically updates split details based on the selected group and split type, validates inputs, and submits the expense to the backend. This component is essential for tracking shared expenses accurately.

### Backend Components

- **main.py**  
  The FastAPI application entry point. It sets up API routes for managing users, groups, expenses, and balances. It includes CORS middleware for frontend-backend communication and uses dependency injection for database sessions. Routes handle CRUD operations and balance calculations.

- **crud.py**  
  Contains database operations for creating, reading, updating, and deleting users, groups, and expenses. It also includes logic for calculating balances within groups and for individual users. This module abstracts database interactions and business logic.

- **models.py**  
  Defines SQLAlchemy ORM models representing the database schema: User, Group, Expense, ExpenseSplit, and the SplitTypeEnum. It establishes relationships between entities and includes properties for convenient access to related data.

- **schemas.py**  
  Defines Pydantic schemas for request validation and response serialization. It includes detailed validation logic for fields such as split types and amounts, ensuring data integrity and consistency between frontend and backend.

## How Components Interact

- The **frontend** React components interact with the **backend** FastAPI API via HTTP requests to perform operations like creating groups, adding expenses, and fetching balances.
- The backend uses SQLAlchemy ORM models and CRUD functions to manage data persistence in PostgreSQL.
- Validation schemas ensure that data sent between frontend and backend is consistent and valid.
- The frontend components provide a user-friendly interface to manage group expenses and balances, while the backend handles data storage, business logic, and calculations.

## Running the Project

- Backend runs on FastAPI server (default port 8000).
- Frontend runs on React development server (default port 3000).
- Use Docker and Docker Compose for easy setup and deployment.
