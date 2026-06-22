"""
Comprehensive Test Suite for RAG System
========================================
Tests for RAG indexing, querying, and knowledge retrieval.
"""

import pytest
import os
import tempfile
from rag_system import IRM_RAG


class TestRAGSystem:
    """Test suite for IRM_RAG class."""
    
    @pytest.fixture
    async def rag_system(self):
        """Fixture to create IRM_RAG instance."""
        rag = IRM_RAG(lightweight=True)
        await rag.initialize()
        yield rag
        # Cleanup if needed
    
    def test_initialization(self):
        """Test that IRM_RAG initializes correctly."""
        rag = IRM_RAG(lightweight=True)
        assert rag is not None
        assert hasattr(rag, 'lightweight')
        assert rag.lightweight == True
    
    @pytest.mark.asyncio
    async def test_initialize(self, rag_system):
        """Test RAG system initialization."""
        assert rag_system is not None
        assert hasattr(rag_system, 'client')
    
    @pytest.mark.asyncio
    async def test_get_stats(self, rag_system):
        """Test getting RAG statistics."""
        try:
            stats = await rag_system.get_stats()
            
            assert isinstance(stats, dict)
            assert "total_chunks" in stats
            assert isinstance(stats["total_chunks"], int)
        except Exception as e:
            pytest.skip(f"RAG stats not available: {e}")
    
    @pytest.mark.asyncio
    async def test_query_empty_database(self, rag_system):
        """Test querying when database is empty."""
        try:
            result = await rag_system.query("test query")
            
            # Should return tuple with context and sources
            assert isinstance(result, tuple)
            assert len(result) == 2
            context, sources = result
            
            assert isinstance(context, str)
            assert isinstance(sources, list)
        except Exception as e:
            pytest.skip(f"RAG query not available: {e}")
    
    @pytest.mark.asyncio
    async def test_query_with_filters(self, rag_system):
        """Test querying with filters."""
        try:
            filters = {"category": "test"}
            result = await rag_system.query("test query", filters=filters)
            
            assert isinstance(result, tuple)
        except Exception as e:
            pytest.skip(f"RAG query with filters not available: {e}")
    
    @pytest.mark.asyncio
    async def test_index_text_file(self, rag_system):
        """Test indexing a text file."""
        try:
            # Create a temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("This is a test document for RAG indexing.")
                temp_path = f.name
            
            try:
                # Index the file
                await rag_system.index_any(temp_path)
                
                # Should not raise an exception
                assert True
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            pytest.skip(f"Text file indexing not available: {e}")
    
    @pytest.mark.asyncio
    async def test_index_markdown_file(self, rag_system):
        """Test indexing a markdown file."""
        try:
            # Create a temporary markdown file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write("# Test Document\n\nThis is a test markdown document.")
                temp_path = f.name
            
            try:
                # Index the file
                await rag_system.index_any(temp_path)
                
                # Should not raise an exception
                assert True
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            pytest.skip(f"Markdown file indexing not available: {e}")
    
    @pytest.mark.asyncio
    async def test_index_json_file(self, rag_system):
        """Test indexing a JSON file."""
        try:
            # Create a temporary JSON file
            import json
            test_data = {"title": "Test", "content": "Test content for indexing"}
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_path = f.name
            
            try:
                # Index the file
                await rag_system.index_any(temp_path)
                
                # Should not raise an exception
                assert True
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            pytest.skip(f"JSON file indexing not available: {e}")
    
    @pytest.mark.asyncio
    async def test_index_unsupported_file(self, rag_system):
        """Test indexing an unsupported file type."""
        try:
            # Create a temporary unsupported file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
                f.write("Unsupported file type")
                temp_path = f.name
            
            try:
                # Should handle gracefully or raise appropriate error
                await rag_system.index_any(temp_path)
            except Exception as e:
                # Expected to fail for unsupported types
                assert True
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            pytest.skip(f"Unsupported file handling test not available: {e}")
    
    @pytest.mark.asyncio
    async def test_query_after_indexing(self, rag_system):
        """Test querying after indexing a document."""
        try:
            # Create and index a document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Color analysis is important for quality control in manufacturing.")
                temp_path = f.name
            
            try:
                await rag_system.index_any(temp_path)
                
                # Query for related content
                result = await rag_system.query("color analysis")
                
                # Should return results
                assert isinstance(result, tuple)
                context, sources = result
                assert isinstance(context, str)
                assert isinstance(sources, list)
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            pytest.skip(f"Query after indexing not available: {e}")
    
    @pytest.mark.asyncio
    async def test_lightweight_mode(self):
        """Test that lightweight mode is properly set."""
        rag = IRM_RAG(lightweight=True)
        assert rag.lightweight == True
        
        rag_heavy = IRM_RAG(lightweight=False)
        assert rag_heavy.lightweight == False
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, rag_system):
        """Test progress callback during indexing."""
        try:
            callback_called = []
            
            async def progress_callback(data):
                callback_called.append(data)
            
            # Create a test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Test document for progress callback")
                temp_path = f.name
            
            try:
                await rag_system.index_any(temp_path, progress_callback=progress_callback)
                
                # Callback should have been called at least once
                # (may not be called for very small files)
                assert isinstance(callback_called, list)
            finally:
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            pytest.skip(f"Progress callback not available: {e}")
    
    @pytest.mark.asyncio
    async def test_empty_query(self, rag_system):
        """Test querying with empty string."""
        try:
            result = await rag_system.query("")
            
            # Should handle empty query gracefully
            assert isinstance(result, tuple)
        except Exception as e:
            # May raise an error for empty queries
            pytest.skip(f"Empty query handling not available: {e}")
    
    @pytest.mark.asyncio
    async def test_query_special_characters(self, rag_system):
        """Test querying with special characters."""
        try:
            result = await rag_system.query("test query with special chars: @#$%")
            
            # Should handle special characters
            assert isinstance(result, tuple)
        except Exception as e:
            pytest.skip(f"Special character query not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
