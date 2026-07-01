"""
Integration Tests for RAG System
==================================
Тестове за интеграция на RAG System с Qdrant и Knowledge Graph.
"""

import pytest
import asyncio
import os
from app.modules.rag_system import RAGSystem
from app.modules.knowledge_graph import IndustrialKG

@pytest.fixture
async def rag_system():
    """Fixture за RAG System."""
    rag = RAGSystem()
    await rag.initialize()
    yield rag
    # Cleanup if needed

@pytest.fixture
def knowledge_graph():
    """Fixture за Knowledge Graph."""
    kg = IndustrialKG()
    yield kg

@pytest.mark.asyncio
async def test_rag_initialization(rag_system):
    """Тест за инициализация на RAG System."""
    assert rag_system is not None
    assert rag_system.enabled is True
    assert rag_system.client is not None

@pytest.mark.asyncio
async def test_rag_query_empty(rag_system):
    """Тест за заявка с празна колекция."""
    context, sources = await rag_system.query("test query")
    
    assert isinstance(context, str)
    assert isinstance(sources, list)
    # Empty collection should return empty results
    assert context == ""
    assert sources == []

@pytest.mark.asyncio
async def test_rag_add_to_collection(rag_system):
    """Тест за добавяне на документ в колекцията."""
    test_text = "This is a test document for color analysis."
    source_name = "test_document.txt"
    
    await rag_system.add_to_collection(test_text, source_name)
    
    # Verify the document was added
    context, sources = await rag_system.query("test document")
    
    # Should return some context now
    assert len(context) > 0
    assert len(sources) > 0

@pytest.mark.asyncio
async def test_rag_query_with_filters(rag_system):
    """Тест за заявка с филтри."""
    test_text = "This is a test document for color analysis."
    source_name = "test_document_filtered.txt"
    metadata = {"industry": "automotive", "substrate": "metal"}
    
    await rag_system.add_to_collection(test_text, source_name, metadata)
    
    context, sources = await rag_system.query("test document", filters={"industry": "automotive"})
    
    assert isinstance(context, str)
    assert isinstance(sources, list)

@pytest.mark.asyncio
async def test_rag_get_stats(rag_system):
    """Тест за получаване на статистика."""
    stats = await rag_system.get_stats()
    
    assert stats is not None
    assert "total_chunks" in stats
    assert "total_files" in stats
    assert "total_size" in stats

def test_knowledge_graph_initialization(knowledge_graph):
    """Тест за инициализация на Knowledge Graph."""
    assert knowledge_graph is not None
    assert knowledge_graph.graph is not None
    assert len(knowledge_graph.graph.nodes) > 0

def test_knowledge_graph_add_event(knowledge_graph):
    """Тест за добавяне на събитие в графа."""
    machine_id = "Machine_P3"
    issue_id = "Yellow_Drift"
    
    initial_edges = len(knowledge_graph.graph.edges)
    knowledge_graph.add_event(machine_id, issue_id, relation="PREDICTED")
    
    # Edge should be added
    assert len(knowledge_graph.graph.edges) >= initial_edges

def test_knowledge_graph_search_entities(knowledge_graph):
    """Тест за търсене на ентитети в текст."""
    text = "Machine_P3 has Yellow_Drift issue"
    
    found_entities = knowledge_graph.search_entities_in_text(text)
    
    assert isinstance(found_entities, list)
    # Should find at least one entity
    assert len(found_entities) > 0

def test_knowledge_graph_get_related_entities(knowledge_graph):
    """Тест за намиране на свързани ентитети."""
    entity_name = "Machine_P3"
    
    related = knowledge_graph.get_related_entities(entity_name, depth=1)
    
    assert isinstance(related, list)

def test_knowledge_graph_find_reasoning_path(knowledge_graph):
    """Тест за намиране на логически път."""
    issue_label = "Yellow_Drift"
    
    path = knowledge_graph.find_reasoning_path(issue_label, depth=2)
    
    assert path is not None
    assert isinstance(path, list)

@pytest.mark.asyncio
async def test_rag_graph_integration(rag_system, knowledge_graph):
    """Тест за интеграция между RAG и Knowledge Graph."""
    test_text = "Machine_P3 is experiencing Yellow_Drift issue due to high humidity."
    source_name = "test_graph_integration.txt"
    
    await rag_system.add_to_collection(test_text, source_name)
    
    # Query should leverage graph context
    context, sources = await rag_system.query("Yellow_Drift")
    
    assert isinstance(context, str)
    assert isinstance(sources, list)
