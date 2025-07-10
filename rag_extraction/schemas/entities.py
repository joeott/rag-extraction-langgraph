"""
Entity and relationship schemas
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    """Types of entities that can be extracted"""
    CONCEPT = "concept"
    METHOD = "method"
    FORMULA = "formula"
    QUESTION = "question"
    EXAMPLE = "example"
    LEGAL_PRINCIPLE = "legal_principle"
    CASE_CITATION = "case_citation"


class RelationshipType(str, Enum):
    """Types of relationships between entities"""
    RELATED_TO = "RELATED_TO"
    PREREQUISITE_OF = "PREREQUISITE_OF"
    PART_OF = "PART_OF"
    USES = "USES"
    SIMILAR_TO = "SIMILAR_TO"
    APPLIED_IN = "APPLIED_IN"


class ExtractedEntity(BaseModel):
    """Schema for extracted entities"""
    name: str = Field(description="Name/title of the entity")
    entity_type: EntityType = Field(description="Type of entity")
    definition: Optional[str] = Field(default=None, description="Definition or description")
    confidence: float = Field(default=0.8, description="Confidence score (0-1)")
    domain: str = Field(default="general", description="Domain/subject area")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ExtractedRelationship(BaseModel):
    """Schema for relationships between entities"""
    source_entity: str = Field(description="Name of source entity")
    target_entity: str = Field(description="Name of target entity")
    relationship_type: RelationshipType = Field(description="Type of relationship")
    confidence: float = Field(default=0.8, description="Confidence score (0-1)")
    description: Optional[str] = Field(default=None, description="Description of relationship")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")