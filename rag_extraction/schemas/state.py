"""
Extraction State for LangGraph Cloud Deployment
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ExtractionState(BaseModel):
    """State for semantic extraction workflow."""
    
    # Input
    chunk_id: str = Field(description="Unique identifier for the chunk to process")
    
    # Retrieved data
    chunk_text: Optional[str] = Field(default=None, description="Text content of the chunk")
    chunk_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata about the chunk")
    chunk_type: Optional[str] = Field(default=None, description="Type of chunk (paragraph, section, etc.)")
    
    # Extraction results
    extracted_entities: Dict[str, List[Dict]] = Field(
        default_factory=dict, 
        description="Extracted entities by type"
    )
    entity_relationships: List[Dict] = Field(
        default_factory=list, 
        description="Relationships between entities"
    )
    
    # Processing metadata
    processing_time: float = Field(default=0.0, description="Time taken to process")
    errors: List[str] = Field(default_factory=list, description="Any processing errors")
    warnings: List[str] = Field(default_factory=list, description="Any processing warnings")
    
    # Quality metrics
    entity_count: int = Field(default=0, description="Total number of entities extracted")
    relationship_count: int = Field(default=0, description="Total number of relationships found")
    
    # Processing flags
    should_process: bool = Field(default=True, description="Whether chunk should be processed")
    skip_reason: Optional[str] = Field(default=None, description="Reason for skipping if applicable")
    
    class Config:
        arbitrary_types_allowed = True