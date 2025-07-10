"""
Input validation for chunk processing and entity quality
"""
import re
from typing import Tuple


def should_process_chunk(chunk_text: str, chunk_type: str) -> Tuple[bool, str]:
    """
    Determine if chunk should be processed for entity extraction.
    
    Returns:
        Tuple of (should_process, reason_if_not)
    """
    
    # Skip very short chunks
    if len(chunk_text.strip()) < 50:
        return False, "chunk_too_short"
        
    # Skip image-only chunks
    if chunk_text.strip().startswith('![') and chunk_text.count('\n') < 2:
        return False, "image_only_chunk"
        
    # Skip table of contents and navigation
    navigation_patterns = [
        '# Table of Contents', '## Page', 'Click here', 'See page',
        'Page ', '...', '##', 'Chapter ', 'Section '
    ]
    
    text_lower = chunk_text.lower()
    if any(pattern.lower() in text_lower for pattern in navigation_patterns):
        # Allow if chunk has substantial content beyond navigation
        content_lines = [line.strip() for line in chunk_text.split('\n') if line.strip()]
        non_nav_lines = [line for line in content_lines 
                        if not any(nav.lower() in line.lower() for nav in navigation_patterns)]
        
        if len(' '.join(non_nav_lines)) < 100:
            return False, "navigation_only"
    
    # Skip very repetitive content
    lines = chunk_text.split('\n')
    if len(lines) > 5:
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(unique_lines) / len(lines) < 0.3:  # Less than 30% unique lines
            return False, "repetitive_content"
    
    # Focus on content-rich chunk types
    content_types = ['paragraph', 'section', 'subsection']
    if chunk_type and chunk_type not in content_types:
        # Allow if chunk has substantial content despite type
        if len(chunk_text.strip()) < 200:
            return False, f"non_content_type_{chunk_type}"
    
    # Skip chunks that are mostly formulas/math without context
    if chunk_text.count('$') > 10 and len(chunk_text.replace('$', '').strip()) < 50:
        return False, "formula_only"
        
    return True, ""


def validate_entity_name(name: str) -> Tuple[bool, str]:
    """
    Validate extracted entity names for quality.
    
    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    
    name = name.strip()
    
    # Reject empty or very short names
    if len(name) < 3:
        return False, "too_short"
        
    # Reject truncated names (common extraction errors)
    truncation_patterns = [
        r'^ly\s+',  # "ly to perceive..."
        r'^ing\s+', # "ing something..."
        r'^ed\s+',  # "ed in the..."
        r'^er\s+',  # "er than..."
        r'^and\s+', # "and the..."
        r'^the\s+', # "the method..." (if very short)
        r'\.\.\.', # Contains ellipsis
    ]
    
    for pattern in truncation_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return False, "truncated_name"
    
    # Reject single digits or very short math expressions as formulas
    if name.isdigit() and len(name) <= 2:
        return False, "single_digit"
    
    # Reject common OCR artifacts
    ocr_artifacts = ['{', '}', '^', '_', '\\', '$$', '`']
    if any(artifact in name for artifact in ocr_artifacts):
        return False, "ocr_artifact"
    
    # Reject if mostly punctuation
    alpha_chars = sum(1 for c in name if c.isalpha())
    if alpha_chars / len(name) < 0.5:
        return False, "mostly_punctuation"
    
    # Reject common meaningless phrases
    meaningless = [
        "click here", "see page", "page ", "chapter ", "section ",
        "figure ", "table ", "appendix ", "index", "bibliography"
    ]
    
    name_lower = name.lower()
    if any(phrase in name_lower for phrase in meaningless):
        return False, "meaningless_phrase"
    
    return True, ""


def validate_entity_definition(definition: str, entity_name: str) -> Tuple[bool, str]:
    """
    Validate that entity definition is relevant and useful.
    
    Returns:
        Tuple of (is_valid, reason_if_invalid)
    """
    
    if not definition or len(definition.strip()) < 10:
        return False, "too_short"
    
    definition = definition.strip()
    
    # Check if definition is just a repetition of the name
    if entity_name.lower() in definition.lower() and len(definition) < len(entity_name) + 20:
        return False, "circular_definition"
    
    # Check for meaningless definitions
    meaningless_defs = [
        "definition not provided",
        "see above",
        "as mentioned",
        "refers to",
        "unknown",
        "n/a"
    ]
    
    def_lower = definition.lower()
    if any(phrase in def_lower for phrase in meaningless_defs):
        return False, "meaningless_definition"
    
    return True, ""