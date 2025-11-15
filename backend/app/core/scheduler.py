"""
Core scheduling engine implementing backtracking and hall allocation algorithms.
"""
from typing import List, Dict, Set, Tuple, Optional
import random
from collections import defaultdict

from .types import (
    TimetableConfig, TimetableResult, ExamSlot,
    HallConfig, HallAllocationResult, HallAssignment,
    StudentGroup
)
from .exceptions import (
    NoSolutionError, InsufficientSlotsError, ConflictError,
    InsufficientHallCapacityError
)
from .utils import (
    build_conflict_graph, count_conflicts, validate_config,
    get_subjects_in_slot, check_group_conflicts
)


class TimetableScheduler:
    """
    Implements backtracking algorithm with MRV heuristic and forward checking
    for exam timetable generation.
    """
    
    def __init__(self, config: TimetableConfig):
        self.config = config
        self.conflicts = build_conflict_graph(config.groups)
        self.assignment: Dict[str, Tuple[int, int]] = {}
        self.domains: Dict[str, Set[Tuple[int, int]]] = {}
        self.backtrack_count = 0
        
        if config.random_seed is not None:
            random.seed(config.random_seed)
    
    def generate_timetable(self) -> TimetableResult:
        """
        Generate exam timetable using backtracking with MRV heuristic.
        
        Returns:
            TimetableResult object
            
        Raises:
            NoSolutionError: If no valid timetable can be generated
        """
        # Validate configuration
        is_valid, errors = validate_config(self.config)
        if not is_valid:
            raise NoSolutionError(
                "Invalid configuration",
                {"validation_errors": errors}
            )
        
        # Check basic feasibility
        if len(self.config.subjects) > self.config.total_slots:
            raise InsufficientSlotsError(
                f"Cannot fit {len(self.config.subjects)} subjects into "
                f"{self.config.total_slots} slots",
                {
                    "subjects_count": len(self.config.subjects),
                    "total_slots": self.config.total_slots,
                    "deficit": len(self.config.subjects) - self.config.total_slots
                }
            )
        
        # Initialize domains for all subjects
        all_slots = [
            (day, slot)
            for day in range(self.config.days)
            for slot in range(self.config.slots_per_day)
        ]
        for subject in self.config.subjects:
            self.domains[subject] = set(all_slots)
        
        # Sort subjects by MRV (Most Remaining Values - subjects with most conflicts first)
        subjects = sorted(
            self.config.subjects,
            key=lambda s: count_conflicts(s, self.conflicts),
            reverse=True
        )
        
        # Run backtracking
        if not self._backtrack(subjects, 0):
            raise NoSolutionError(
                "No valid timetable found after exhaustive search",
                {
                    "backtrack_attempts": self.backtrack_count,
                    "subjects": len(self.config.subjects),
                    "conflicts": {
                        s: list(self.conflicts.get(s, set()))
                        for s in self.config.subjects
                    }
                }
            )
        
        # Build result
        assignments = [
            ExamSlot(day=day, slot=slot, subject=subject)
            for subject, (day, slot) in self.assignment.items()
        ]
        
        return TimetableResult(assignments=assignments, config=self.config)
    
    def _backtrack(self, subjects: List[str], index: int) -> bool:
        """
        Recursive backtracking algorithm.
        
        Args:
            subjects: List of subjects to schedule
            index: Current subject index
            
        Returns:
            True if solution found, False otherwise
        """
        self.backtrack_count += 1
        
        # Base case: all subjects assigned
        if index >= len(subjects):
            return True
        
        subject = subjects[index]
        
        # Try each possible slot in the domain
        possible_slots = list(self.domains[subject])
        random.shuffle(possible_slots)  # Randomize to avoid biases
        
        for day, slot in possible_slots:
            if self._is_consistent(subject, day, slot):
                # Make assignment
                self.assignment[subject] = (day, slot)
                
                # Forward checking: update domains
                saved_domains = self._save_domains()
                if self._forward_check(subject, day, slot):
                    # Recursively assign remaining subjects
                    if self._backtrack(subjects, index + 1):
                        return True
                
                # Undo assignment and restore domains
                del self.assignment[subject]
                self._restore_domains(saved_domains)
        
        return False
    
    def _is_consistent(self, subject: str, day: int, slot: int) -> bool:
        """
        Check if assigning subject to (day, slot) is consistent with current assignment.
        
        Args:
            subject: Subject to assign
            day: Day to assign to
            slot: Slot to assign to
            
        Returns:
            True if consistent, False otherwise
        """
        # Check if slot is already occupied
        for assigned_subject, (assigned_day, assigned_slot) in self.assignment.items():
            if assigned_day == day and assigned_slot == slot:
                return False
        
        # Check conflicts with same group
        subjects_in_slot = get_subjects_in_slot(
            self.config.groups, subject, day, slot, self.assignment
        )
        
        return not check_group_conflicts(self.config.groups, subjects_in_slot)
    
    def _forward_check(self, subject: str, day: int, slot: int) -> bool:
        """
        Forward checking: remove inconsistent values from domains.
        
        Args:
            subject: Subject just assigned
            day: Day assigned to
            slot: Slot assigned to
            
        Returns:
            True if all domains are non-empty, False otherwise
        """
        # Remove (day, slot) from all conflicting subjects' domains
        for conflicting_subject in self.conflicts.get(subject, set()):
            if conflicting_subject not in self.assignment:
                if (day, slot) in self.domains[conflicting_subject]:
                    self.domains[conflicting_subject].remove((day, slot))
                
                # If domain becomes empty, this branch won't work
                if not self.domains[conflicting_subject]:
                    return False
        
        return True
    
    def _save_domains(self) -> Dict[str, Set[Tuple[int, int]]]:
        """Save current state of domains."""
        return {
            subject: domain.copy()
            for subject, domain in self.domains.items()
        }
    
    def _restore_domains(self, saved_domains: Dict[str, Set[Tuple[int, int]]]):
        """Restore domains to saved state."""
        self.domains = saved_domains


