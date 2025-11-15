# Core Algorithm Documentation

## 1. Introduction

This algorithm handles the creation of exam timetables for student groups. Its objective is to assign each subject to a valid time slot and allocate students to available halls while satisfying the required constraints. 

## 2. Problem Constraints

- Each subject must be assigned to exactly one slot
- No group can have two exams scheduled at the same time
- Halls have limited seating capacity
- All students taking a subject must be seated
- The total number of slots (days × slots per day) must be enough for all subjects

## 3. Scheduling Approach (High-Level Description)

A basic backtracking method is used for scheduling. The algorithm tries to place subjects into slots one by one. If a conflict is detected (such as a group having two exams at the same time), it tries the next available slot. If no slot works for a subject, the algorithm backtracks to try different arrangements. This approach works well for small datasets and is simple to implement and understand.

## 4. Why Backtracking? (Justification)

Backtracking was selected because it provides a clear and deterministic way to explore possible subject–slot assignments while respecting constraints. It ensures that if a feasible timetable exists, the algorithm will eventually find it. Given the scale of the problem and the size of typical academic datasets, backtracking offers a good balance between implementation simplicity and reliability without requiring more complex optimization frameworks.

## 5. Hall Allocation Logic (Simple Description)

The algorithm counts how many students are taking each subject. Halls are sorted by capacity, and the largest halls are filled first. The process ensures that no hall exceeds its capacity and continues until all students are placed for each slot.

## 6. Time Complexity

**Scheduling (Backtracking):**
- Worst-case: O(S × D × Slots) for trying combinations
- Efficient for small numbers of subjects in practice

**Hall Allocation:**
- Sorting halls: O(H log H)
- Allocation loop: O(H × Subjects)

## 7. Space Complexity

**Scheduling:**
- Stores assignments: O(Subjects)
- Temporary slot choices: O(Days × Slots)

**Hall Allocation:**
- Student counts: O(Subjects)
- Final allocation list: O(Halls × Slots)

## 8. Example Walkthrough

**Input:** 2 subjects, 1 day, 2 slots
- Step 1: Place "Math" in slot 1
- Step 2: Place "Physics" in slot 2
- Step 3: Allocate students for each subject to available halls

## 9. Limitations of the Algorithm

- Slower for very large numbers of subjects
- No advanced optimization or heuristic pruning
- Assumes input size is moderate
- Single-threaded, simple design

## 10. Conclusion

The algorithm meets the requirements for generating basic exam timetables and demonstrates a practical implementation of constraint-based scheduling.