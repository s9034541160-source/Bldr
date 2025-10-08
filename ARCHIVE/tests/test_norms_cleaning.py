"""
Test suite for NTD base cleaning functionality
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
import hashlib

# Try to import required modules with error handling
PANDAS_AVAILABLE = False
pd = None
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    print("Warning: Pandas not available")

NORMS_MODULES_AVAILABLE = False
try:
    from core.norms_scan import NormsScanner
    from core.norms_processor import NormsProcessor
    NORMS_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Norms modules not available: {e}")

class TestNormsCleaning(unittest.TestCase):
    """Test cases for NTD base cleaning functionality"""
    
    def setUp(self):
        """Set up test environment"""
        if not NORMS_MODULES_AVAILABLE:
            self.skipTest("Norms modules not available")
        
        # Create temporary directories for testing
        self.test_dir = Path(tempfile.mkdtemp())
        self.base_dir = self.test_dir / "base"
        self.clean_base_dir = self.test_dir / "clean_base"
        
        # Create base directory
        self.base_dir.mkdir(parents=True)
        self.clean_base_dir.mkdir(parents=True)
        
        # Create test files
        self._create_test_files()
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directories
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_files(self):
        """Create test files for deduplication testing"""
        # Create two identical files (duplicates)
        content1 = b"Test content for duplicate detection"
        file1 = self.base_dir / "test1.pdf"
        file2 = self.base_dir / "test2.pdf"
        
        with open(file1, 'wb') as f:
            f.write(content1)
        
        with open(file2, 'wb') as f:
            f.write(content1)
        
        # Create a unique file
        content3 = b"Unique test content"
        file3 = self.base_dir / "unique.pdf"
        
        with open(file3, 'wb') as f:
            f.write(content3)
    
    def test_file_hash_calculation(self):
        """Test that file hashes are calculated correctly"""
        # Calculate hash of a test file
        test_file = self.base_dir / "test1.pdf"
        with open(test_file, 'rb') as f:
            content = f.read()
            calculated_hash = hashlib.md5(content).hexdigest()
        
        # Verify hash is a valid MD5 hash
        self.assertEqual(len(calculated_hash), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in calculated_hash))
    
    @unittest.skipIf(not PANDAS_AVAILABLE, "Pandas not available")
    def test_duplicate_detection(self):
        """Test that duplicate files are detected"""
        # Create scanner and scan base
        scanner = NormsScanner(base_dir=str(self.base_dir))
        df = scanner.scan_base()
        
        # Should find 3 files
        self.assertEqual(len(df), 3)
        
        # Should find 2 duplicates (same hash)
        duplicates = scanner.find_duplicates(df)
        self.assertEqual(len(duplicates), 2)
    
    def test_norms_scanner_initialization(self):
        """Test that NormsScanner initializes correctly"""
        if not NORMS_MODULES_AVAILABLE:
            self.skipTest("Norms modules not available")
            
        scanner = NormsScanner(base_dir=str(self.base_dir))
        self.assertEqual(str(scanner.base_dir), str(self.base_dir))
    
    def test_norms_processor_initialization(self):
        """Test that NormsProcessor initializes correctly"""
        if not NORMS_MODULES_AVAILABLE:
            self.skipTest("Norms modules not available")
            
        processor = NormsProcessor(
            base_dir=str(self.base_dir),
            clean_base_dir=str(self.clean_base_dir)
        )
        self.assertEqual(str(processor.base_dir), str(self.base_dir))
        self.assertEqual(str(processor.clean_base_dir), str(self.clean_base_dir))

if __name__ == '__main__':
    unittest.main()