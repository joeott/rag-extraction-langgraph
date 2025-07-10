"""
Chunk retriever node for LangGraph Cloud
"""
from langsmith import traceable
from ..schemas.state import ExtractionState
from ..utils.neo4j_client import Neo4jClient
from ..utils.validators import should_process_chunk


@traceable(
    name="retrieve_chunk_node",
    metadata={"component": "chunk-retrieval"}
)
def retrieve_chunk(state: ExtractionState) -> ExtractionState:
    """
    Retrieve chunk data from Neo4j and validate if it should be processed.
    """
    
    # Get Neo4j client
    client = Neo4jClient()
    
    try:
        # Fetch chunk data
        chunk_data = client.get_chunk_data(state.chunk_id)
        
        if not chunk_data:
            state.errors.append(f"Chunk {state.chunk_id} not found in database")
            state.should_process = False
            state.skip_reason = "chunk_not_found"
            return state
        
        # Update state with chunk data
        state.chunk_text = chunk_data.get('text', '')
        state.chunk_type = chunk_data.get('chunk_type', 'unknown')
        state.chunk_metadata = {
            'token_count': chunk_data.get('token_count'),
            'book_id': chunk_data.get('book_id'),
            'position': chunk_data.get('position')
        }
        
        # Validate if chunk should be processed
        should_process, reason = should_process_chunk(state.chunk_text, state.chunk_type)
        state.should_process = should_process
        
        if not should_process:
            state.skip_reason = reason
            state.warnings.append(f"Skipping chunk: {reason}")
        
        return state
        
    except Exception as e:
        state.errors.append(f"Error retrieving chunk: {str(e)}")
        state.should_process = False
        state.skip_reason = "retrieval_error"
        return state
        
    finally:
        client.close()