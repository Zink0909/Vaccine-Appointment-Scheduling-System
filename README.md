# Vaccine Reservation Scheduling System

A command-line vaccine reservation system built with Python and SQLite, supporting caregiver availability management, patient appointment booking, and secure user authentication.  
This project emphasizes database-backed application design, transactional consistency, and robust input validation.

---

## Features

### User Management
- Create and authenticate **patients** and **caregivers**
- Passwords are securely stored using **salted hashing**
- Enforced **strong password policy** (length, case, digits, special characters)

### Caregiver Operations
- Upload daily availability
- View scheduled appointments
- Cancel appointments (extra credit)

### Patient Operations
- Search caregiver availability by date
- Reserve vaccine appointments
- View appointment history
- Cancel appointments (extra credit)

### Appointment System
- Automatically assigns caregivers based on **alphabetical priority**
- Ensures:
  - One caregiver per day
  - Sufficient vaccine doses
  - Consistent database updates (availability, appointments, vaccines)

---

## Key Concepts & Skills Demonstrated

- **Relational Database Design**
  - Entity-Relationship (ER) modeling
  - Primary & foreign keys
  - One-to-many relationships
- **SQLite with Python**
  - Parameterized SQL queries
  - Transaction handling
  - Constraint enforcement
- **Backend Application Logic**
  - Session state management (login/logout)
  - Role-based access control
  - Robust error handling
- **Security Best Practices**
  - Password salting and hashing
  - Input validation
- **CLI Application Design**
  - Deterministic output formatting (autograder-safe)
  - Defensive parsing of user commands

---

## Database Schema

**Tables**
- `Caregivers(username, salt, hash)`
- `Patients(username, salt, hash)`
- `Availabilities(date, caregiver_username)`
- `Vaccines(name, doses)`
- `Appointments(id, date, caregiver_username, patient_username, vaccine_name)`
