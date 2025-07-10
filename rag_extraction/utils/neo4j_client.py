"""
Neo4j client for LangGraph Cloud deployment
"""
import os
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase


class Neo4jClient:
    """Neo4j client for cloud deployment"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
    
    def get_chunk_data(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk data from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (c:SemanticChunk {id: $chunk_id})
            RETURN c.text as text,
                   c.semantic_type as chunk_type,
                   c.token_count as token_count,
                   c.book_id as book_id,
                   c.position as position
            """
            result = session.run(query, chunk_id=chunk_id)
            record = result.single()
            return dict(record) if record else None
    
    def store_entities(self, chunk_id: str, entities: List[Dict], relationships: List[Dict]) -> None:
        """Store extracted entities and relationships"""
        with self.driver.session() as session:
            # Store entities
            for entity in entities:
                entity_query = """
                MATCH (c:SemanticChunk {id: $chunk_id})
                MERGE (e:{entity_type} {name: $name})
                SET e.definition = $definition,
                    e.confidence = $confidence,
                    e.domain = $domain,
                    e.created_at = datetime()
                MERGE (c)<-[r:{relationship}]-(e)
                SET r.created_at = datetime()
                """.format(
                    entity_type=entity['entity_type'].title(),
                    relationship=self._get_relationship_type(entity['entity_type'])
                )
                
                session.run(entity_query, 
                           chunk_id=chunk_id,
                           name=entity['name'],
                           definition=entity.get('definition'),
                           confidence=entity.get('confidence', 0.8),
                           domain=entity.get('domain', 'general'))
            
            # Store relationships
            for rel in relationships:
                rel_query = """
                MATCH (source {name: $source_name})
                MATCH (target {name: $target_name})
                MERGE (source)-[r:{rel_type}]->(target)
                SET r.confidence = $confidence,
                    r.description = $description,
                    r.created_at = datetime()
                """.format(rel_type=rel['relationship_type'])
                
                session.run(rel_query,
                           source_name=rel['source_entity'],
                           target_name=rel['target_entity'],
                           confidence=rel.get('confidence', 0.8),
                           description=rel.get('description'))
    
    def _get_relationship_type(self, entity_type: str) -> str:
        """Get appropriate relationship type for entity"""
        mapping = {
            'concept': 'DEFINED_IN',
            'method': 'EXPLAINED_IN',
            'formula': 'APPEARS_IN',
            'question': 'ASKED_IN',
            'example': 'DESCRIBED_IN',
            'legal_principle': 'STATED_IN',
            'case_citation': 'CITED_IN'
        }
        return mapping.get(entity_type.lower(), 'APPEARS_IN')
    
    def close(self):
        """Close the Neo4j connection"""
        self.driver.close()