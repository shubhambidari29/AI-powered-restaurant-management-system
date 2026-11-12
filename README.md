# Foodora – Restaurant Management System

Foodora is a web-based restaurant management and table reservation system built with Django and PostgreSQL. Customers can explore the menu, reserve tables, and get AI-powered food recommendations.

## Features

- User authentication and role management
- Food menu management
- Table reservations
- Admin and staff dashboards
- REST API
- AI food assistant using Google Gemini
- Automated tests

## Technologies

- Python and Django
- PostgreSQL
- Django REST Framework
- HTML, CSS, JavaScript, Bootstrap
- Google Gemini API

## Installation

```bash
git clone https://github.com/shubhambidari29/AI-powered-restaurant-management-system.git
cd AI-powered-restaurant-management-system
uv sync
```

Create a `.env` file with your Django secret key, Gemini API key, and PostgreSQL credentials.

Run migrations and start the server:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

## Run Tests

```bash
uv run python manage.py test
```

