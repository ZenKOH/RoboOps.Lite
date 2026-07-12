from typing import Optional

from pydantic import BaseModel, Field


class RobotCreate(BaseModel):
    name: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    hardware_version: str = ""
    firmware_version: str = ""
    notes: str = ""


class SkillCreate(BaseModel):
    name: str = Field(min_length=1)
    category: str = "general"
    description: str = ""
    compatible_platforms: str = ""
    status: str = "lab"
    safety_boundary: str = ""


class TrialCreate(BaseModel):
    title: str = Field(min_length=1)
    robot_id: Optional[int] = None
    skill_id: Optional[int] = None
    environment: str = ""
    model_version: str = ""
    protocol: str = ""
    status: str = "unknown"
    notes: str = ""


class TrialAnnotation(BaseModel):
    timestamp: Optional[float] = None
    event_type: str = Field(min_length=1)
    label: str = ""
    confidence: Optional[float] = None
    value: Optional[float] = None
    metadata: str = ""
