#!/usr/bin/env python3
"""
Enhanced demonstration of chunking and metadata extraction for labor_rules.md.
This script shows how the document is split into chunks with per-chunk section extraction.
"""

import os
import sys
import re
from typing import List, Dict, Any

# Add the parent directory to sys.path to import from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions from the ingest script
from scripts.ingest import preprocess_markdown, chunk_markdown_with_headers, extract_metadata

def display_chunk_info(chunk: str, metadata: Dict[str, Any], index: int, total: int) -> None:
    """
    Display information about a chunk in a readable format.
    """
    print(f"\n{'='*80}")
    print(f"CHUNK {index+1} OF {total}")
    print(f"{'='*80}")
    
    # Display metadata
    print(f"METADATA:")
    print(f"  Source: {metadata['source']}")
    print(f"  Title: {metadata['title']}")
    
    # Display section information
    if 'section' in metadata and metadata['section']:
        print(f"  Section: {metadata['section']}")
    else:
        print(f"  Section: [No section found]")
    
    # Display subsection information if available
    if 'subsection' in metadata and metadata['subsection']:
        print(f"  Subsection: {metadata['subsection']}")
    
    print(f"  Path: {metadata['path']}")
    print(f"  Chunk ID: {metadata['chunk_id']}")
    print(f"  Chunk Total: {metadata['chunk_total']}")
    
    # Display chunk content (truncated if very long)
    print(f"\nCONTENT:")
    if len(chunk) > 500:
        print(f"{chunk[:500]}...\n[Content truncated, total length: {len(chunk)} characters]")
    else:
        print(chunk)

def create_test_document_with_multiple_sections():
    """
    Create a test document with multiple sections in close proximity to demonstrate
    the per-chunk section extraction.
    """
    return """# Test Document with Multiple Sections

## Section 1
This is content for section 1.

## Section 2
This is content for section 2.

## Section 3
This is content for section 3.

## Section 4
This is content for section 4.
"""

def main():
    """
    Main function to demonstrate chunking and metadata extraction.
    """
    # First process the labor_rules.md file
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "docs", "labor_rules.md")
    
    print(f"\n{'='*80}")
    print(f"PROCESSING REAL DOCUMENT: {file_path}")
    print(f"{'='*80}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Preprocess the content
    processed_content = preprocess_markdown(content)
    
    # Print the first 100 characters of the processed content to debug
    print(f"\nProcessed content starts with: '{processed_content[:100]}...'")
    
    # Chunk the document using LangChain's MarkdownHeaderTextSplitter
    chunks_with_metadata = chunk_markdown_with_headers(processed_content)
    
    # Print document split message
    print(f"\nDocument split into {len(chunks_with_metadata)} chunks")
    
    # Display information for each chunk
    for i, chunk_with_metadata in enumerate(chunks_with_metadata):
        # Extract text and metadata
        chunk_text = chunk_with_metadata.page_content
        chunk_header_metadata = chunk_with_metadata.metadata
        
        # Create full metadata
        chunk_metadata = extract_metadata(file_path, chunk_header_metadata)
        chunk_metadata["chunk_id"] = i
        chunk_metadata["chunk_total"] = len(chunks_with_metadata)
        
        # Display chunk info
        display_chunk_info(chunk_text, chunk_metadata, i, len(chunks_with_metadata))
    
    # Now process a test document specifically designed to show multiple sections in one chunk
    print(f"\n{'='*80}")
    print(f"PROCESSING TEST DOCUMENT WITH MULTIPLE SECTIONS PER CHUNK")
    print(f"{'='*80}")
    
    test_content = create_test_document_with_multiple_sections()
    processed_test_content = preprocess_markdown(test_content)
    
    # Print the first 100 characters of the processed test content to debug
    print(f"\nProcessed test content starts with: '{processed_test_content[:100]}...'")
    
    # Chunk the test document using LangChain's MarkdownHeaderTextSplitter
    test_chunks_with_metadata = chunk_markdown_with_headers(processed_test_content)
    
    # Print document split message
    print(f"\nTest document split into {len(test_chunks_with_metadata)} chunks")
    
    # Display information for each chunk
    for i, chunk_with_metadata in enumerate(test_chunks_with_metadata):
        # Extract text and metadata
        chunk_text = chunk_with_metadata.page_content
        chunk_header_metadata = chunk_with_metadata.metadata
        
        # Create full metadata
        chunk_metadata = extract_metadata("test_multiple_sections.md", chunk_header_metadata)
        chunk_metadata["chunk_id"] = i
        chunk_metadata["chunk_total"] = len(test_chunks_with_metadata)
        
        # Display chunk info
        display_chunk_info(chunk_text, chunk_metadata, i, len(test_chunks_with_metadata))

if __name__ == "__main__":
    main()