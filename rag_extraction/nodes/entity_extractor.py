"""
Entity extractor node for LangGraph Cloud
"""
import asyncio
import time
from typing import List, Dict
from langsmith import traceable
from openai import AsyncOpenAI

from ..schemas.state import ExtractionState
from ..schemas.entities import ExtractedEntity, EntityType
from ..utils.validators import validate_entity_name, validate_entity_definition


@traceable(
    name="extract_entities_node", 
    metadata={"component": "entity-extraction"}
)
async def extract_entities(state: ExtractionState) -> ExtractionState:
    """
    Extract entities from chunk text using specialized extractors.
    """
    
    start_time = time.time()
    
    # Skip if chunk shouldn't be processed
    if not state.should_process:
        state.processing_time = time.time() - start_time
        return state
    
    try:
        # Initialize OpenAI client
        client = AsyncOpenAI()
        
        # Run specialized extractors
        extractors = {
            'concept': extract_concepts,
            'method': extract_methods,
            'formula': extract_formulas,
            'example': extract_examples,
            'legal_principle': extract_legal_principles
        }
        
        # Run extractors concurrently
        tasks = []
        for extractor_type, extractor_func in extractors.items():
            task = extractor_func(client, state.chunk_text, state.chunk_type)
            tasks.append((extractor_type, task))
        
        # Collect results
        for extractor_type, task in tasks:
            try:
                entities = await task
                validated_entities = []
                
                for entity in entities:
                    # Validate entity name
                    is_valid_name, name_reason = validate_entity_name(entity['name'])
                    if not is_valid_name:
                        state.warnings.append(f"Invalid entity name '{entity['name']}': {name_reason}")
                        continue
                    
                    # Validate definition if present
                    if entity.get('definition'):
                        is_valid_def, def_reason = validate_entity_definition(
                            entity['definition'], entity['name']
                        )
                        if not is_valid_def:
                            state.warnings.append(f"Invalid definition for '{entity['name']}': {def_reason}")
                            entity['definition'] = None
                    
                    validated_entities.append(entity)
                
                if validated_entities:
                    state.extracted_entities[extractor_type] = validated_entities
                    
            except Exception as e:
                state.errors.append(f"Error in {extractor_type} extractor: {str(e)}")
        
        # Update metrics
        state.entity_count = sum(len(entities) for entities in state.extracted_entities.values())
        state.processing_time = time.time() - start_time
        
        return state
        
    except Exception as e:
        state.errors.append(f"Error in entity extraction: {str(e)}")
        state.processing_time = time.time() - start_time
        return state


@traceable(name="concept_extractor")
async def extract_concepts(client: AsyncOpenAI, chunk_text: str, chunk_type: str) -> List[Dict]:
    """Extract concepts with improved prompting and validation."""
    
    prompt = f"""
    Extract key concepts from this {chunk_type} text. Focus on:
    - Theories, principles, and methodologies
    - Technical terms and domain-specific concepts
    - Important ideas or frameworks
    
    Rules:
    - Entity names must be complete phrases (minimum 3 characters)
    - No fragments starting with "ly", "ing", "ed", "er"
    - No single digits or mathematical symbols alone
    - Provide clear, relevant definitions
    - If unsure about a concept, don't extract it
    
    Text: {chunk_text}
    
    Return JSON array of objects with 'name', 'definition', 'confidence' (0-1), 'domain'.
    Maximum 10 concepts.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000
    )
    
    try:
        import json
        entities = json.loads(response.choices[0].message.content)
        return entities if isinstance(entities, list) else []
    except:
        return []


@traceable(name="method_extractor") 
async def extract_methods(client: AsyncOpenAI, chunk_text: str, chunk_type: str) -> List[Dict]:
    """Extract methods and procedures."""
    
    prompt = f"""
    Extract methods, procedures, and step-by-step processes from this text.
    Look for:
    - Analytical methods
    - Procedures and workflows
    - Systematic approaches
    - Techniques and strategies
    
    Rules: Complete names only, relevant definitions, confidence 0-1.
    
    Text: {chunk_text}
    
    JSON array format: [{{"name": "...", "definition": "...", "confidence": 0.8, "domain": "..."}}]
    Maximum 5 methods.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1500
    )
    
    try:
        import json
        entities = json.loads(response.choices[0].message.content)
        return entities if isinstance(entities, list) else []
    except:
        return []


@traceable(name="formula_extractor")
async def extract_formulas(client: AsyncOpenAI, chunk_text: str, chunk_type: str) -> List[Dict]:
    """Extract mathematical formulas and equations."""
    
    # Skip if no mathematical content
    if not any(indicator in chunk_text for indicator in ['$', '=', '+', '-', '*', '/', '^', '²', '³']):
        return []
    
    prompt = f"""
    Extract mathematical formulas and equations from this text.
    Look for:
    - Mathematical equations
    - Statistical formulas
    - Algorithmic expressions
    
    Rules:
    - NO single digits (1, 2, 3, etc.)
    - Must contain mathematical operators or variables
    - Include LaTeX notation if present
    - Provide mathematical context in definition
    
    Text: {chunk_text}
    
    JSON array format with mathematical formulas only.
    Maximum 3 formulas.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    
    try:
        import json
        entities = json.loads(response.choices[0].message.content)
        # Additional filter for single digits
        filtered_entities = []
        for entity in entities:
            if not (entity['name'].isdigit() and len(entity['name']) <= 2):
                filtered_entities.append(entity)
        return filtered_entities
    except:
        return []


@traceable(name="example_extractor")
async def extract_examples(client: AsyncOpenAI, chunk_text: str, chunk_type: str) -> List[Dict]:
    """Extract examples and case studies."""
    
    prompt = f"""
    Extract examples, case studies, and illustrative scenarios from this text.
    Look for:
    - Practical examples
    - Case studies
    - Scenarios and situations
    - Illustrative instances
    
    Rules: Complete example descriptions, no fragments.
    
    Text: {chunk_text}
    
    JSON array format. Maximum 5 examples.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1500
    )
    
    try:
        import json
        entities = json.loads(response.choices[0].message.content)
        return entities if isinstance(entities, list) else []
    except:
        return []


@traceable(name="legal_principle_extractor")
async def extract_legal_principles(client: AsyncOpenAI, chunk_text: str, chunk_type: str) -> List[Dict]:
    """Extract legal principles and rules."""
    
    # Skip if no legal content indicators
    legal_indicators = ['court', 'law', 'rule', 'statute', 'precedent', 'jurisdiction', 'legal', 'judge']
    if not any(indicator in chunk_text.lower() for indicator in legal_indicators):
        return []
    
    prompt = f"""
    Extract legal principles, rules, and doctrines from this text.
    Look for:
    - Legal rules and principles
    - Court doctrines
    - Statutory provisions
    - Legal standards
    
    Rules: Focus on established legal principles.
    
    Text: {chunk_text}
    
    JSON array format. Maximum 3 legal principles.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000
    )
    
    try:
        import json
        entities = json.loads(response.choices[0].message.content)
        return entities if isinstance(entities, list) else []
    except:
        return []