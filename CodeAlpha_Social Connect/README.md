# Social Connect &bull; Social Media Platform

A modern, responsive, and fully-featured Social Media Platform built with **Python**, **Django**, and **MySQL** for **CodeAlpha Task 2**.

---

## 🌟 Key Features

1. **Authentication & Authorization**
   - Secure registration, login, and logout using Django's built-in authentication system.
   - Strong password hashing with server-side validation.
   - Protected routes with `@login_required` decorators and CSRF protection across all forms.
   - Authorization checks ensuring users can only edit or delete their own posts and comments.

2. **User Profiles**
   - User profiles with username, first/last name, bio, location, join date, and avatar picture.
   - Profile image upload with default SVG avatar fallback.
   - Profile editing dashboard.

3. **Posts Management**
   - Create posts with rich text and optional image attachments.
   - Client-side image upload preview with removal option.
   - Edit and delete own posts with dropdown menu and confirmation dialogs.
   - Full post discussion view (`/post/<id>/`).

4. **Feed & Content Discovery**
   - **Global Feed**: Real-time chronological timeline of posts from all platform users.
   - **Following Feed**: Personalized stream featuring posts exclusively from followed creators.
   - Instant search filtering by post content, author username, or name.

5. **Interactive Likes System**
   - One-click like / unlike toggle with responsive micro-animations (heart pulse).
   - Real-time like counter updates via Vanilla JavaScript Fetch API.
   - Database constraint (`UniqueConstraint(fields=['post', 'user'])`) preventing duplicate likes.

6. **Threaded Comments**
   - Add thoughtful comments directly from the feed or the post detail page.
   - Inline comment submission with instant DOM append.
   - Comment author and post author moderation/deletion rights.

7. **Follow / Unfollow System**
   - Follow and unfollow users directly from feed cards, profile pages, or explore widgets.
   - Live updates to follower and following counts.
   - Database constraint (`UniqueConstraint(fields=['follower', 'following'])`) preventing duplicate follows.
   - Self-follow prevention enforced at both model validation and view levels.
   - Followers and Following user list pages.

8. **Modern, Responsive UI**
   - Sleek dark theme with glassmorphism cards (`backdrop-filter: blur`), curated color system (indigo, violet, pink, and emerald accents).
   - Clean modern typography with Google Fonts (*Plus Jakarta Sans*).
   - Fully responsive design: 3-column desktop layout, collapsible tablet layout, and sticky bottom navigation bar on mobile devices.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.14+, Django 6.1
- **Database:** MySQL / MariaDB (configured via environment variables)
- **Frontend:** HTML5 (Django Templates), Vanilla CSS, Vanilla JavaScript (ES6+ Fetch API)
- **Database Driver:** PyMySQL with Cryptography

---

## 📁 Project Structure

```
Social Connect/
│── social_connect/         # Django Project configuration
│   ├── __init__.py         # PyMySQL driver setup & database version compatibility
│   ├── settings.py         # App configuration & .env integration
│   ├── urls.py             # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│── social/                 # Core Social application
│   ├── management/         # Management commands (e.g., seed_data)
│   ├── migrations/         # Database migrations
│   ├── models.py           # Profile, Post, Comment, Like, Follow models
│   ├── forms.py            # User registration, login, profile, post & comment forms
│   ├── views.py            # Complete business logic & authorization
│   ├── urls.py             # Application URL routes
│   ├── signals.py          # Automatic Profile creation on User save
│   └── tests.py            # Automated unit and integration test suite
│── templates/              # Django HTML templates
│   ├── base.html           # Master layout & responsive navigation
│   ├── sidebar.html        # Desktop sidebar menu
│   ├── messages.html       # Toast notification system
│   └── social/             # App-specific templates (feed, profile, etc.)
│── static/                 # Static assets
│   ├── css/style.css       # Main stylesheet
│   ├── js/main.js          # Vanilla JavaScript interactions
│   └── images/             # SVGs (logo, default avatar)
│── media/                  # User uploads (avatars & post attachments)
│── .env                    # Environment variables (DB credentials, secret key)
│── .env.example            # Environment variables template
│── requirements.txt        # Python package dependencies
│── test_live_server.py     # Live server end-to-end integration test runner
└── manage.py
```

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- Python 3.10+ installed
- MySQL Server or XAMPP MySQL running on `localhost:3306`

### 2. Clone / Open Directory
```bash
cd "d:\Social Connect"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root (or copy from `.env.example`):
```ini
SECRET_KEY=your-secure-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=social_connect_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 5. Create MySQL Database
Ensure your MySQL server is running, then run:
```sql
CREATE DATABASE IF NOT EXISTS social_connect_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Run Database Migrations
```bash
python manage.py migrate
```

### 7. Seed Sample Data (Recommended)
Populate the database with realistic sample users, profiles, posts, comments, likes, and follows:
```bash
python manage.py seed_data
```

### 8. Run the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open your browser and navigate to: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 👥 Demo User Credentials

The `seed_data` command creates ready-to-test accounts:

| Username | Password | Role / Details |
| :--- | :--- | :--- |
| **testuser** | `Password123!` | Test Evaluator Account |
| **alex_dev** | `Password123!` | Software Engineer Profile |
| **sophia_ai** | `Password123!` | AI Researcher Profile |
| **marcus_v** | `Password123!` | UI/UX Designer Profile |

*(You can also click "Create an account" on the login page to register a brand new user.)*

---

## 🧪 Testing

### 1. Automated Django Test Suite
Runs all model constraint tests, permission validations, view tests, and form validations:
```bash
python manage.py test social
```
*Result: 8/8 tests pass successfully.*

### 2. Live Server End-to-End Test Suite
Tests live HTTP flows against the running server (session login, feed extraction, post creation, AJAX likes, comments, and follows):
```bash
python test_live_server.py
```
*Result: All 9 live server steps execute and verify with status 200.*

---

## 🔒 Security & Database Integrity

- **Database Constraints:** 
  - `unique_post_like`: Enforces at database level that a user can only like a post once.
  - `unique_user_follow`: Enforces at database level that a user can only follow another user once.
  - Self-follow rejection: Enforced at both model level (`clean()`) and view level.
- **CSRF Protection:** Integrated across all forms and Fetch API calls with standard `csrftoken` cookie verification.
- **Authorization:** `edit_post`, `delete_post`, and `delete_comment` perform strict author checks before making database changes.
- **Environment Confidentiality:** Passwords and keys are never hardcoded and are loaded through `.env`.
