# UniBuzz - College Social Media Web App

UniBuzz is a production-grade college social media web app inspired by Twitter's UI/UX, built with Django.

## Setup Instructions

1. Ensure you have Python 3.8+ installed.
2. Clone/Navigate to the directory `e:\DJANGO\UniTwitter`.
3. Create and activate the virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
5. Apply migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Seed the initial data:
   ```bash
   python manage.py seed_data
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Seeded Login Credentials

### Admin Account
- **URL**: `/admin-panel/login/`
- **Username**: `admin`
- **Password**: `admin123`

### Teacher Accounts
- **URL**: `/teacher/login/`
- **Email**: `alice@campus.edu` | `bob@campus.edu`
- **Password**: `teacher123`

### Student Accounts
- **URL**: `/student/login/`
- **Roll Number**: `CS2021001` (to `CS2021005`)
- **Password**: `student123`

## Feature List

- **Custom Authentication**: Fully session-based authentication bypassing Django's built-in User model.
- **Three Distinct Roles**: Separate models and dashboards for Students, Teachers, and Admins.
- **Twitter-inspired UI/UX**: Dark mode layout with sidebars, dynamic post feeds, and custom CSS.
- **AJAX Likes**: Like posts without reloading the page.
- **Pinned Posts**: Admin announcements are pinned to the top for 24 hours.
- **Notifications**: Instant notification alerts on likes, comments, and follows.
- **Direct Messaging & Groups**: Student-to-student direct chats and group messages.
- **Admin Management**: Full user and post moderation tools.
