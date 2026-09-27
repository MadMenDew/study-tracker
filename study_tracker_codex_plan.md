# Study Tracker Web App — MVP Development Plan

## 1. Project Goal

Build the **simplest possible working study tracker web application** for the Engineering Design 2 AI software assignment.

The priority is to get a complete, functional application working first. Do **not** add unnecessary features until the MVP is fully working, tested, pushed to GitHub, and deployed.

The application must use:

- Python
- Flask
- Supabase
- HTML/CSS
- Git/GitHub
- User authentication
- Database CRUD operations

The app should allow each user to create an account, log in, manage their own study sessions, and log out.

---

## 2. MVP Features

The MVP is complete when the following features work:

### Authentication

- User registration
- User login
- User logout
- Users must be authenticated before viewing or modifying their study data
- Each user must only be able to access their own study sessions

### Study Session CRUD

Users must be able to:

- Create a study session
- View their study sessions
- Edit a study session
- Delete a study session

Each study session should contain:

- Subject
- Minutes studied
- Study date
- Optional notes

---

## 3. Technology Stack

Use the following stack unless there is a strong technical reason not to:

### Backend

- Python
- Flask

### Database and Authentication

- Supabase
- Supabase PostgreSQL database
- Supabase Auth

### Frontend

- HTML
- CSS
- Flask/Jinja templates

Avoid JavaScript unless it is actually necessary.

Do not use React, Node.js, Django, or other frameworks for the MVP.

### Version Control

- Git
- Public GitHub repository

### Deployment

Use a Python-compatible hosting service for Flask.

Recommended:

- Render

Supabase will remain the hosted database/authentication service.

---

## 4. Project Structure

Use a simple structure like this:

```text
study-tracker/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   └── edit.html
│
└── static/
    └── style.css
```

Do not add unnecessary folders or architectural layers unless the application becomes large enough to justify them.

---

## 5. Database Design

Create one application table:

### Table: `study_sessions`

Suggested columns:

| Column | Purpose |
|---|---|
| `id` | Unique session ID |
| `user_id` | Supabase Auth user ID |
| `subject` | Subject or class studied |
| `minutes` | Number of minutes studied |
| `study_date` | Date of study session |
| `notes` | Optional notes |
| `created_at` | Record creation timestamp |

The `user_id` field must associate each study session with the authenticated user.

Do not create separate tables for classes, goals, badges, streaks, or Pomodoro sessions during the MVP.

Supabase Auth should manage users. Do not create a custom users table unless required.

---

## 6. Pages / Routes

Keep the app small.

### `/register`

Purpose:

- Allow a new user to create an account using Supabase Auth

Expected fields:

- Email
- Password

After successful registration, direct the user to login or the dashboard depending on the authentication flow used.

---

### `/login`

Purpose:

- Authenticate an existing user

Expected fields:

- Email
- Password

After successful login:

- Store the required authentication information securely
- Redirect to `/`

---

### `/logout`

Purpose:

- Sign the user out
- Clear local/session authentication state
- Redirect to `/login`

---

### `/`

Purpose:

Main study dashboard.

Authenticated users should be able to:

- See the Add Study Session form
- See their existing study sessions
- Access Edit and Delete actions
- Logout

Unauthenticated users should be redirected to `/login`.

---

### `/add`

Method:

```text
POST
```

Purpose:

Create a new study session.

Expected input:

- subject
- minutes
- study_date
- notes

The session must automatically be associated with the currently authenticated user's `user_id`.

---

### `/edit/<session_id>`

Methods:

```text
GET
POST
```

Purpose:

- GET: Display the current session information
- POST: Save updated session information

Security requirement:

The authenticated user may only edit a record that belongs to their own `user_id`.

---

### `/delete/<session_id>`

Method:

```text
POST
```

Purpose:

Delete one study session.

Security requirement:

The authenticated user may only delete a record belonging to their own `user_id`.

---

## 7. Dashboard Design

Keep the initial UI simple.

Example:

```text
Study Tracker

Welcome, user@email.com

Add Study Session
-----------------

Subject:
[ Physics ]

Minutes:
[ 60 ]

Date:
[ 09/15/2026 ]

Notes:
[ Projectile motion practice ]

[ Add Session ]


Your Study Sessions
-------------------

Physics
60 minutes
September 15, 2026
Projectile motion practice

[ Edit ] [ Delete ]


Programming Languages
45 minutes
September 14, 2026
BNF practice

[ Edit ] [ Delete ]


[ Logout ]
```

