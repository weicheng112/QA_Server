#!/usr/bin/env python3
"""
Test file for testing the ingest.py script functions.
Focuses on testing extract_metadata and ingest_docs functions.
"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
import pytest

# Import functions from ingest.py
from scripts.ingest import extract_metadata, ingest_docs, preprocess_markdown, chunk_markdown_with_headers
from langchain_text_splitters import MarkdownHeaderTextSplitter

class TestExtractMetadata(unittest.TestCase):
    """Test the extract_metadata function"""
    
    def setUp(self):
        """Set up temporary directory and files for testing"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test markdown files
        self.test_files = {
            'simple.md': "# Simple Document\n\n## First Section\n\nThis is a simple test document.",
            'no_headings.md': "This document has no headings at all.",
            'complex.md': "# Complex Document\n\n## Section 1\n\nContent 1\n\n### Subsection 1.1\n\nMore content\n\n## Section 2\n\nContent 2"
        }
        
        # Write test files
        self.file_paths = {}
        for filename, content in self.test_files.items():
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.file_paths[filename] = file_path
    
    def tearDown(self):
        """Clean up temporary directory and files"""
        shutil.rmtree(self.test_dir)
    
    def test_extract_metadata_with_headings(self):
        """Test extract_metadata with a document that has headings"""
        file_path = self.file_paths['simple.md']
        
        # Create metadata similar to what LangChain would produce
        chunk_metadata = {
            "title": "Simple Document",
            "section": "First Section"
        }
        
        metadata = extract_metadata(file_path, chunk_metadata)
        
        self.assertEqual(metadata['source'], 'simple.md')
        self.assertEqual(metadata['title'], 'Simple Document')
        self.assertEqual(metadata['section'], 'First Section')
        self.assertEqual(metadata['path'], file_path)
    
    def test_extract_metadata_without_headings(self):
        """Test extract_metadata with a document that has no headings"""
        file_path = self.file_paths['no_headings.md']
        
        # Create empty metadata
        chunk_metadata = {}
        
        metadata = extract_metadata(file_path, chunk_metadata)
        
        self.assertEqual(metadata['source'], 'no_headings.md')
        self.assertEqual(metadata['title'], 'no_headings.md')
        self.assertEqual(metadata['section'], "")
        self.assertEqual(metadata['path'], file_path)
    
    def test_extract_metadata_complex_document(self):
        """Test extract_metadata with a complex document structure"""
        file_path = self.file_paths['complex.md']
        
        # Create metadata similar to what LangChain would produce
        chunk_metadata = {
            "title": "Complex Document",
            "section": "Section 1",
            "subsection": "Subsection 1.1"
        }
        
        metadata = extract_metadata(file_path, chunk_metadata)
        
        self.assertEqual(metadata['source'], 'complex.md')
        self.assertEqual(metadata['title'], 'Complex Document')
        self.assertEqual(metadata['section'], 'Section 1')
        self.assertEqual(metadata['subsection'], 'Subsection 1.1')
        self.assertEqual(metadata['path'], file_path)


class TestIngestDocs(unittest.TestCase):
    """Test the ingest_docs function"""
    
    def setUp(self):
        """Set up temporary directory and files for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.db_dir = tempfile.mkdtemp()
        
        # Create test markdown files
        test_content = "# Test Document\n\n## Section 1\n\nThis is test content.\n\n## Section 2\n\nMore test content."
        self.test_file = os.path.join(self.test_dir, "test_doc.md")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
    
    def tearDown(self):
        """Clean up temporary directories and files"""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.db_dir)
    
    @patch('scripts.ingest.chromadb.PersistentClient')
    def test_ingest_docs(self, mock_client):
        """Test ingest_docs function with mocked ChromaDB client"""
        # Set up mock collection
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        
        # Call the function
        ingest_docs(self.test_dir, self.db_dir)
        
        # Verify ChromaDB client was initialized correctly
        mock_client.assert_called_once_with(path=self.db_dir)
        
        # Verify collection was created
        mock_client.return_value.get_or_create_collection.assert_called_once()
        
        # Verify documents were added to the collection
        mock_collection.add.assert_called_once()
        
        # Get the arguments passed to add()
        args, kwargs = mock_collection.add.call_args
        
        # Verify documents were passed
        self.assertIn('documents', kwargs)
        self.assertTrue(len(kwargs['documents']) > 0)
        
        # Verify metadatas were passed
        self.assertIn('metadatas', kwargs)
        self.assertTrue(len(kwargs['metadatas']) > 0)
        
        # Verify ids were passed
        self.assertIn('ids', kwargs)
        self.assertTrue(len(kwargs['ids']) > 0)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions in ingest.py"""
    
    def test_preprocess_markdown(self):
        """Test preprocess_markdown function"""
        # Test removing image links
        md_with_images = "# Document\n\nHere's an image: ![Alt text](image.jpg)\n\nMore text."
        processed = preprocess_markdown(md_with_images)
        self.assertNotIn("![Alt text](image.jpg)", processed)
        
        # Test removing HTML tags
        md_with_html = "# Document\n\n<div>HTML content</div>\n\nMore text."
        processed = preprocess_markdown(md_with_html)
        self.assertNotIn("<div>", processed)
        self.assertIn("HTML content", processed)
        
        # Note: The updated preprocess_markdown function no longer normalizes whitespace
        # as this is handled by LangChain's text splitter
    
    def test_chunk_markdown_with_headers(self):
        """Test chunk_markdown_with_headers function"""
        # Test with a simple document
        simple_text = "# Document Title\n\n## Section 1\n\nThis is content for section 1.\n\n## Section 2\n\nThis is content for section 2."
        chunks = chunk_markdown_with_headers(simple_text)
        
        # Verify we get chunks
        self.assertTrue(len(chunks) > 0)
        
        # Verify each chunk has metadata
        for chunk in chunks:
            self.assertTrue(hasattr(chunk, 'page_content'))
            self.assertTrue(hasattr(chunk, 'metadata'))
            
            # Check that metadata contains expected keys
            if 'title' in chunk.metadata:
                self.assertEqual(chunk.metadata['title'], 'Document Title')
            
            # Verify section metadata is captured
            if 'section' in chunk.metadata:
                self.assertTrue(chunk.metadata['section'] in ['Section 1', 'Section 2'])
        
        # Test with a document that has subsections
        complex_text = """# Complex Document
        
## Section 1

Content for section 1.

### Subsection 1.1

Content for subsection 1.1.

## Section 2

Content for section 2.
"""
        chunks = chunk_markdown_with_headers(complex_text)
        
        # Verify we get chunks
        self.assertTrue(len(chunks) > 0)
        
        # Find a chunk with subsection
        subsection_chunk = None
        for chunk in chunks:
            if 'subsection' in chunk.metadata:
                subsection_chunk = chunk
                break
                
        # Verify subsection metadata is captured
        if subsection_chunk:
            self.assertEqual(subsection_chunk.metadata['title'], 'Complex Document')
            self.assertEqual(subsection_chunk.metadata['section'], 'Section 1')
            self.assertEqual(subsection_chunk.metadata['subsection'], 'Subsection 1.1')


if __name__ == "__main__":
    unittest.main()