"""
Utility functions for the exam scheduling system.
"""
from typing import List, Dict, Set, Tuple
from .types import StudentGroup, TimetableConfig
import csv
from io import StringIO


def build_conflict_graph(groups: List[StudentGroup]) -> Dict[str, Set[str]]:
    """
    Build a conflict graph where subjects that share a group conflict.
    
    Args:
        groups: List of student groups
        
    Returns:
        Dictionary mapping each subject to set of conflicting subjects
    """
    conflicts: Dict[str, Set[str]] = {}
    
    for group in groups:
        for subject in group.subjects:
            if subject not in conflicts:
                conflicts[subject] = set()
            # Add all other subjects in the same group as conflicts
            for other_subject in group.subjects:
                if other_subject != subject:
                    conflicts[subject].add(other_subject)
    
    return conflicts


def count_conflicts(subject: str, conflicts: Dict[str, Set[str]]) -> int:
    """Count the number of conflicts for a subject."""
    return len(conflicts.get(subject, set()))


def validate_config(config: TimetableConfig) -> Tuple[bool, List[str]]:
    """
    Validate timetable configuration.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if enough slots
    if len(config.subjects) > config.total_slots:
        errors.append(
            f"Insufficient slots: {len(config.subjects)} subjects need "
            f"{config.total_slots} slots"
        )
    
    # Check for subjects not in any group
    all_group_subjects = set()
    for group in config.groups:
        all_group_subjects.update(group.subjects)
    
    for subject in config.subjects:
        if subject not in all_group_subjects:
            errors.append(f"Subject '{subject}' not assigned to any group")
    
    # Check for subjects in groups but not in subject list
    for subject in all_group_subjects:
        if subject not in config.subjects:
            errors.append(
                f"Subject '{subject}' in groups but not in subject list"
            )
    
    return len(errors) == 0, errors


def generate_csv_export(hall_allocation_result) -> str:
    """
    Generate CSV export of timetable and hall allocations.
    
    Args:
        hall_allocation_result: HallAllocationResult object
        
    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write timetable section
    writer.writerow(["=== TIMETABLE ==="])
    writer.writerow(["Day", "Slot", "Subject"])
    
    for assignment in hall_allocation_result.timetable.assignments:
        writer.writerow([
            f"Day {assignment.day + 1}",
            f"Slot {assignment.slot + 1}",
            assignment.subject
        ])
    
    writer.writerow([])
    
    # Write hall allocation section
    writer.writerow(["=== HALL ALLOCATIONS ==="])
    writer.writerow(["Hall", "Day", "Slot", "Subject", "Students"])
    
    for assignment in hall_allocation_result.assignments:
        for subject, count in assignment.allocations:
            writer.writerow([
                assignment.hall_name,
                f"Day {assignment.day + 1}",
                f"Slot {assignment.slot + 1}",
                subject,
                count
            ])
    
    return output.getvalue()


def get_subjects_in_slot(
    groups: List[StudentGroup],
    subject: str,
    day: int,
    slot: int,
    current_assignment: Dict[str, Tuple[int, int]]
) -> Set[str]:
    """
    Get all subjects that would be in the same slot if 'subject' is assigned there.
    
    Args:
        groups: List of student groups
        subject: Subject to check
        day: Day to check
        slot: Slot to check
        current_assignment: Current subject assignments
        
    Returns:
        Set of subjects that would be in the same slot
    """
    subjects_in_slot = {subject}
    
    for other_subject, (assigned_day, assigned_slot) in current_assignment.items():
        if assigned_day == day and assigned_slot == slot:
            subjects_in_slot.add(other_subject)
    
    return subjects_in_slot


def check_group_conflicts(
    groups: List[StudentGroup],
    subjects_in_slot: Set[str]
) -> bool:
    """
    Check if placing multiple subjects in the same slot violates group constraints.
    
    Args:
        groups: List of student groups
        subjects_in_slot: Set of subjects to check
        
    Returns:
        True if there's a conflict, False otherwise
    """
    for group in groups:
        # Count how many subjects from this group are in the slot
        group_subjects_in_slot = [
            s for s in group.subjects if s in subjects_in_slot
        ]
        if len(group_subjects_in_slot) > 1:
            return True  # Conflict found
    
    return False
