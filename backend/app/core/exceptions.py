"""
Custom exceptions for the exam scheduling system.
"""
from typing import List, Dict, Any, Optional


class SchedulerError(Exception):
    """Base exception for all scheduler errors."""
    pass


class NoSolutionError(SchedulerError):
    """Raised when no valid timetable can be generated."""
    
    def __init__(
        self,
        message: str,
        diagnostics: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.diagnostics = diagnostics or {}
    
    def __str__(self) -> str:
        base = super().__str__()
        if self.diagnostics:
            diag_str = "\nDiagnostics:\n"
            for key, value in self.diagnostics.items():
                diag_str += f"  {key}: {value}\n"
            return base + diag_str
        return base


class InsufficientSlotsError(NoSolutionError):
    """Raised when there are not enough slots for all subjects."""
    pass


class ConflictError(NoSolutionError):
    """Raised when subject conflicts cannot be resolved."""
    pass


class HallAllocationError(SchedulerError):
    """Raised when hall allocation fails."""
    pass


class InsufficientHallCapacityError(HallAllocationError):
    """Raised when total hall capacity is insufficient."""
    pass


class ValidationError(SchedulerError):
    """Raised when input validation fails."""
    pass
