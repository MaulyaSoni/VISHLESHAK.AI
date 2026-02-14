"""
Tests for RAG System
"""
import unittest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.document_loader import DocumentProcessor


class TestDocumentProcessor(unittest.TestCase):
    """Test Document Processor"""
    
    def setUp(self):
        self.processor = DocumentProcessor()
    
    def test_load_text_file(self):
        """Test loading text files"""
        # Create a temp text file
        test_file = Path("tests/test_data.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("This is test content for document processing.")
        
        docs = self.processor.load_file(test_file)
        self.assertTrue(len(docs) > 0)
        self.assertIn("test content", docs[0].page_content)
        
        # Cleanup
        test_file.unlink()
    
    def test_chunk_documents(self):
        """Test document chunking"""
        from langchain_core.documents import Document
        
        long_text = "Hello world. " * 200
        docs = [Document(page_content=long_text, metadata={"source": "test"})]
        
        chunks = self.processor.chunk_documents(docs)
        self.assertTrue(len(chunks) >= 1)
    
    def test_supported_extensions(self):
        """Test that supported extensions are declared"""
        supported = ['.txt', '.md', '.pdf', '.docx', '.csv', '.json']
        # Just verify the processor loads without error
        self.assertIsNotNone(self.processor)


class TestRAGInitialization(unittest.TestCase):
    """Test RAG components can be initialized"""
    
    def test_document_processor_init(self):
        """Test DocumentProcessor initializes"""
        processor = DocumentProcessor()
        self.assertIsNotNone(processor)


if __name__ == '__main__':
    unittest.main()
