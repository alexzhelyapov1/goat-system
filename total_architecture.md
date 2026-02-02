# Goat System: Architecture Report (Post-Migration)

This document provides a detailed analysis of the Goat System's current architecture, following a successful migration to a decoupled, service-oriented structure.

## 1. Overall Architecture Summary

The Goat System is a multi-headed application with a clean separation between its presentation layer and its business logic. The four main entry points are:

1.  **Flask Web App**: Acts as a pure presentation layer (a "Backend for Frontend"). It serves HTML pages, manages user interface state, and is a client to the FastAPI backend for all data and business operations.
2.  **FastAPI App**: The sole backend service. It provides a comprehensive RESTful JSON API for all the application's business logic and is the single source of truth for data and authentication.
3.  **Telegram Bot**: A standalone conversational interface for interacting with the system. It uses the shared, framework-agnostic service layer to perform its duties.
4.  **RQ Worker**: A background process that executes asynchronous jobs. It is also a standalone component that interacts with the application core via the service layer.

The core of the system is now a framework-agnostic **Data and Service Layer**. The tight coupling to the Flask ecosystem has been removed, allowing all components to share the same business logic and data models without depending on a web framework context.

---

## 2. System Components

### 2.1. Flask Web Application (Frontend Server)

-   **Entry Point**: `run.py` (for Gunicorn/WSGI).
-   **Framework**: Flask, Flask-Login.
-   **Responsibility**:
    -   Render Jinja2 templates to provide the user interface.
    -   Manage frontend user sessions.
    -   Act as a pure client to the FastAPI backend for **all** operations, including user registration, login, and data management. It uses an `httpx`-based client (`app/api_client`).
-   **Structure**: Organized into Blueprints (`auth`, `tasks`, `habits`, etc.).

### 2.2. FastAPI Application (Backend API)

-   **Entry Point**: `main.py` (for Uvicorn/ASGI).
-   **Framework**: FastAPI, Pydantic.
-   **Responsibility**:
    -   Provide a clean, RESTful JSON API for all application resources.
    -   Handle user authentication (registration, JWT issuance) and authorization.
    -   Enforce all business logic and data validation via the Service Layer.
-   **Structure**: Organized into APIRouters (`auth`, `tasks`, `habits`, etc.).

### 2.3. Data Layer (Models & Database)

-   **Definition Files**: `app/models.py`, `app/database.py`.
-   **Technology**: Pure **SQLAlchemy**.
-   **Key Models**: `User`, `Task`, `Habit`, `Movie`.
-   **Coupling**: The data layer is now **decoupled** from any web framework. Models are defined using SQLAlchemy's declarative base. A central `database.py` file manages the engine and session creation, which can be imported and used by any component.

### 2.4. Service Layer

-   **Location**: `app/services/`.
-   **Responsibility**: Encapsulate all business logic and database interactions. Acts as the single bridge between entry points (API, Bot, etc.) and the data models.
-   **Structure**: Composed of classes with static methods (e.g., `TaskService`, `UserService`, `HabitService`) that operate on a standard SQLAlchemy session. The `UserService` is now complete, handling user creation and password management with `passlib`.

### 2.5. Background Workers (RQ & Redis)

-   **Entry Point**: `worker.py`.
-   **Technology**: Redis, RQ (Redis Queue).
-   **Responsibility**: Execute asynchronous tasks in the background.
-   **Coupling**: The worker is now a **standalone process**. It no longer requires a Flask application context. Job functions in `app/tasks_rq.py` create their own database sessions via the central `SessionLocal` factory and use the Service Layer to perform work.

### 2.6. Telegram Bot

-   **Entry Point**: `bot.py`.
-   **Technology**: `python-telegram-bot`.
-   **Responsibility**: Provide a chat-based interface.
-   **Coupling**: The bot is also a **standalone process**. It interacts with the database exclusively through the decoupled Service Layer, using its own database sessions. It does not depend on a Flask context.

---

## 3. Data Flow & Interactions

### Feature: New User Registration

1.  User submits a form on the **Flask** web page (`/auth/register`).
2.  The Flask route handler calls the `app.api_client` to make a `POST` request to the `/auth/register` endpoint on the **FastAPI** service.
3.  The FastAPI endpoint receives the request and calls `UserService.create_user()`.
4.  The `UserService` creates a `User` model object, hashes the password using `passlib`, and commits it to the database.
5.  A successful response is returned to Flask, which then redirects the user to the login page.

### Feature: Create Task via Web

1.  User submits a form on the **Flask** web page (`/tasks/create`).
2.  The Flask route handler makes a `POST` request to the `/tasks/` endpoint on the **FastAPI** service.
3.  The FastAPI endpoint receives the request, validates the data, and calls `TaskService.create_task()`.
4.  The `TaskService` creates a `Task` model object and commits it to the database.
5.  A successful response is returned to Flask, which then redirects the user.

### Feature: List Tasks via Bot

1.  User sends `/task_list_all` to the **Telegram Bot**.
2.  The `task_list` handler enqueues a job for the **RQ Worker**: `q.enqueue('app.tasks_rq.handle_task_list', ...)`.
3.  The RQ Worker picks up the job and executes the `handle_task_list` function.
4.  The function creates a new database session and calls `TaskService.get_tasks_by_user_and_type()` to fetch tasks.
5.  The function formats the task list and enqueues another job to send the message back to the user via the Telegram API.

---

## 4. Architectural Assessment

The system architecture is now **robust, decoupled, and maintainable**. The clear separation of concerns between the frontend (Flask), backend (FastAPI), and core logic (Service/Data layers) aligns with modern application design principles. This structure eliminates the previous inconsistencies and allows for independent development, testing, and scaling of components. The system is in a healthy, fully-migrated state.
