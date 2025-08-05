# AI SVAT Project

## Overview

**AI SVAT** is a web application for security vulnerability assessment and testing. It features a Django backend and an Angular frontend:

- **Backend:** Django, MySQL, Djoser (JWT authentication), Channels (real-time), python-decouple (env vars)
- **Frontend:** Angular (responsive UI)

---

## Prerequisites

- Python 3.8+
- Node.js 18.x or later
- MySQL 8.0
- Docker (optional, for MySQL/MailHog)
- npm (for Angular)

---

## Setup Instructions

### Backend (Django)

1. **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd ai_svat
    ```

2. **Set Up Virtual Environment**
    ```bash
    python -m venv venv
    # On Unix/macOS:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    Ensure `requirements.txt` includes: `django`, `djangorestframework`, `djoser`, `django-cors-headers`, `channels`, `mysqlclient`, `python-decouple`.

4. **Configure Environment Variables**

    Create a `.env` file in the project root:
    ```
    EMAIL_HOST=localhost
    EMAIL_PORT=1025
    EMAIL_HOST_USER=dev@example.com
    EMAIL_HOST_PASSWORD=password

    MYSQL_HOST=localhost
    MYSQL_DATABASE=vulnerability_db
    MYSQL_USER=root
    MYSQL_PORT=3307
    MYSQL_PASSWORD=root@123

    ```

5. **Set Up MySQL Database**

    - **Using Docker (recommended):**
      ```bash
      docker run --name aisvat \
         -e MYSQL_ROOT_PASSWORD=root@123 \
         -e MYSQL_DATABASE=vulnerability_db \
         -e MYSQL_USER=root \
         -e MYSQL_PASSWORD=root@123 \
         -p 3306:3306 -d mysql:8.0
      ```
    - **Or install MySQL locally** and create a database named `vulnerability_db`.

6. **Run Migrations**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7. **Start Django Development Server**
    ```bash
    python manage.py runserver
    ```
    Backend runs at [http://localhost:8000](http://localhost:8000).

---

### Frontend (Angular)

1. **Navigate to Frontend Directory**
    ```bash
    cd <frontend-directory>  # Where angular.json is located
    ```

2. **Install Dependencies**
    ```bash
    npm install
    ```

3. **Start Angular Development Server**
    ```bash
    ng serve
    ```
    Frontend runs at [http://localhost:4200](http://localhost:4200).

---

## Additional Setup

### MailHog for Email Testing

- Run MailHog:
  ```bash
  docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
  ```
- Access MailHog UI at [http://localhost:8025](http://localhost:8025).

### CORS Configuration

- Development: `CORS_ALLOW_ALL_ORIGINS = True`
- Production: Use `CORS_ALLOWED_ORIGINS` or `CORS_ALLOWED_ORIGIN_REGEXES` to restrict access.

---

## Project Structure

```
ai_svat/           # Django project settings and WSGI config
  svatapp/         # Custom Django app (models, views, email templates)
  media/           # Uploaded files (PDFs, images, code)
  templates/       # Django templates

<frontend-directory>/
  src/             # Angular source code
  node_modules/    # Node.js dependencies
  angular.json     # Angular config
```

---

## Running the Application

1. Start MySQL (Docker or local)
2. Run Django backend: `python manage.py runserver`
3. Run Angular frontend: `ng serve`
4. Access frontend at [http://localhost:4200](http://localhost:4200) (communicates with backend at [http://localhost:8000](http://localhost:8000))

---

## Authentication

- Uses Djoser with JWT.
- Register: `/auth/users/`
- Activate: via email link (see MailHog)
- Obtain JWT: `/auth/jwt/create/`

---

## File Uploads

- Supported: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.py`, `.js`, `.java`, `.c`, `.cpp`, `.cs`, `.php`, `.rb`
- Stored in `media/` directory

---

## Logging

- Console output for `vulnerability_app` logger at INFO level

---

## Notes

- **Security:** Replace the provided `SECRET_KEY` with a secure one for production (use `django.core.management.utils.get_random_secret_key()`).
- **Debug:** `DEBUG = True` for development; set to `False` in production.
- **Chroma:** Backend connects to Chroma at `CHROMA_HOST` (default: `localhost`) and `CHROMA_PORT` (default: `6003`). Ensure Chroma is running if required.

---

## Troubleshooting

- **Database:** Ensure MySQL is running and env vars are correct.
- **CORS:** Confirm `corsheaders` middleware and allowed origins.
- **Email:** Make sure MailHog is running and accessible at [http://localhost:8025](http://localhost:8025).
