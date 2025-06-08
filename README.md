# Library Management System

A simple web-based Library Management System built with **Python**, **Flask**, **SQLite**, **HTML**, **CSS**, and **Bootstrap**.

It allows users to **borrow, return, reserve books**, and **view their borrowing history**. Admins have extended privileges such as **managing books**, **managing users**, and **viewing all transactions**.

## Table of Contents

- [Library Management System](#library-management-system)
- [Technologies Used](#technologies-used)
- [Team Members & Roles](#team-members--roles)
- [Features](#features)
- [Installation & Setup](#how-to-run-the-project)
- [Project Structure](#project-structure)

## Technologies Used

- **Backend:** Python, Flask  
- **Database:** SQLite  
- **Frontend:** HTML, CSS, Bootstrap  
- **Version Control:** Git & GitHub  

## Team Members & Roles

- **Saeeda** – Uploaded the project to GitHub, created documentation, and integrated all modules  
- **Rukhsar** – Worked on Bootstrap and frontend design (HTML/CSS)  
- **Raihana** – Designed the database and created the schema (tables and connections)  

## Features

-  User Registration & Login (User/Admin roles)
-  Search books by title or author
-  Borrow, Return, and Reserve books
-  View individual borrowing history
-  Admin Dashboard:
   - View total, available, borrowed, and returned books
   - View all transactions
   - Manage books (Add, Edit, Delete)
   - Manage users (View and Delete)

## Project Structure

- library_project
  - app.py
  - library.db
  - schema.sql
  - models
    - database.py
  - routes
    - auth_routes.py  
    - book_routes.py
    - main_routes.py
  - templates
    - base.html
    - dashboard.html
    - ...
  - README.md

##  How to Run the Project

### Prerequisites

- Python 3 installed
- A Python IDE (e.g., VS Code or PyCharm)
- Internet connection (to install Flask)

### Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/saeeda23/library_project.git
cd library_project

# 2. Install Flask (command prompt)
pip install flask

# 3. Set up the database (command prompt)
sqlite3 library.db < schema.sql

# 4. Run the Flask application
python app.py (In Python IDE)

# 5. Follow the link that appears after the app.py
http://127.0.0.1:5000


