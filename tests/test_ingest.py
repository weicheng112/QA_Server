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
from scripts.ingest import extract_metadata, ingest_docs, preprocess_markdown, chunk_text

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
        content = self.test_files['simple.md']
        
        metadata = extract_metadata(file_path, content)
        
        self.assertEqual(metadata['source'], 'simple.md')
        self.assertEqual(metadata['title'], 'Simple Document')
        self.assertEqual(metadata['section'], 'First Section')
        self.assertEqual(metadata['path'], file_path)
    
    def test_extract_metadata_without_headings(self):
        """Test extract_metadata with a document that has no headings"""
        file_path = self.file_paths['no_headings.md']
        content = self.test_files['no_headings.md']
        
        metadata = extract_metadata(file_path, content)
        
        self.assertEqual(metadata['source'], 'no_headings.md')
        self.assertEqual(metadata['title'], 'no_headings.md')
        self.assertEqual(metadata['section'], "")
        self.assertEqual(metadata['path'], file_path)
    
    def test_extract_metadata_complex_document(self):
        """Test extract_metadata with a complex document structure"""
        file_path = self.file_paths['complex.md']
        content = self.test_files['complex.md']
        
        metadata = extract_metadata(file_path, content)
        
        self.assertEqual(metadata['source'], 'complex.md')
        self.assertEqual(metadata['title'], 'Complex Document')
        self.assertEqual(metadata['section'], 'Section 1')
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
    
    @patch('ingest.chromadb.PersistentClient')
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
        
        # Test normalizing whitespace
        md_with_whitespace = "# Document\n\n\n\nMultiple    spaces   and\nlines."
        processed = preprocess_markdown(md_with_whitespace)
        self.assertNotIn("    ", processed)
        self.assertIn("Multiple spaces and lines", processed)
    
    def test_chunk_text(self):
        """Test chunk_text function"""
        # Test with text shorter than chunk size
        short_text = "This is a short text."
        chunks = chunk_text(short_text, chunk_size=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)
        
        # Test with text longer than chunk size
        # Create a text with multiple paragraphs
        long_text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.\n\nParagraph 4.\n\nParagraph 5."
        # Use a very small chunk size to ensure splitting
        chunks = chunk_text(long_text, chunk_size=5, chunk_overlap=1)
        self.assertTrue(len(chunks) > 1)
        
        # Verify that all content is preserved across chunks
        combined = " ".join(chunks)
        for paragraph in ["Paragraph 1", "Paragraph 2", "Paragraph 3", "Paragraph 4", "Paragraph 5"]:
            self.assertIn(paragraph, combined)


if __name__ == "__main__":
    unittest.main()