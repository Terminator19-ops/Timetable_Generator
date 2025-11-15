"""
Pydantic schemas for API request/response validation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class StudentGroupSchema(BaseModel):
    """Schema for student group."""
    name: str = Field(min_length=1, description="Group name")
    subjects: List[str] = Field(min_length=1, description="List of subjects")
    size: int = Field(gt=0, description="Number of students")
    
    @field_validator('subjects')
    @classmethod
    def subjects_not_empty(cls, v):
        if not v:
            raise ValueError("Subjects list cannot be empty")
        return v


class HallSchema(BaseModel):
    """Schema for examination hall."""
    name: str = Field(min_length=1, description="Hall name")
    capacity: int = Field(gt=0, description="Hall capacity")


class TimetableConfigSchema(BaseModel):
    """Schema for timetable configuration."""
    days: int = Field(gt=0, description="Number of days")
    slots_per_day: int = Field(gt=0, description="Slots per day")
    subjects: List[str] = Field(min_length=1, description="List of subjects")
    groups: List[StudentGroupSchema] = Field(min_length=1, description="Student groups")
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    
    @field_validator('subjects')
    @classmethod
    def subjects_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Subjects must be unique")
        return v


class HallConfigSchema(BaseModel):
    """Schema for hall configuration."""
    halls: List[HallSchema] = Field(min_length=1, description="List of halls")
    per_subject_limit: int = Field(default=30, gt=0, description="Maximum students per subject in a hall")


class GenerateRequestSchema(BaseModel):
    """Schema for generate timetable request."""
    timetable_config: TimetableConfigSchema
    hall_config: HallConfigSchema


class ConfigRequestSchema(BaseModel):
    """Schema for configuration request."""
    subjects: List[str] = Field(min_length=1)
    groups: List[StudentGroupSchema] = Field(default_factory=list, description="Student groups (can be empty initially)")
    days: int = Field(gt=0)
    slots_per_day: int = Field(gt=0)
    halls: List[HallSchema] = Field(min_length=1)
    per_subject_limit: int = Field(default=30, gt=0)
    random_seed: Optional[int] = None


class ExamSlotSchema(BaseModel):
    """Schema for exam slot."""
    day: int
    slot: int
    subject: str


class TimetableResponseSchema(BaseModel):
    """Schema for timetable response."""
    days: int
    slots_per_day: int
    assignments: List[ExamSlotSchema]


class AllocationSchema(BaseModel):
    """Schema for subject allocation in a hall."""
    subject: str
    students: int


class HallAssignmentSchema(BaseModel):
    """Schema for hall assignment."""
    hall: str
    day: int
    slot: int
    allocations: List[AllocationSchema]


class HallAllocationResponseSchema(BaseModel):
    """Schema for hall allocation response."""
    timetable: TimetableResponseSchema
    hall_allocations: List[HallAssignmentSchema]


class ErrorResponseSchema(BaseModel):
    """Schema for error response."""
    error: str
    detail: Optional[str] = None
    diagnostics: Optional[dict] = None


class AddGroupRequestSchema(BaseModel):
    """Schema for adding a group."""
    name: str = Field(min_length=1)
    subjects: List[str] = Field(min_length=1)
    size: int = Field(gt=0)
