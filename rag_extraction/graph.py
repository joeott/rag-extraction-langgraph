"""
RAG Extraction Graph for LangGraph Cloud
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langsmith import traceable

from .schemas.state import ExtractionState
from .nodes.chunk_retriever import retrieve_chunk
from .nodes.entity_extractor import extract_entities
from .nodes.relationship_enhancer import enhance_relationships  
from .nodes.storage_writer import store_results


@traceable(name="create_extraction_graph")
def create_extraction_graph():
    """Create the semantic extraction workflow for cloud deployment."""
    
    workflow = StateGraph(ExtractionState)
    
    # Add nodes with proper naming for cloud tracing
    workflow.add_node("retrieve_chunk", retrieve_chunk)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("enhance_relationships", enhance_relationships)
    workflow.add_node("store_results", store_results)
    
    # Define linear workflow
    workflow.add_edge("retrieve_chunk", "extract_entities")
    workflow.add_edge("extract_entities", "enhance_relationships")
    workflow.add_edge("enhance_relationships", "store_results")
    workflow.add_edge("store_results", END)
    
    # Set entry point
    workflow.set_entry_point("retrieve_chunk")
    
    # Cloud deployment uses managed checkpointer
    return workflow.compile()


# Export for LangGraph Cloud deployment
extraction_graph = create_extraction_graph()


if __name__ == "__main__":
    # Test graph creation
    graph = create_extraction_graph()
    print("✅ RAG Extraction Graph created successfully for LangGraph Cloud!")
    print("\nWorkflow:")
    print("retrieve_chunk → extract_entities → enhance_relationships → store_results → END")
    print("\nNodes:")
    print("- retrieve_chunk: Fetches chunk data from Neo4j")
    print("- extract_entities: Runs specialized entity extractors with validation")
    print("- enhance_relationships: Discovers relationships between entities")
    print("- store_results: Stores validated entities and relationships in Neo4j")