The initial design only needs to be functional and easy to navigate.

---

## 8. Environment Variables

Do not hard-code Supabase credentials.

Use a `.env` file.

Example:

```text
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
FLASK_SECRET_KEY=your_secret_key
```

Use `python-dotenv` to load environment variables.

Make sure `.env` is included in `.gitignore`.

Never commit secrets to GitHub.

---

## 9. Python Dependencies

Initial dependencies should stay minimal.

Suggested:

```text
Flask
supabase
python-dotenv
gunicorn
```

Generate/update:

```text
requirements.txt
```

Do not add libraries unless the project actually needs them.

---

# 10. Development Phases

## Phase 1 — Initialize Project

Goal:

Get the Flask application running locally.

Tasks:

- Create project folders/files
- Create Flask application
- Create basic home page
- Create Git repository
- Create public GitHub repository
- Push initial code

Suggested commit:

```text
Create Flask application structure
```

Completion check:

- Flask runs locally
- Browser successfully displays the application

---

## Phase 2 — Connect Supabase

Status: Complete (September 25, 2026). The `study-tracker` Supabase project is
configured, environment variables are stored in the ignored local `.env`, and
`schema.sql` has been applied with row-level security policies. The live
`flask --app app check-supabase` command passed. Authentication is next (Phase 3).

Goal:

Connect Flask to Supabase.

Tasks:

- Create Supabase project
- Add environment variables
- Install Supabase Python package
- Initialize Supabase client in Python
- Create `study_sessions` table

Suggested commit:

```text
Connect Flask application to Supabase
```

Completion check:

- Python can successfully communicate with Supabase

---

## Phase 3 — Authentication

Status: Complete. The user verified the live authentication checks.

Goal:

Complete authentication before building study session CRUD.

Implement:

- Register
- Login
- Logout
- Protected dashboard route

Suggested commit:

```text
Add user registration and authentication
```

Test:

1. Register a new account
2. Logout
3. Login again
4. Attempt to access `/` while logged out
5. Confirm logged-out users are redirected to login

Do not continue until authentication is working reliably.

---

## Phase 4 — Create and Read Study Sessions

Status: Complete. The user verified saving, refresh persistence, and isolation
between accounts.

Goal:

Allow authenticated users to add and view study sessions.

Implement:

### Create

Form fields:

- Subject
- Minutes
- Date
- Notes

When inserting a record:

```text
user_id = current authenticated user ID
```

### Read

Query the database for study sessions belonging only to the authenticated user.

Example logic:

```text
SELECT study_sessions
WHERE user_id == current_user_id
```

Display sessions on the dashboard.

Suggested commit:

```text
Add and display study sessions
```

Completion check:

- User can add a session
- Session appears on dashboard
- Data persists after refreshing
- One user's data is not visible to another user

---

## Phase 5 — Update and Delete

Status: Complete. Live edit/delete was verified by the user; 33 automated tests
pass. Both routes check ownership and scope mutations to the authenticated
user; edits share create validation and deletion uses a CSRF-protected POST.

Goal:

Complete CRUD.

Implement:

- Edit study session
- Delete study session

Suggested commit:

```text
Complete study session CRUD functionality
```

Security checks:

- Verify ownership before editing
- Verify ownership before deleting
- Never trust a session ID from the URL by itself

Completion check:

```text
CREATE ✅
READ   ✅
UPDATE ✅
DELETE ✅
```

---

## Phase 6 — Basic Styling

Status: Complete. Responsive dark styling with pink accents, session cards,
consistent authentication/edit forms, and visible keyboard focus. Desktop and
phone-width dashboard layouts and the login page were visually checked.

Only begin this phase after the full application works.

Goal:

Make the app clean and readable.

Possible style:

- Dark background
- Pink accent color
- Simple cards
- Rounded buttons
- Clean forms

Do not spend significant time on animations or visual polish yet.

Suggested commit:

```text
Improve study tracker interface
```

---

## Phase 7 — Deployment

Goal:

Deploy the working Flask app.

