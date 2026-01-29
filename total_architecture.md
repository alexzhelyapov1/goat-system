# Goat System: Architecture Report

This document provides a detailed analysis of the Goat System's architecture, a hybrid application combining a Flask frontend with a FastAPI backend.

## 1. Overall Architecture Summary

The Goat System is a multi-headed application with four main entry points:

1.  **Flask Web App**: Serves HTML pages, handles user sessions, and acts as a client to the FastAPI backend. This is the primary user-facing web interface.
2.  **FastAPI App**: Provides a RESTful JSON API for the application's business logic (managing tasks, habits, etc.). It is intended to be the "backend for the frontend."
3.  **Telegram Bot**: Offers a conversational interface for interacting with the system, primarily for managing tasks. It operates independently of the FastAPI service.
4.  **RQ Worker**: A background process that executes asynchronous jobs, such as sending Telegram messages or creating tasks, which are enqueued by other parts of the system (mainly the bot).

The entire system is built around a single, shared database schema defined using **Flask-SQLAlchemy**. This tight coupling of the data layer to the Flask ecosystem is the most significant architectural characteristic, as all four components depend on it, either directly or indirectly.

![Architecture Diagram](https://i.imgur.com/8f1qL3j.png)

*This is a simplified conceptual diagram. The "Flask App Context" is not a physical server but a logical construct that the Bot and Worker processes create to gain access to the database and configuration.*

---

## 2. System Components

### 2.1. Flask Web Application (Frontend Server)

-   **Entry Point**: `run.py` (for Gunicorn/WSGI).
-   **Framework**: Flask, Flask-Login.
-   **Responsibility**:
    -   Render Jinja2 templates to provide the user interface.
    -   Manage user authentication and sessions via Flask-Login.
    -   For most features (Tasks, Habits), it acts as a pure client, making API calls to the FastAPI backend using an `httpx`-based client (`app.api_client`).
    -   **CRITICAL**: For user registration, it bypasses the API and interacts directly with the database.
-   **Structure**: Organized into Blueprints (`auth`, `tasks`, `habits`, etc.).

### 2.2. FastAPI Application (Backend API)

-   **Entry Point**: `main.py` (for Uvicorn/ASGI).
-   **Framework**: FastAPI, Pydantic.
-   **Responsibility**:
    -   Provide a clean, RESTful JSON API for core application resources.
    -   Handle authentication via JWTs (issuing tokens at the `/token` endpoint).
    -   Enforce business logic and data validation.
    -   Delegate all database operations to the Service Layer.
-   **Structure**: Organized into APIRouters (`tasks`, `habits`, etc.), which mirror the Flask blueprints.
-   **INCONSISTENCY**: Lacks a user creation endpoint, making it reliant on the Flask app for user registration.

### 2.3. Data Layer (Models & Database)

-   **Definition File**: `app/models.py`.
-   **Technology**: SQLAlchemy, but defined and managed via **Flask-SQLAlchemy**.
-   **Key Models**: `User`, `Task`, `Habit`, `Movie`.
-   **Coupling**: This is the system's core. The `User` model has direct dependencies on Flask-Login (`UserMixin`) and Werkzeug (for password hashing). All other components use these Flask-specific models to interact with the database. This prevents the FastAPI service from being a truly standalone component.

### 2.4. Service Layer

-   **Location**: `app/services/`.
-   **Responsibility**: Encapsulate all business logic and database interactions. Acts as a bridge between the API/entry points and the data models.
-   **Structure**: Composed of classes with static methods (e.g., `TaskService`, `HabitService`). These services take a database session as an argument, allowing them to be used by both FastAPI (via dependencies) and other components (via a Flask app context).
-   **INCONSISTENCY**: The `UserService` is minimal and incomplete, lacking a `create_user` method. The password verification relies on `werkzeug`, a Flask dependency.

### 2.5. Background Workers (RQ & Redis)

-   **Entry Point**: `worker.py`.
-   **Technology**: Redis, RQ (Redis Queue).
-   **Responsibility**: Execute long-running or asynchronous tasks in the background.
-   **Coupling**: The worker process is entirely dependent on the Flask application. Each job function defined in `app/tasks_rq.py` creates a new Flask app instance to get an application context, which is needed for configuration and database access. It does not communicate with the FastAPI service.

### 2.6. Telegram Bot

-   **Entry Point**: `bot.py`.
-   **Technology**: `python-telegram-bot`.
-   **Responsibility**: Provide a chat-based interface.
-   **Coupling**: Like the worker, the bot is heavily coupled to the Flask ecosystem.
    -   It runs within a Flask application context to gain access to the database.
    -   It reads data directly from the database using `User.query` and `Task.query` (bypassing the service layer for reads).
    -   For write operations, it enqueues jobs for the RQ worker.
    -   It does not communicate with the FastAPI service.

---

## 3. Data Flow & Interactions

### Feature: New User Registration

1.  User submits a form on the **Flask** web page (`/auth/register`).
2.  The Flask route handler receives the request.
3.  **It directly creates a `User` model object, hashes the password, and commits it to the database using `db.session.commit()`.**
4.  The FastAPI service is **not involved**.

### Feature: Create Task via Web

1.  User submits a form on the **Flask** web page (`/tasks/create`).
2.  The Flask route handler receives the request.
3.  The handler makes a `POST` request to the `/tasks/` endpoint on the **FastAPI** service, sending the form data as JSON.
4.  The FastAPI endpoint receives the request, validates the data using the `TaskCreate` Pydantic schema.
5.  The endpoint calls `TaskService.create_task()`.
6.  The `TaskService` creates a `Task` model object and commits it to the database.
7.  A successful response is returned to Flask, which then redirects the user.

### Feature: List Tasks via Bot

1.  User sends `/task_list_all` to the **Telegram Bot**.
2.  The `task_list` handler in `app/telegram_bot.py` is triggered.
3.  The handler enqueues a job for the **RQ Worker**: `q.enqueue('app.tasks_rq.handle_task_list', ...)`.
4.  The RQ Worker picks up the job and executes the `handle_task_list` function.
5.  The function (inside a Flask app context) calls `TaskService.get_tasks_by_user_and_type()` to fetch tasks from the database.
6.  The function formats the task list into a string and enqueues another job: `q.enqueue('app.tasks_rq.send_telegram_message', ...)`.
7.  The RQ Worker executes `send_telegram_message`, which sends the final message back to the user via the Telegram API.

---

## 4. Architectural Assessment

This report serves as the foundation for the migration assessment. The next step is to analyze these findings to provide a clear answer on the success of the migration and recommendations for improvement.
