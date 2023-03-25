"""Schema for API payloads and inputs"""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ExposeRequest(BaseModel):
    """Schema for expose request"""
    type: str = Field(..., description="The type of data to expose: latest | 24h_devt "
                                       "| 24_average | 7d_devt | 7d_average")


class FraudItem(BaseModel):
    """Schema for a weather item"""
    name: str
    timestamp: str
    fraud_data: Dict


class ExposeResponse(BaseModel):
    """Schema for expose response"""
    status: str
    description: str
    data: Dict[str, FraudItem]


class WriteRequest(BaseModel):
    """Schema for expose request"""
    data: Dict


class WriteResponse(BaseModel):
    """Schema for Write response item"""
    status: str
    description: str
    data: Dict


class ApiRecord(BaseModel):
    """Schema for table record"""
    id: str
    sk: str
    event_time: str
    name: str
    user_id: Optional[str]
    data: Optional[Dict]

