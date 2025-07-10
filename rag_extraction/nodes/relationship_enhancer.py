"""
Relationship enhancer node for LangGraph Cloud
"""
from typing import List, Dict
from langsmith import traceable
from openai import AsyncOpenAI

from ..schemas.state import ExtractionState
from ..schemas.entities import RelationshipType


@traceable(
    name="enhance_relationships_node",
    metadata={"component": "relationship-enhancement"}
)
async def enhance_relationships(state: ExtractionState) -> ExtractionState:
    """
    Discover relationships between extracted entities.
    """
    
    # Skip if no entities or chunk wasn't processed
    if not state.should_process or state.entity_count == 0:
        return state
    
    # Get all entity names
    all_entities = []
    for entity_type, entities in state.extracted_entities.items():
        for entity in entities:
            all_entities.append(entity['name'])
    
    # Skip if too few entities for relationships
    if len(all_entities) < 2:
        return state
    
    try:
        # Initialize OpenAI client
        client = AsyncOpenAI()
        
        # Find relationships between entities
        relationships = await find_entity_relationships(
            client, all_entities, state.chunk_text
        )
        
        state.entity_relationships = relationships
        state.relationship_count = len(relationships)
        
        return state
        
    except Exception as e:
        state.errors.append(f"Error in relationship enhancement: {str(e)}")
        return state


@traceable(name="find_entity_relationships")
async def find_entity_relationships(
    client: AsyncOpenAI, 
    entities: List[str], 
    chunk_text: str
) -> List[Dict]:
    """Find relationships between entities in the chunk."""
    
    if len(entities) < 2:
        return []
    
    # Limit to avoid overwhelming the LLM
    if len(entities) > 10:
        entities = entities[:10]
    
    prompt = f"""
    Analyze the relationships between these entities found in the text:
    {', '.join(f'"{entity}"' for entity in entities)}
    
    Text context: {chunk_text[:1500]}...
    
    Find direct relationships where one entity relates to another based on the text.
    
    Relationship types to consider:
    - RELATED_TO: General conceptual relationship
    - PREREQUISITE_OF: One concept is needed to understand another
    - PART_OF: One is a component of another
    - USES: One concept uses or applies another
    - SIMILAR_TO: Concepts are similar or analogous
    - APPLIED_IN: One concept is applied in the context of another
    
    Return JSON array of relationships:
    [{{
        "source_entity": "exact entity name",
        "target_entity": "exact entity name", 
        "relationship_type": "RELATIONSHIP_TYPE",
        "confidence": 0.8,
        "description": "brief explanation of the relationship"
    }}]
    
    Only return relationships that are clearly supported by the text.
    Maximum 5 relationships.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    
    try:
        import json
        relationships = json.loads(response.choices[0].message.content)
        
        # Validate relationships
        valid_relationships = []
        valid_rel_types = [rt.value for rt in RelationshipType]
        
        for rel in relationships:
            if (rel.get('source_entity') in entities and 
                rel.get('target_entity') in entities and
                rel.get('relationship_type') in valid_rel_types and
                rel.get('source_entity') != rel.get('target_entity')):
                valid_relationships.append(rel)
        
        return valid_relationships
        
    except Exception:
        return []