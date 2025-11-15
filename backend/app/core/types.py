"""
Type definitions for the exam scheduling system.
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class StudentGroup:
    """Represents a group of students with common subjects."""
    name: str
    subjects: List[str]
    size: int
    
    def __post_init__(self):
        if self.size <= 0:
            raise ValueError(f"Group {self.name} must have positive size")
        if not self.subjects:
            raise ValueError(f"Group {self.name} must have at least one subject")


@dataclass
class TimetableConfig:
    """Configuration for timetable generation."""
    days: int
    slots_per_day: int
    subjects: List[str]
    groups: List[StudentGroup]
    random_seed: Optional[int] = None
    
    def __post_init__(self):
        if self.days <= 0:
            raise ValueError("Days must be positive")
        if self.slots_per_day <= 0:
            raise ValueError("Slots per day must be positive")
        if not self.subjects:
            raise ValueError("Must have at least one subject")
        if not self.groups:
            raise ValueError("Must have at least one group")
        
        # Check for duplicate subjects
        if len(self.subjects) != len(set(self.subjects)):
            raise ValueError("Duplicate subjects found")
    
    @property
    def total_slots(self) -> int:
        return self.days * self.slots_per_day


@dataclass
class ExamSlot:
    """Represents a single exam slot in the timetable."""
    day: int
    slot: int
    subject: str
    
    def __str__(self) -> str:
        return f"Day {self.day + 1}, Slot {self.slot + 1}: {self.subject}"


@dataclass
class TimetableResult:
    """Result of timetable generation."""
    assignments: List[ExamSlot]
    config: TimetableConfig
    
    def get_assignment(self, day: int, slot: int) -> Optional[str]:
        """Get subject assigned to a specific day and slot."""
        for assignment in self.assignments:
            if assignment.day == day and assignment.slot == slot:
                return assignment.subject
        return None
    
    def get_subject_slot(self, subject: str) -> Optional[Tuple[int, int]]:
        """Get (day, slot) for a given subject."""
        for assignment in self.assignments:
            if assignment.subject == subject:
                return (assignment.day, assignment.slot)
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "days": self.config.days,
            "slots_per_day": self.config.slots_per_day,
            "assignments": [
                {
                    "day": a.day + 1,
                    "slot": a.slot + 1,
                    "subject": a.subject
                }
                for a in self.assignments
            ]
        }


@dataclass
class Hall:
    """Represents an examination hall."""
    name: str
    capacity: int
    
    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(f"Hall {self.name} must have positive capacity")


@dataclass
class HallConfig:
    """Configuration for hall allocation."""
    halls: List[Hall]
    per_subject_limit: int = 30
    
    def __post_init__(self):
        if not self.halls:
            raise ValueError("Must have at least one hall")
        if self.per_subject_limit <= 0:
            raise ValueError("Per-subject limit must be positive")
    
    @property
    def total_capacity(self) -> int:
        return sum(h.capacity for h in self.halls)


@dataclass
class HallAssignment:
    """Represents assignment of students to a hall for a specific slot."""
    hall_name: str
    day: int
    slot: int
    allocations: List[Tuple[str, int]]  # (subject, student_count)
    
    def __str__(self) -> str:
        alloc_str = ", ".join(f"{subj}: {count}" for subj, count in self.allocations)
        return f"{self.hall_name} (Day {self.day + 1}, Slot {self.slot + 1}): {alloc_str}"


@dataclass
class HallAllocationResult:
    """Result of hall allocation."""
    assignments: List[HallAssignment]
    timetable: TimetableResult
    hall_config: HallConfig
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "timetable": self.timetable.to_dict(),
            "hall_allocations": [
                {
                    "hall": a.hall_name,
                    "day": a.day + 1,
                    "slot": a.slot + 1,
                    "allocations": [
                        {"subject": subj, "students": count}
                        for subj, count in a.allocations
                    ]
                }
                for a in self.assignments
            ]
        }
