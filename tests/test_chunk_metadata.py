#!/usr/bin/env python3
"""
Simple demonstration of chunking and metadata extraction for labor_rules.md.
This script shows how the document is split into chunks and what metadata is extracted.
"""

import os
import sys
import re
from typing import List, Dict, Any

# Add the parent directory to sys.path to import from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions from the ingest script
from scripts.ingest import preprocess_markdown, chunk_text, extract_metadata

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
    if metadata['section']:
        print(f"  Section: {metadata['section']}")
    else:
        # Try to extract section from the chunk content
        section_match = re.search(r'##\s+([^\n]+)', chunk)
        if section_match:
            print(f"  Section: {section_match.group(1)}")
        else:
            print(f"  Section: [No section found]")
        
        # Try to extract subsections for additional context
        subsections = re.findall(r'###\s+([^\n]+)', chunk)
        if subsections:
            print(f"  Subsections: {', '.join(subsections[:3])}" +
                  (f" (and {len(subsections)-3} more)" if len(subsections) > 3 else ""))
    
    print(f"  Path: {metadata['path']}")
    print(f"  Chunk ID: {metadata['chunk_id']}")
    print(f"  Chunk Total: {metadata['chunk_total']}")
    
    # Display chunk content (truncated if very long)
    print(f"\nCONTENT:")
    if len(chunk) > 500:
        print(f"{chunk[:500]}...\n[Content truncated, total length: {len(chunk)} characters]")
    else:
        print(chunk)

def main():
    """
    Main function to demonstrate chunking and metadata extraction.
    """
    # Path to the labor_rules.md file
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            "docs", "labor_rules.md")
    
    print(f"Processing file: {file_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Preprocess the content
    processed_content = preprocess_markdown(content)
    
    # Extract base metadata with a custom approach for this demo
    base_metadata = extract_metadata(file_path, processed_content)
    
    # Fix the title if it's too long (likely grabbed the whole document)
    if len(base_metadata['title']) > 100:
        # Try to extract just the main title
        title_match = re.search(r'^#\s+([^\n]+)', content)
        if title_match:
            base_metadata['title'] = title_match.group(1)
        else:
            base_metadata['title'] = os.path.basename(file_path).replace('.md', '')
    
    # Chunk the document (using a smaller chunk size for demonstration)
    chunks = chunk_text(processed_content, chunk_size=300, chunk_overlap=50)
    
    # Analyze chunks to identify main sections and their distribution
    print("\nSECTION DISTRIBUTION ACROSS CHUNKS:")
    for i, chunk in enumerate(chunks):
        section_matches = re.findall(r'##\s+([^\n]+)', chunk)
        if section_matches:
            # Clean up the section names to just show the heading text
            clean_sections = []
            for section in section_matches:
                # Extract just the section name without any following content
                clean_section = section.split(' ###')[0].strip()
                clean_sections.append(clean_section)
            
            sections_str = ", ".join(clean_sections)
            print(f"  Chunk {i+1}: {sections_str}")
    
    # Print document split message
    print(f"\nDocument split into {len(chunks)} chunks")
    
    # Display information for each chunk
    for i, chunk in enumerate(chunks):
        # Add chunk-specific metadata
        chunk_metadata = base_metadata.copy()
        chunk_metadata["chunk_id"] = i
        chunk_metadata["chunk_total"] = len(chunks)
        
        # Extract section for this specific chunk - clean up the section name
        section_match = re.search(r'##\s+([^\n]+)', chunk)
        if section_match:
            # Extract just the section name without any following content
            section_text = section_match.group(1)
            clean_section = section_text.split(' ###')[0].strip()
            chunk_metadata["section"] = clean_section
        
        # Display chunk info
        display_chunk_info(chunk, chunk_metadata, i, len(chunks))

if __name__ == "__main__":
    main()