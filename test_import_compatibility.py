#!/usr/bin/env python
"""
Test script to verify backward compatibility of refactored models package.
This verifies all documented import patterns work correctly.
"""

import sys

def test_imports():
    """Test all critical import patterns for backward compatibility."""
    print("Testing import compatibility for refactored models package...\n")
    
    errors = []
    
    # Test 1: Import classes from requests.models
    print("Test 1: Import classes from requests.models")
    try:
        from requests.models import Request, PreparedRequest, Response
        print("  ✓ from requests.models import Request, PreparedRequest, Response")
        assert Request is not None
        assert PreparedRequest is not None
        assert Response is not None
    except Exception as e:
        errors.append(f"  ✗ Failed to import classes: {e}")
        print(errors[-1])
    
    # Test 2: Import constants from requests.models
    print("\nTest 2: Import constants from requests.models")
    try:
        from requests.models import (
            DEFAULT_REDIRECT_LIMIT,
            REDIRECT_STATI,
            CONTENT_CHUNK_SIZE,
            ITER_CHUNK_SIZE
        )
        print("  ✓ from requests.models import DEFAULT_REDIRECT_LIMIT")
        print("  ✓ from requests.models import REDIRECT_STATI")
        print("  ✓ from requests.models import CONTENT_CHUNK_SIZE")
        print("  ✓ from requests.models import ITER_CHUNK_SIZE")
        assert DEFAULT_REDIRECT_LIMIT == 30
        assert isinstance(REDIRECT_STATI, tuple)
        assert CONTENT_CHUNK_SIZE == 10 * 1024
        assert ITER_CHUNK_SIZE == 512
    except Exception as e:
        errors.append(f"  ✗ Failed to import constants: {e}")
        print(errors[-1])
    
    # Test 3: Import urlencode re-export from requests.models
    print("\nTest 3: Import urlencode from requests.models (re-export from compat)")
    try:
        from requests.models import urlencode
        print("  ✓ from requests.models import urlencode")
        assert urlencode is not None
        assert callable(urlencode)
    except Exception as e:
        errors.append(f"  ✗ Failed to import urlencode: {e}")
        print(errors[-1])
    
    # Test 4: Import classes from requests public API
    print("\nTest 4: Import classes from requests public API")
    try:
        from requests import Request as ReqAPI, PreparedRequest as PrepAPI, Response as RespAPI
        print("  ✓ from requests import Request, PreparedRequest, Response")
        assert ReqAPI is not None
        assert PrepAPI is not None
        assert RespAPI is not None
    except Exception as e:
        errors.append(f"  ✗ Failed to import from requests API: {e}")
        print(errors[-1])
    
    # Test 5: Verify classes are the same when imported from different paths
    print("\nTest 5: Verify import paths point to same objects")
    try:
        from requests.models import Request as ModelReq
        from requests import Request as APIReq
        assert ModelReq is APIReq, "Request class differs between import paths"
        print("  ✓ requests.models.Request is requests.Request")
        
        from requests.models import PreparedRequest as ModelPrep
        from requests import PreparedRequest as APIPrep
        assert ModelPrep is APIPrep, "PreparedRequest class differs between import paths"
        print("  ✓ requests.models.PreparedRequest is requests.PreparedRequest")
        
        from requests.models import Response as ModelResp
        from requests import Response as APIResp
        assert ModelResp is APIResp, "Response class differs between import paths"
        print("  ✓ requests.models.Response is requests.Response")
    except Exception as e:
        errors.append(f"  ✗ Import paths not consistent: {e}")
        print(errors[-1])
    
    # Test 6: Test the specific imports used in tests/test_requests.py
    print("\nTest 6: Test imports used in tests/test_requests.py")
    try:
        from requests.models import PreparedRequest, urlencode
        print("  ✓ from requests.models import PreparedRequest, urlencode")
        assert PreparedRequest is not None
        assert urlencode is not None
    except Exception as e:
        errors.append(f"  ✗ Failed test_requests.py imports: {e}")
        print(errors[-1])
    
    # Test 7: Test imports used in sessions.py
    print("\nTest 7: Test imports used in sessions.py (internal)")
    try:
        from requests.models import (
            DEFAULT_REDIRECT_LIMIT,
            REDIRECT_STATI,
            PreparedRequest,
            Request,
        )
        print("  ✓ sessions.py imports verified")
    except Exception as e:
        errors.append(f"  ✗ Failed sessions.py imports: {e}")
        print(errors[-1])
    
    # Test 8: Test type hint imports for adapters.py
    print("\nTest 8: Test PreparedRequest can be imported for type hints")
    try:
        from requests.models import PreparedRequest
        # Type hints just need the name to be importable
        print("  ✓ PreparedRequest available for type hints")
    except Exception as e:
        errors.append(f"  ✗ Failed type hint import: {e}")
        print(errors[-1])
    
    # Summary
    print("\n" + "="*60)
    if errors:
        print(f"FAILED: {len(errors)} error(s) found:")
        for error in errors:
            print(error)
        return 1
    else:
        print("SUCCESS: All import compatibility tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(test_imports())