class HallAllocator:
    """
    Implements greedy hall allocation algorithm with subject mixing.
    """
    
    def __init__(
        self,
        timetable: TimetableResult,
        hall_config: HallConfig
    ):
        self.timetable = timetable
        self.hall_config = hall_config
        self.groups = timetable.config.groups
    
    def allocate_halls(self) -> HallAllocationResult:
        """
        Allocate students to halls using greedy algorithm with mixing priority.
        
        Returns:
            HallAllocationResult object
            
        Raises:
            InsufficientHallCapacityError: If hall capacity is insufficient
        """
        assignments: List[HallAssignment] = []
        
        # Process each slot
        for day in range(self.timetable.config.days):
            for slot in range(self.timetable.config.slots_per_day):
                slot_assignments = self._allocate_slot(day, slot)
                assignments.extend(slot_assignments)
        
        return HallAllocationResult(
            assignments=assignments,
            timetable=self.timetable,
            hall_config=self.hall_config
        )
    
    def _allocate_slot(self, day: int, slot: int) -> List[HallAssignment]:
        """
        Allocate students for a specific slot.
        
        Args:
            day: Day index
            slot: Slot index
            
        Returns:
            List of HallAssignment for this slot
        """
        # Find subjects scheduled in this slot
        subjects_in_slot = []
        for assignment in self.timetable.assignments:
            if assignment.day == day and assignment.slot == slot:
                subjects_in_slot.append(assignment.subject)
        
        if not subjects_in_slot:
            return []
        
        # Calculate student counts for each subject
        subject_students: Dict[str, int] = defaultdict(int)
        for group in self.groups:
            for subject in subjects_in_slot:
                if subject in group.subjects:
                    subject_students[subject] += group.size
        
        # Greedy allocation with mixing
        allocations = self._greedy_allocate(subject_students, day, slot)
        
        return allocations
    
    def _greedy_allocate(
        self,
        subject_students: Dict[str, int],
        day: int,
        slot: int
    ) -> List[HallAssignment]:
        """
        Greedy allocation algorithm with subject mixing.
        
        Args:
            subject_students: Map of subject to student count
            day: Day index
            slot: Slot index
            
        Returns:
            List of HallAssignment
        """
        allocations: List[HallAssignment] = []
        remaining: Dict[str, int] = dict(subject_students)
        
        # Sort halls by capacity (largest first for better mixing)
        sorted_halls = sorted(
            self.hall_config.halls,
            key=lambda h: h.capacity,
            reverse=True
        )
        
        hall_index = 0
        
        while any(count > 0 for count in remaining.values()):
            if hall_index >= len(sorted_halls):
                # Check if we can reuse halls (shouldn't happen in single slot)
                total_remaining = sum(remaining.values())
                total_capacity = self.hall_config.total_capacity
                raise InsufficientHallCapacityError(
                    f"Insufficient hall capacity for slot Day {day + 1}, Slot {slot + 1}",
                    {
                        "remaining_students": total_remaining,
                        "total_capacity": total_capacity,
                        "subjects": dict(remaining)
                    }
                )
            
            hall = sorted_halls[hall_index]
            hall_allocation: List[Tuple[str, int]] = []
            hall_capacity_used = 0
            
            # Try to mix subjects in this hall
            subjects_with_students = [
                (subj, count) for subj, count in remaining.items() if count > 0
            ]
            subjects_with_students.sort(key=lambda x: x[1], reverse=True)
            
            # Strategy: Fill with per_subject_limit chunks
            for subject, count in subjects_with_students:
                if hall_capacity_used >= hall.capacity:
                    break
                
                # Calculate how much we can allocate
                available_in_hall = hall.capacity - hall_capacity_used
                allocate_amount = min(
                    count,
                    self.hall_config.per_subject_limit,
                    available_in_hall
                )
                
                # Special case: if only one subject left and it needs > 30, use full capacity
                if len([s for s, c in remaining.items() if c > 0]) == 1:
                    allocate_amount = min(count, available_in_hall)
                
                if allocate_amount > 0:
                    hall_allocation.append((subject, allocate_amount))
                    remaining[subject] -= allocate_amount
                    hall_capacity_used += allocate_amount
            
            if hall_allocation:
                allocations.append(HallAssignment(
                    hall_name=hall.name,
                    day=day,
                    slot=slot,
                    allocations=hall_allocation
                ))
            
            hall_index += 1
        
        return allocations


def generate_timetable(config: TimetableConfig) -> TimetableResult:
    """
    Main entry point for timetable generation.
    
    Args:
        config: Timetable configuration
        
    Returns:
        TimetableResult object
        
    Raises:
        NoSolutionError: If no valid timetable can be generated
    """
    scheduler = TimetableScheduler(config)
    return scheduler.generate_timetable()


def allocate_halls(
    timetable: TimetableResult,
    hall_config: HallConfig
) -> HallAllocationResult:
    """
    Main entry point for hall allocation.
    
    Args:
        timetable: Generated timetable
        hall_config: Hall configuration
        
    Returns:
        HallAllocationResult object
        
    Raises:
        InsufficientHallCapacityError: If hall capacity is insufficient
    """
    allocator = HallAllocator(timetable, hall_config)
    return allocator.allocate_halls()
