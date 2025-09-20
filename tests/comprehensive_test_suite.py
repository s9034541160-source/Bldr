#!/usr/bin/env python3
"""
Comprehensive Test Suite for Bldr Empire v2
Tests all components including API, RAG pipeline, tools, plugins, and integrations.
"""
import unittest
import asyncio
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.bldr_rag_trainer import BldrRAGTrainer
from core.model_manager import ModelManager
from core.tools_system import ToolsSystem

class ComprehensiveTestSuite(unittest.TestCase):
    """Comprehensive test suite for all Bldr Empire v2 components"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Create temporary directories for testing
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.data_dir = cls.test_dir / "data"
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        cls.trainer = BldrRAGTrainer(
            base_dir=str(cls.data_dir),
            neo4j_uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_pass=os.getenv("NEO4J_PASSWORD", "neopassword"),
            qdrant_path=str(cls.test_dir / "qdrant_db")
        )
        
        cls.model_manager = ModelManager()
        cls.tools_system = ToolsSystem(cls.trainer, cls.model_manager)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        # Clean up temporary directories
        import shutil
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def test_01_rag_pipeline_initialization(self):
        """Test RAG pipeline initialization"""
        self.assertIsNotNone(self.trainer)
        self.assertIsNotNone(self.trainer.neo4j_driver)
        self.assertIsNotNone(self.trainer.qdrant_client)
        self.assertTrue(Path(self.trainer.base_dir).exists())
    
    def test_02_model_manager_initialization(self):
        """Test ModelManager initialization"""
        self.assertIsNotNone(self.model_manager)
        # Test that at least one role is available
        roles = self.model_manager.get_all_roles()
        self.assertGreater(len(roles), 0)
    
    def test_03_tools_system_initialization(self):
        """Test ToolsSystem initialization"""
        self.assertIsNotNone(self.tools_system)
        self.assertIsNotNone(self.tools_system.rag_system)
        self.assertIsNotNone(self.tools_system.model_manager)
        
        # Test that all required tools are registered
        required_tools = [
            "generate_letter",
            "auto_budget", 
            "generate_ppr",
            "create_gpp",
            "parse_gesn_estimate",
            "analyze_tender"
        ]
        for tool in required_tools:
            self.assertIn(tool, self.tools_system.tool_methods)
    
    def test_04_document_processing(self):
        """Test document processing pipeline"""
        # Create a sample document for testing
        sample_doc = self.data_dir / "sample.txt"
        sample_content = """
        СП 31.13330.2012. Свод правил. Системы противопожарной защиты. 
        Общие требования. Пожарная безопасность зданий и сооружений.
        
        cl.5.2 Требования к путям эвакуации
        1. Ширина путей эвакуации должна быть не менее 1.2 м.
        2. Высота путей эвакуации должна быть не менее 2.0 м.
        3. Пути эвакуации должны быть свободны от препятствий.
        """
        
        with open(sample_doc, "w", encoding="utf-8") as f:
            f.write(sample_content)
        
        # Process the document
        success = self.trainer.process_document(str(sample_doc))
        self.assertTrue(success)
        
        # Test querying the processed document
        results = self.trainer.query("требования к путям эвакуации", k=3)
        self.assertIsNotNone(results)
        self.assertIn("results", results)
        self.assertGreater(len(results["results"]), 0)
    
    def test_05_tool_execution(self):
        """Test tool execution"""
        # Test letter generation
        letter_args = {
            "template": "compliance_sp31",
            "data": {
                "recipient": "ООО СтройПроект",
                "subject": "Согласование проектной документации",
                "content": "Прошу согласовать представленную проектную документацию в соответствии с требованиями СП 31.13330.2012."
            }
        }
        
        result = self.tools_system.execute_tool("generate_letter", letter_args)
        self.assertIsNotNone(result)
        self.assertIn("status", result)
        # Note: This might fail if docx2pdf is not available, but shouldn't error
        
        # Test budget calculation
        budget_args = {
            "estimate_data": {
                "project_name": "Реконструкция здания",
                "positions": [
                    {"name": "Фундаментные работы", "quantity": 100, "unit": "м3", "rate": 5000},
                    {"name": "Кладка стен", "quantity": 200, "unit": "м2", "rate": 3000}
                ]
            },
            "gesn_rates": {}  # Use default rates
        }
        
        result = self.tools_system.execute_tool("auto_budget", budget_args)
        self.assertIsNotNone(result)
        self.assertIn("status", result)
        # Note: This might fail if pandas is not available, but shouldn't error
    
    def test_06_coordinator_integration(self):
        """Test coordinator integration with tools"""
        # Import Coordinator after other components are initialized
        from core.coordinator import Coordinator
        coordinator = Coordinator(self.model_manager, self.tools_system, self.trainer)
        self.assertIsNotNone(coordinator)
        self.assertIsNotNone(coordinator.model_manager)
        self.assertIsNotNone(coordinator.tools_system)
        self.assertIsNotNone(coordinator.rag_system)
    
    def test_07_plugin_functionality(self):
        """Test plugin functionality"""
        # Test that plugins can be loaded
        from core.plugin_manager import PluginManager
        plugin_manager = PluginManager()
        plugin_manager.load_all_plugins()
        
        # Check that plugins are loaded
        loaded_plugins = plugin_manager.get_loaded_plugins()
        self.assertIsNotNone(loaded_plugins)
        
        # Test webhook plugin
        webhook_plugin = plugin_manager.loaded_plugins.get("webhook_plugin")
        if webhook_plugin:
            # Test webhook registration
            success = webhook_plugin.register_webhook(
                "test_event",
                "http://localhost:8000/test",
                "test_secret"
            )
            self.assertTrue(success)
    
    def test_08_api_endpoints(self):
        """Test API endpoints (integration test)"""
        # Import the FastAPI app
        try:
            from core.bldr_api import app
            # Skip actual API testing as it requires running server
            self.assertIsNotNone(app)
        except ImportError:
            # Skip if API modules not available
            self.skipTest("API modules not available for testing")
    
    def test_09_performance_metrics(self):
        """Test performance and metrics"""
        import time
        
        # Test RAG query performance
        start_time = time.time()
        results = self.trainer.query("пожарная безопасность", k=5)
        query_time = time.time() - start_time
        
        # Query should complete in reasonable time
        self.assertLess(query_time, 10.0)  # Should be under 10 seconds
        self.assertIsNotNone(results)
        
        # Test NDCG score calculation
        if "ndcg" in results:
            self.assertIsInstance(results["ndcg"], (int, float))
            self.assertGreaterEqual(results["ndcg"], 0.0)
            self.assertLessEqual(results["ndcg"], 1.0)

def run_tests():
    """Run the comprehensive test suite"""
    print("🚀 Starting Comprehensive Test Suite for Bldr Empire v2")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ComprehensiveTestSuite)
    
    # Run tests with custom result handler
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Test failures: {len(result.failures)}")
    print(f"💥 Test errors: {len(result.errors)}")
    
    if result.failures:
        print("\n🔧 Failed Tests:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Test Errors:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)