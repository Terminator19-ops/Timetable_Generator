"""
FastAPI routes for the exam scheduling API.
"""
from fastapi import APIRouter, HTTPException, Response
from typing import List, Dict, Any
import logging

from .schemas import (
    GenerateRequestSchema, HallAllocationResponseSchema,
    ConfigRequestSchema, ErrorResponseSchema,
    AddGroupRequestSchema, StudentGroupSchema
)
from ..core.types import (
    TimetableConfig, StudentGroup, Hall, HallConfig
)
from ..core.scheduler import generate_timetable, allocate_halls
from ..core.exceptions import (
    NoSolutionError, InsufficientSlotsError,
    InsufficientHallCapacityError, SchedulerError
)
from ..core.utils import generate_csv_export

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for dynamic configuration
config_store: Dict[str, Any] = {
    "subjects": [],
    "groups": [],
    "days": 5,
    "slots_per_day": 2,
    "halls": [],
    "per_subject_limit": 30,
    "random_seed": None
}


@router.post("/api/config", response_model=dict)
async def configure_system(request: ConfigRequestSchema):
    """
    Configure the scheduling system with subjects, groups, and halls.
    
    Args:
        request: Configuration request
        
    Returns:
        Success message with stored configuration
    """
    try:
        # Store as plain dicts/lists to avoid serialization issues
        config_store["subjects"] = list(request.subjects)
        config_store["groups"] = [
            {"name": g.name, "subjects": list(g.subjects), "size": g.size}
            for g in request.groups
        ]
        config_store["days"] = request.days
        config_store["slots_per_day"] = request.slots_per_day
        config_store["halls"] = [
            {"name": h.name, "capacity": h.capacity}
            for h in request.halls
        ]
        config_store["per_subject_limit"] = request.per_subject_limit
        config_store["random_seed"] = request.random_seed
        
        # Return a clean copy without any objects
        return {
            "message": "Configuration stored successfully",
            "config": {
                "subjects": config_store["subjects"],
                "groups": config_store["groups"],
                "days": config_store["days"],
                "slots_per_day": config_store["slots_per_day"],
                "halls": config_store["halls"],
                "per_subject_limit": config_store["per_subject_limit"],
                "random_seed": config_store["random_seed"]
            }
        }
    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/generate", response_model=HallAllocationResponseSchema)
async def generate_schedule(request: GenerateRequestSchema):
    """
    Generate exam timetable and hall allocations.
    
    Args:
        request: Generation request with timetable and hall config
        
    Returns:
        Complete timetable and hall allocations
        
    Raises:
        HTTPException: On validation or generation errors
    """
    try:
        # Convert schema to domain types
        groups = [
            StudentGroup(
                name=g.name,
                subjects=g.subjects,
                size=g.size
            )
            for g in request.timetable_config.groups
        ]
        
        timetable_config = TimetableConfig(
            days=request.timetable_config.days,
            slots_per_day=request.timetable_config.slots_per_day,
            subjects=request.timetable_config.subjects,
            groups=groups,
            random_seed=request.timetable_config.random_seed
        )
        
        halls = [
            Hall(name=h.name, capacity=h.capacity)
            for h in request.hall_config.halls
        ]
        
        hall_config = HallConfig(
            halls=halls,
            per_subject_limit=request.hall_config.per_subject_limit
        )
        
        # Generate timetable
        logger.info("Generating timetable...")
        timetable = generate_timetable(timetable_config)
        
        # Allocate halls
        logger.info("Allocating halls...")
        hall_allocation = allocate_halls(timetable, hall_config)
        
        # Store for CSV export
        config_store["last_result"] = hall_allocation
        
        return hall_allocation.to_dict()
        
    except InsufficientSlotsError as e:
        logger.error(f"Insufficient slots: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Insufficient slots",
                "message": str(e),
                "diagnostics": e.diagnostics
            }
        )
    except InsufficientHallCapacityError as e:
        logger.error(f"Insufficient hall capacity: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Insufficient hall capacity",
                "message": str(e),
                "diagnostics": getattr(e, 'diagnostics', {})
            }
        )
    except NoSolutionError as e:
        logger.error(f"No solution found: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "No solution found",
                "message": str(e),
                "diagnostics": e.diagnostics
            }
        )
    except SchedulerError as e:
        logger.error(f"Scheduler error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/api/export/csv")
async def export_csv():
    """
    Export last generated timetable and hall allocations as CSV.
    
    Returns:
        CSV file as downloadable attachment
    """
    try:
        if "last_result" not in config_store:
            raise HTTPException(
                status_code=404,
                detail="No timetable generated yet. Please generate a timetable first."
            )
        
        csv_content = generate_csv_export(config_store["last_result"])
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=timetable_export.csv"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/subjects", response_model=List[str])
async def get_subjects():
    """
    Get list of configured subjects.
    
    Returns:
        List of subject names
    """
    return config_store.get("subjects", [])


@router.post("/api/groups", response_model=dict)
async def add_group(request: AddGroupRequestSchema):
    """
    Add a student group dynamically.
    
    Args:
        request: Group to add
        
    Returns:
        Success message with updated groups
    """
    try:
        new_group = {
            "name": request.name,
            "subjects": list(request.subjects),  # Ensure it's a list
            "size": request.size
        }
        
        if "groups" not in config_store:
            config_store["groups"] = []
        
        # Check for duplicate group name
        for group in config_store["groups"]:
            if group["name"] == request.name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Group '{request.name}' already exists"
                )
        
        config_store["groups"].append(new_group)
        
        return {
            "message": f"Group '{request.name}' added successfully",
            "groups": list(config_store["groups"])  # Return clean copy
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add group error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/config", response_model=dict)
async def get_config():
    """
    Get current system configuration.
    
    Returns:
        Current configuration
    """
    # Return clean serializable dict
    return {
        "subjects": config_store.get("subjects", []),
        "groups": config_store.get("groups", []),
        "days": config_store.get("days", 5),
        "slots_per_day": config_store.get("slots_per_day", 2),
        "halls": config_store.get("halls", []),
        "per_subject_limit": config_store.get("per_subject_limit", 30),
        "random_seed": config_store.get("random_seed", None)
    }


@router.delete("/api/groups/{group_name}", response_model=dict)
async def delete_group(group_name: str):
    """
    Delete a student group.
    
    Args:
        group_name: Name of group to delete
        
    Returns:
        Success message
    """
    try:
        if "groups" not in config_store:
            config_store["groups"] = []
        
        initial_count = len(config_store["groups"])
        config_store["groups"] = [
            g for g in config_store["groups"] if g["name"] != group_name
        ]
        
        if len(config_store["groups"]) == initial_count:
            raise HTTPException(
                status_code=404,
                detail=f"Group '{group_name}' not found"
            )
        
        return {
            "message": f"Group '{group_name}' deleted successfully",
            "groups": config_store["groups"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete group error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
