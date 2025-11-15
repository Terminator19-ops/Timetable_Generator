
# Exam Timetable Generator

A simple exam scheduling system with hall allocation.

## 1. Introduction

This project automates the creation of exam timetables by assigning subjects to available days and slots, and then allocating students into halls based on capacity. It was built as part of a college course on AI and software engineering. The system includes a simple backend API and a web interface for input and viewing results.

## 2. Features

- Subject scheduling
- Group conflict checking
- Hall allocation
- Simple input forms
- JSON-based API
- CSV export
- Basic error handling

## 3. Technologies Used

- Python
- Django (UI)
- FastAPI (API)
- HTML/CSS/JS

## 4. How to Run

### Install dependencies

```powershell
pip install fastapi django uvicorn
```

### Run backend

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

### Run frontend

```powershell
cd frontend/django_ui
python manage.py migrate
python manage.py runserver 8080
```

### Access the UI

Open your browser and go to:

```
http://localhost:8080
```

## 5. System Overview

The frontend collects inputs for subjects, student groups, and halls. It sends these details to the backend using simple API calls. The backend generates a timetable using basic constraint checking to avoid group conflicts, then allocates students to halls based on available capacity. The frontend displays the generated timetable and hall allocations, and allows exporting results to CSV.

## 6. Scheduling Logic

The system checks that conflicting subjects do not end up in the same slot. It tries different slot assignments until a valid arrangement is found, using basic backtracking if needed. This approach works well for small and medium-sized exam schedules.

## 7. Hall Allocation Logic

For each subject, the system calculates the total number of students. It assigns students to halls starting from the largest available hall, ensuring no hall exceeds its capacity. Allocations are made slot by slot and shown in the results.

## 8. Example Input/Output

**Example Input:**

```json
{
   "subjects": ["Math", "Physics"],
   "groups": [
      {"name": "G1", "subjects": ["Math"], "size": 25},
      {"name": "G2", "subjects": ["Physics"], "size": 25}
   ],
   "days": 1,
   "slots_per_day": 2,
   "halls": [
      {"name": "Hall-1", "capacity": 60}
   ]
}
```

**Sample Timetable Output:**

| Day | Slot | Subject  |
|-----|------|----------|
| 1   | 1    | Math     |
| 1   | 2    | Physics  |

**Sample Hall Allocation:**

| Hall   | Day | Slot | Subject  | Students |
|--------|-----|------|----------|----------|
| Hall-1 | 1   | 1    | Math     | 25       |
| Hall-1 | 1   | 2    | Physics  | 25       |

## 9. Limitations

- In-memory storage only
- No authentication
- Not optimized for large datasets
- Basic scheduling strategy (not advanced algorithms)

## 10. Conclusion

This project demonstrates a simple approach to automating exam scheduling using Python and a web-based interface. It covers basic constraint checking and hall capacity assignment suitable for small-scale use.


