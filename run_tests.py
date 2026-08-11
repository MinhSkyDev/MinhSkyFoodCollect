import sys
import unittest

if __name__ == "__main__":
    print("=" * 60)
    print("[TESTS] Running Unit Tests for Munch Recap Backend")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        sys.exit(1)
