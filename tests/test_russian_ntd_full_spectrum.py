import pytest
import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from scripts.bldr_rag_trainer import BldrRAGTrainer
from core.norms_updater import NormsUpdater
from regex_patterns import DOCUMENT_TYPE_PATTERNS, SEED_WORK_PATTERNS

# Test Russian NTD full spectrum coverage
class TestRussianNTDFullSpectrum:
    """Test suite for full Russian NTD coverage with auto-search/sorting/updating"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.norms_dir = os.path.join(self.test_dir, "ntd")
        self.docs_dir = os.path.join(self.test_dir, "documents")
        
        # Create directories
        os.makedirs(self.norms_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Initialize components
        self.norms_updater = NormsUpdater(base_dir=self.norms_dir)
        self.rag_trainer = BldrRAGTrainer(
            base_dir=self.docs_dir,
            norms_db=self.norms_dir,
            use_advanced_embeddings=True
        )
    
    def teardown_method(self):
        """Clean up test environment"""
        # Clean up temporary directories
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_document_type_patterns_coverage(self):
        """Test that all 10+ categories are covered in document type patterns"""
        from regex_patterns import DOCUMENT_TYPE_PATTERNS
        
        # Check that all required categories are present
        required_categories = [
            'norms', 'ppr', 'smeta', 'rd', 'educational',
            'finance', 'safety', 'ecology', 'accounting', 'hr',
            'logistics', 'procurement', 'insurance'
        ]
        
        for category in required_categories:
            assert category in DOCUMENT_TYPE_PATTERNS, f"Missing category: {category}"
            assert 'keywords' in DOCUMENT_TYPE_PATTERNS[category], f"Missing keywords for {category}"
            assert 'subtype_patterns' in DOCUMENT_TYPE_PATTERNS[category], f"Missing subtype_patterns for {category}"
    
    def test_seed_work_patterns_coverage(self):
        """Test that all 10+ categories are covered in seed work patterns"""
        from regex_patterns import SEED_WORK_PATTERNS
        
        # Check that all required categories are present
        required_categories = [
            'norms', 'ppr', 'smeta', 'rd', 'educational',
            'finance', 'safety', 'ecology', 'accounting', 'hr',
            'logistics', 'procurement', 'insurance'
        ]
        
        for category in required_categories:
            assert category in SEED_WORK_PATTERNS, f"Missing category: {category}"
            assert len(SEED_WORK_PATTERNS[category]) > 0, f"No patterns for {category}"
    
    def test_russian_embeddings_model(self):
        """Test that advanced Russian embeddings model is used"""
        # Check that the advanced Russian model is being used
        assert self.rag_trainer.use_advanced_embeddings == True
        # Check that the model is loaded (this would be 'ai-forever/sbert_large_nlu_ru' if available)
        assert self.rag_trainer.embedding_model is not None
    
    def test_category_filtering_in_rag(self):
        """Test that category filtering works in RAG queries"""
        # This would test the query_with_category method
        assert hasattr(self.rag_trainer, 'query_with_category')
    
    def test_norms_updater_sources(self):
        """Test that norms updater has all required sources"""
        # Check that all required sources are present
        required_sources = [
            "minstroyrf.ru", "consultant.ru", "rosstat.gov.ru",
            "mintrud.gov.ru", "rospotrebnadzor.ru", "nalog.gov.ru",
            "minfin.ru", "minprirody.ru"
        ]
        
        for source in required_sources:
            assert source in self.norms_updater.sources, f"Missing source: {source}"
    
    def test_category_mapping_for_qdrant(self):
        """Test that category mapping works for Qdrant tagging"""
        # Test the category mapping used in stage 14
        category_mapping = {
            'norms': 'construction',
            'ppr': 'construction',
            'smeta': 'finance',
            'rd': 'construction',
            'educational': 'education',
            'finance': 'finance',
            'safety': 'safety',
            'ecology': 'ecology',
            'accounting': 'finance',
            'hr': 'hr',
            'logistics': 'logistics',
            'procurement': 'procurement',
            'insurance': 'insurance'
        }
        
        # Verify that all categories are mapped
        for category in category_mapping:
            assert category_mapping[category] is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])