Tasks:

- Confirm `requirements.txt`
- Add Gunicorn
- Configure production start command
- Deploy Flask application
- Add production environment variables
- Connect deployed app to Supabase
- Test registration
- Test login
- Test CRUD
- Test logout

Important:

The deployed application must work independently of localhost.

Suggested commit:

```text
Prepare application for deployment
```

---

## Phase 8 — README

Create a README containing:

### Project Name

Study Tracker

### Description

A simple web application that allows authenticated users to record and manage study sessions.

### Features

- User registration
- User login
- User logout
- Add study sessions
- View study sessions
- Edit study sessions
- Delete study sessions
- User-specific data

### Technologies

- Python
- Flask
- HTML
- CSS
- Supabase
- PostgreSQL
- Git/GitHub

### Setup Instructions

Explain:

1. Clone repository
2. Create virtual environment
3. Install requirements
4. Create `.env`
5. Add Supabase credentials
6. Run Flask app

### Deployment

Include the live application link.

---

# 11. MVP Acceptance Criteria

Do not consider the MVP finished until every item below works.

## Authentication

- [ ] User can register
- [ ] User can login
- [ ] User can logout
- [ ] Logged-out users cannot access the dashboard

## Database

- [ ] Supabase connection works
- [ ] `study_sessions` table exists
- [ ] Study sessions persist after page refresh

## CRUD

- [ ] User can create a study session
- [ ] User can view study sessions
- [ ] User can edit a study session
- [ ] User can delete a study session

## User Data Security

- [ ] Every study session includes the correct `user_id`
- [ ] Users only see their own study sessions
- [ ] Users cannot edit another user's study sessions
- [ ] Users cannot delete another user's study sessions

## Project Requirements

- [ ] Public GitHub repository exists
- [ ] Meaningful commits are pushed throughout development
- [ ] README is complete
- [ ] Application is deployed
- [ ] Deployed application works

---

# 12. DO NOT OVERBUILD THE MVP

Do not implement these features until all MVP acceptance criteria are complete:

- Pomodoro timer
- Classes table
- Goals
- Repeating goals
- Study streaks
- Badges
- Awards
- Confetti
- Charts
- Total study analytics
- Friends
- Social feeds
- Public/private class settings
- Notifications
- Advanced dashboards

Do not refactor working code simply to make it more architecturally complex.

Prefer:

- Simple
- Readable
- Functional
- Easy to debug

over:

- Clever
- Abstract
- Over-engineered

---

# 13. Feature Expansion Order

Only after the MVP is deployed and stable, add optional features one at a time.

Recommended order:

```text
MVP
 ↓
Pomodoro Timer
 ↓
Classes
 ↓
Study Goals
 ↓
Total Study Time
 ↓
Streaks
 ↓
Badges / Awards
 ↓
Confetti
 ↓
Charts
 ↓
Recurring Goals
 ↓
Social Features
```

After each new feature:

1. Test it
2. Commit it
3. Push it
4. Confirm existing features still work

---

# 14. Coding Guidance for Codex

When implementing this project:

- Make the smallest reasonable change needed for the current task.
- Do not add features that were not requested.
- Keep Python logic straightforward and readable.
- Prefer built-in Python functionality where reasonable.
- Keep dependencies minimal.
- Use Flask/Jinja templates instead of introducing frontend frameworks.
- Protect authenticated routes.
- Validate all user input.
- Verify record ownership before update/delete operations.
- Keep credentials in environment variables.
- Never expose secrets in source code.
- Do not remove working functionality while adding new features.
- Test each phase before starting the next phase.
- Preserve the simple project structure unless additional complexity becomes necessary.

When uncertain, prioritize a working MVP over additional features.

---

# 15. Definition of Done

The project is considered complete when:

```text
User registers
      ↓
User logs in
      ↓
User reaches dashboard
      ↓
User adds study session
      ↓
Session is stored in Supabase
      ↓
User sees saved session
      ↓
User edits session
      ↓
Changes persist
      ↓
User deletes session
      ↓
Record is removed
      ↓
User logs out
```

And:

```text
Different user logs in
      ↓
Cannot see or modify the first user's data
```

Once this flow works on the deployed application, the core project is finished.

Do not delay deployment in order to add optional features.
