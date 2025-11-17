
# System Architecture

## 1. Overview

This project uses a simple three-part structure: a Django frontend for user input, a FastAPI backend for handling requests, and a scheduling module that assigns subjects to slots and allocates halls based on capacity. The system is designed for small-scale exam scheduling and provides a clear separation between UI, API, and core logic.

## 2. System Components

- **Frontend (Django):**
  - Collects subjects, groups, and halls
  - Sends data to backend
  - Displays generated timetable and hall allocations

- **Backend (FastAPI):**
  - Receives requests from frontend
  - Validates input
  - Calls scheduling and hall allocation functions
  - Returns JSON responses

- **Scheduling Module (Core Python):**
  - Assigns subjects to slots
  - Ensures no conflicting subjects share a slot
  - Allocates students into halls based on capacity

## 3. Data Flow

**Input Flow:**
- User enters subjects, groups, and halls in the frontend
- Data is sent to the backend API
- Backend validates and stores the data temporarily

**Timetable Generation Flow:**
- Frontend triggers "Generate"
- Backend calls scheduling function
- Scheduling module assigns subjects to slots
- Hall allocation function assigns students to halls
- Backend returns results
- Frontend displays the timetable and allocations

## 4. Scheduling Logic

Subjects are placed into available days and slots. The system checks for conflicts, ensuring subjects from the same group do not share a slot. If a conflict is found, it tries another slot. Simple backtracking is used when necessary. This approach works well for small and medium-sized exam schedules.

## 5. Hall Allocation Logic

The system counts how many students are taking each subject. Halls are sorted by capacity, and students are assigned starting from the largest hall. The process ensures no hall exceeds its capacity and creates a final allocation list for each slot.

## 6. Folder Structure

```
backend/
  app/
    core/      ← scheduling + hall allocation
    api/       ← FastAPI routes
frontend/
  django_ui/   ← UI templates + views
```

## 7. Flowchart

```
┌─────────────────────────────────────────────────────────────────┐
│                    Exam Timetable Generator                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   User Enters Configuration                     │
│              (Days, Slots, Subjects, Halls, Groups)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django Frontend (UI)                         │
│                    POST /api/config                             │
│                    POST /api/groups                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                           │
│                  Validate & Store Config                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  User Clicks "Generate"                         │
│                   POST /api/generate                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Timetable Scheduler                           │
│              Build Conflict Graph from Groups                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               Pick Next Subject (MRV Heuristic)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Valid Slot for │
                    │    Subject?     │
                    └─────────────────┘
                         /         \
                       No           Yes
                      /               \
                     ▼                 ▼
          ┌──────────────────┐   ┌────────────────────────┐
          │    Backtrack     │   │   Assign Slot and      │
          │  Try Another     │   │   Forward Check        │
          │      Slot        │   │ (Remove from Conflicts)│
          └──────────────────┘   └────────────────────────┘
                     │                      │
                     └──────────┬───────────┘
                                ▼
                      ┌───────────────────┐
                      │  All Subjects     │
                      │    Assigned?      │
                      └───────────────────┘
                           /         \
                         No           Yes
                        /               \
                       ▼                 ▼
            ┌────────────────┐   ┌──────────────────────┐
            │ Continue Loop  │   │   Hall Allocator     │
            │ Next Subject   │   │  For Each Time Slot  │
            └────────────────┘   └──────────────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │ Count Students per    │
                              │ Subject in Each Slot  │
                              └───────────────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │  Greedy Allocation    │
                              │ Fill Halls by Capacity│
                              │  (Respect Limits)     │
                              └───────────────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │ Sufficient Capacity?  │
                              └───────────────────────┘
                                     /         \
                                   No           Yes
                                  /               \
                                 ▼                 ▼
                    ┌──────────────────┐   ┌──────────────────┐
                    │  Return Error    │   │ Return Timetable │
                    │ (422 Response)   │   │ and Hall         │
                    └──────────────────┘   │ Allocations      │
                                           └──────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────────┐
                                        │  Display in Frontend  │
                                        │  Show Tables + Export │
                                        └───────────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────────┐
                                        │   User Downloads CSV  │
                                        │   GET /api/export/csv │
                                        └───────────────────────┘
```

## 8. Limitations

- No database (in-memory storage)
- Not optimized for large inputs
- Simple algorithm, not meant for large-scale timetabling
- No authentication/security implemented

## 9. Conclusion

This project demonstrates a basic scheduling architecture using separate UI, API, and logic layers. It is suitable for small-scale exam scheduling and provides a clear, maintainable structure for future improvements.