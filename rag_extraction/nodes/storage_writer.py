"""
Storage writer node for LangGraph Cloud
"""
from langsmith import traceable

from ..schemas.state import ExtractionState
from ..utils.neo4j_client import Neo4jClient


@traceable(
    name="store_results_node",
    metadata={"component": "storage"}
)
def store_results(state: ExtractionState) -> ExtractionState:
    """
    Store validated entities and relationships in Neo4j.
    """
    
    # Skip if chunk wasn't processed or no entities
    if not state.should_process or state.entity_count == 0:
        return state
    
    # Get Neo4j client
    client = Neo4jClient()
    
    try:
        # Flatten entities for storage
        all_entities = []
        for entity_type, entities in state.extracted_entities.items():
            for entity in entities:
                entity['entity_type'] = entity_type
                all_entities.append(entity)
        
        # Store in Neo4j
        client.store_entities(
            chunk_id=state.chunk_id,
            entities=all_entities,
            relationships=state.entity_relationships
        )
        
        # Log successful storage
        state.warnings.append(f"Stored {len(all_entities)} entities and {len(state.entity_relationships)} relationships")
        
        return state
        
    except Exception as e:
        state.errors.append(f"Error storing results: {str(e)}")
        return state
        
    finally:
        client.close()