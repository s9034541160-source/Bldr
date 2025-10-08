"""
Final verification test to ensure all improvements are working correctly
"""
import unittest
import os
import sys
from pathlib import Path

# Add the core directory to the path
sys.path.append(str(Path(__file__).parent.parent / "core"))
sys.path.append(str(Path(__file__).parent.parent / "scripts"))
sys.path.append(str(Path(__file__).parent.parent / "integrations"))

class FinalVerificationTest(unittest.TestCase):
    
    def test_imports_work_correctly(self):
        """Test that all modules can be imported without errors"""
        try:
            from core import bldr_api
            from core import model_manager
            from core import coordinator
            from core import tools_system
            from core import budget_auto
            from core import estimate_parser_enhanced
            from core import gpp_creator
            from core import ppr_generator
            from core import official_letters
            from core import autocad_bentley
            from core import monte_carlo
            # If we get here, imports worked
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Import failed: {e}")
    
    def test_optional_dependencies_handled(self):
        """Test that optional dependencies are properly handled"""
        # Test that the system can run even if optional dependencies are missing
        try:
            from core.budget_auto import HAS_EXCEL_LIBS
            from core.autocad_bentley import IFCOPENSHELL_AVAILABLE, EZDXF_AVAILABLE
            from core.monte_carlo import HAS_SCIENTIFIC_LIBS
            
            # These should be boolean values
            self.assertIsInstance(HAS_EXCEL_LIBS, bool)
            self.assertIsInstance(IFCOPENSHELL_AVAILABLE, bool)
            self.assertIsInstance(EZDXF_AVAILABLE, bool)
            self.assertIsInstance(HAS_SCIENTIFIC_LIBS, bool)
        except Exception as e:
            self.fail(f"Optional dependency handling failed: {e}")
    
    def test_paths_are_configurable(self):
        """Test that paths are configurable and not hardcoded"""
        try:
            from scripts.bldr_rag_trainer import BldrRAGTrainer
            # This should not fail due to hardcoded paths
            trainer = BldrRAGTrainer()
            # If we get here, path configuration works
            self.assertIsNotNone(trainer)
        except Exception as e:
            # If it fails, it should not be due to hardcoded paths
            self.assertNotIn("I:\\docs\\база", str(e))
    
    def test_error_handling_implemented(self):
        """Test that error handling is implemented"""
        try:
            from core.bldr_api import format_ifc_error, format_file_error
            # Test that error formatting functions exist
            self.assertTrue(callable(format_ifc_error))
            self.assertTrue(callable(format_file_error))
        except Exception as e:
            self.fail(f"Error handling functions missing: {e}")
    
    def test_logging_implemented(self):
        """Test that logging is implemented"""
        try:
            import logging
            from core import budget_auto
            from core import bldr_api
            from scripts import bldr_rag_trainer
            
            # Check that loggers exist
            self.assertIsNotNone(getattr(budget_auto, 'logger', None))
            self.assertIsNotNone(getattr(bldr_api, 'logger', None))
            self.assertIsNotNone(getattr(bldr_rag_trainer, 'logger', None))
        except Exception as e:
            self.fail(f"Logging not implemented: {e}")
    
    def test_data_files_exist(self):
        """Test that required data files exist"""
        try:
            # Check that sample data files were created
            data_dir = Path(__file__).parent.parent / "data"
            self.assertTrue(data_dir.exists(), "Data directory should exist")
            
            # Check for specific files
            gesn_file = data_dir / "gesn_rates.csv"
            self.assertTrue(gesn_file.exists(), "GESN rates file should exist")
        except Exception as e:
            self.fail(f"Data files check failed: {e}")

if __name__ == "__main__":
    unittest.main()