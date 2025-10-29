# Technical Debt Tracking

**Purpose**: This document catalogs known issues, incomplete features, and future improvement opportunities identified during codebase analysis. It serves as a single source of truth for tracked technical debt items that are separate from current structural refactoring work.

**Last Updated**: Current refactoring cycle  
**Related Work**: Models.py refactoring (completed), adapters package structure (planned)

---

## Scope and Separation from Current Refactoring

This technical debt document focuses on **functional improvements and feature completion**, while the current refactoring work focuses on **structural organization** (breaking up large monolithic files into modular packages).

### Why These Are Separate

- **Current Refactoring Goal**: Improve code organization and maintainability by restructuring large files into logical packages without changing functionality
- **Technical Debt Items**: Represent functional changes, feature additions, or breaking changes scheduled for future major versions (e.g., 3.0.0)
- **Risk Management**: Mixing structural changes with functional changes increases complexity and risk. Keeping them separate ensures:
  - Cleaner git history
  - Easier review and testing
  - Better rollback options if needed
  - Clear separation of concerns

---

## Priority Legend

- **Critical**: Blocks major functionality or has security implications
- **High**: Affects user experience or developer productivity significantly
- **Medium**: Important for long-term maintainability
- **Low**: Nice to have, minimal impact

---

## Categories

1. [Incomplete Features](#incomplete-features)
2. [Deprecations](#deprecations)
3. [Future Enhancements](#future-enhancements)
4. [Code Quality Issues](#code-quality-issues)

---

## Incomplete Features

Features marked as not implemented that need completion in future releases.

### 1. HTTP Digest Authentication - Entity Digest Support

**Priority**: Medium

**File**: `src/requests/auth.py`  
**Line**: 181

**Description**: Entity digest computation is not implemented in HTTP Digest Auth.

**Code Context**:
```python
# XXX not implemented yet
entdig = None
```

**Impact**: 
- Limited HTTP Digest Auth support
- May cause authentication failures with servers requiring entity digest
- Affects users needing full RFC 2617 compliance

**Related Standards**: RFC 2617 - HTTP Authentication: Basic and Digest Access Authentication

**Estimated Effort**: Medium (requires RFC implementation and testing)

---

### 2. HTTP Digest Authentication - Auth-Int QoP

**Priority**: Medium

**File**: `src/requests/auth.py`  
**Line**: 215

**Description**: The `auth-int` (authentication with integrity protection) quality of protection option is not implemented.

**Code Context**:
```python
if not qop:
    respdig = KD(HA1, f"{nonce}:{HA2}")
elif qop == "auth" or "auth" in qop.split(","):
    noncebit = f"{nonce}:{ncvalue}:{cnonce}:auth:{HA2}"
    respdig = KD(HA1, noncebit)
else:
    # XXX handle auth-int.
    return None
```

**Impact**:
- Authentication fails when server requires `auth-int` QoP
- Users cannot authenticate to servers with strict security requirements
- Limits enterprise/high-security environment usage

**Related Standards**: RFC 2617 Section 3.2.2.1

**Estimated Effort**: Medium-High (requires request body hashing implementation)

---

### 3. HTTP Digest Authentication - Partial Digest Encoding

**Priority**: Low

**File**: `src/requests/auth.py`  
**Line**: 220

**Description**: Uncertainty about whether partial digests should be encoded.

**Code Context**:
```python
# XXX should the partial digests be encoded too?
base = (
    f'username="{self.username}", realm="{realm}", nonce="{nonce}", '
    f'uri="{path}", response="{respdig}"'
)
```

**Impact**:
- Potential interoperability issues with specific server implementations
- Edge case authentication failures possible
- Low probability issue (most servers work with current implementation)

**Related Standards**: RFC 2617 - unclear specification in standard

**Estimated Effort**: Low (mainly research and testing)

---

## Deprecations

Code scheduled for removal or replacement in future versions.

### 1. Non-String Authentication Credentials

**Priority**: High

**File**: `src/requests/auth.py`  
**Lines**: 25-54

**Scheduled Removal**: Requests 3.0.0

**Description**: Automatic conversion of non-string usernames and passwords to strings will be removed.

**Code Context**:
```python
# These are here solely to maintain backwards compatibility
# for things like ints. This will be removed in 3.0.0.
if not isinstance(username, basestring):
    warnings.warn(
        "Non-string usernames will no longer be supported in Requests "
        "3.0.0. Please convert the object you've passed in ({!r}) to "
        "a string or bytes object in the near future to avoid "
        "problems.".format(username),
        category=DeprecationWarning,
    )
    username = str(username)
```

**Impact**:
- Breaking change for users passing non-string credentials (e.g., integers)
- Users must update code to explicitly convert credentials to strings
- Deprecation warnings already in place to notify users

**Migration Path**: Convert credentials to strings before passing to auth handlers

**Related Issues**: None referenced

**Estimated Effort**: Low (removal only, warnings already active)

---

### 2. Exception Handling for urllib3 Compatibility

**Priority**: Medium

**File**: `src/requests/adapters.py`  
**Line**: 663

**Scheduled Removal**: Requests 3.0.0

**Related Issue**: #2811

**Description**: Special handling for `ConnectTimeoutError` that isn't also a `NewConnectionError` needs removal.

**Code Context**:
```python
except MaxRetryError as e:
    if isinstance(e.reason, ConnectTimeoutError):
        # TODO: Remove this in 3.0.0: see #2811
        if not isinstance(e.reason, NewConnectionError):
            raise ConnectTimeout(e, request=request)
```

**Impact**:
- Maintains compatibility with older urllib3 versions
- Removing may affect users with older dependencies
- Simplifies exception handling logic

**Migration Path**: Ensure urllib3 version requirements are updated in 3.0.0

**Related Issues**: #2811

**Estimated Effort**: Low (removal of conditional check)

---

### 3. HTTPAdapter.get_connection() Method

**Priority**: High

**File**: `src/requests/adapters.py`  
**Lines**: 472-511

**Replacement**: `get_connection_with_tls_context()`

**Since Version**: 2.32.2

**Description**: The `get_connection` method is deprecated in favor of `get_connection_with_tls_context` which provides better TLS context handling.

**Code Context**:
```python
def get_connection(self, url, proxies=None):
    """DEPRECATED: Users should move to `get_connection_with_tls_context`
    for all subclasses of HTTPAdapter using Requests>=2.32.2.
    ...
    """
    warnings.warn(
        (
            "`get_connection` has been deprecated in favor of "
            "`get_connection_with_tls_context`. Custom HTTPAdapter subclasses "
            "will need to migrate for Requests>=2.32.2. Please see "
            "https://github.com/psf/requests/pull/6710 for more details."
        ),
        DeprecationWarning,
    )
```

**Impact**:
- Affects users with custom HTTPAdapter subclasses
- Better TLS security with new method
- Breaking change for 3.0.0

**Migration Path**: 
- Override `get_connection_with_tls_context()` instead of `get_connection()`
- See PR #6710 for migration guide

**Related Issues**: PR #6710

**Estimated Effort**: Low for library, Medium for users (migration required)

---

### 4. get_encodings_from_content() Function

**Priority**: Medium

**File**: `src/requests/utils.py`  
**Lines**: 479-501

**Scheduled Removal**: Requests 3.0.0

**Related Issue**: #2266

**Description**: Function for extracting encodings from HTML content will be removed.

**Code Context**:
```python
warnings.warn(
    (
        "In requests 3.0, get_encodings_from_content will be removed. For "
        "more information, please see the discussion on issue #2266. (This"
        " warning should only appear once.)"
    ),
    DeprecationWarning,
)
```

**Impact**:
- Users relying on this function need alternative solutions
- Functionality likely better handled by specialized libraries (e.g., chardet, beautifulsoup)
- Reduces requests' scope to core HTTP functionality

**Migration Path**: Use specialized encoding detection libraries

**Related Issues**: #2266

**Estimated Effort**: Low (removal only, warnings active)

---

### 5. get_unicode_from_response() Function

**Priority**: Medium

**File**: `src/requests/utils.py`  
**Lines**: 581-617

**Scheduled Removal**: Requests 3.0.0

**Related Issue**: #2266

**Description**: Function for getting unicode content from responses will be removed.

**Code Context**:
```python
warnings.warn(
    (
        "In requests 3.0, get_unicode_from_response will be removed. For "
        "more information, please see the discussion on issue #2266. (This"
        " warning should only appear once.)"
    ),
    DeprecationWarning,
)
```

**Impact**:
- Users must use native response.text or response.content handling
- Simplifies response handling code
- Better aligned with modern Python 3 string handling

**Migration Path**: Use `response.text` property for unicode content

**Related Issues**: #2266

**Estimated Effort**: Low (removal only, warnings active)

---

## Future Enhancements

Opportunities for expanding functionality beyond current scope.

### 1. Hook System Expansion

**Priority**: Low

**File**: `src/requests/hooks.py`  
**Line**: 19

**Description**: The hook system currently only supports the `response` hook. Additional hooks could be beneficial.

**Code Context**:
```python
HOOKS = ["response"]

# TODO: response is the only one
```

**Impact**:
- Limited extensibility for users wanting to hook into other lifecycle events
- Potential hooks could include:
  - `pre_request` - Before request is sent
  - `post_request` - After request completes (before response processing)
  - `on_error` - When exceptions occur
  - `on_redirect` - When redirects are followed
  - `pre_retry` - Before retry attempts

**Use Cases**:
- Custom logging at multiple points
- Request modification before sending
- Error handling and recovery
- Metrics collection
- Authentication token refresh

**Considerations**:
- Must maintain backward compatibility
- Need clear hook execution order
- Should not significantly impact performance
- Must be well-documented

**Estimated Effort**: Medium-High (design, implementation, testing, documentation)

**Related Work**: Review hook systems in other HTTP libraries (httpx, etc.)

---

## Code Quality Issues

Items that don't affect functionality but improve code quality.

### General Assessment

The codebase has **excellent code quality** overall. The technical debt items documented above are well-marked with appropriate comments (XXX, TODO) and most include deprecation warnings to guide users.

### Positive Observations

1. **Clear Deprecation Strategy**: All deprecations have:
   - Deprecation warnings with clear messages
   - Target version for removal (3.0.0)
   - Context about why the change is needed

2. **Well-Documented Limitations**: Incomplete features are marked with XXX comments explaining what's missing

3. **Issue Tracking**: Several items reference GitHub issues (e.g., #2811, #2266, PR #6710)

4. **Backward Compatibility**: Strong commitment to not breaking existing code until major version

### No Critical Issues Found

- No FIXME comments indicating urgent problems
- No HACK comments indicating workarounds that need replacement
- No security vulnerabilities identified in code comments

---

## Summary Statistics

| Category | Count | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Incomplete Features | 3 | 0 | 0 | 2 | 1 |
| Deprecations | 5 | 0 | 2 | 3 | 0 |
| Future Enhancements | 1 | 0 | 0 | 0 | 1 |
| Code Quality Issues | 0 | 0 | 0 | 0 | 0 |
| **Total** | **9** | **0** | **2** | **5** | **2** |

---

## Action Items for Requests 3.0.0

When planning the 3.0.0 release, address the following items:

### Must Complete Before 3.0.0

1. ✅ Remove non-string username/password conversion (`auth.py` lines 25-54)
2. ✅ Remove urllib3 compatibility workaround (`adapters.py` line 663, issue #2811)
3. ✅ Remove `get_connection()` method (`adapters.py` lines 472-511)
4. ✅ Remove `get_encodings_from_content()` (`utils.py` lines 479-501, issue #2266)
5. ✅ Remove `get_unicode_from_response()` (`utils.py` lines 581-617, issue #2266)

### Consider for 3.0.0

1. ⚠️ Complete HTTP Digest Auth implementation (auth-int QoP, entity digest)
2. ⚠️ Expand hook system beyond `response` hooks

### 3.0.0 Planning Notes

- Update urllib3 minimum version requirement
- Update migration guide with all breaking changes
- Run comprehensive test suite against new deprecations
- Update documentation to remove deprecated examples

---

## Maintenance Guidelines

### For Developers Adding Technical Debt

When introducing technical debt (incomplete features, TODOs, deprecations):

1. **Mark clearly** with standard comments:
   - `TODO:` for planned future work
   - `XXX:` for incomplete implementations or issues
   - `FIXME:` for code that needs fixing soon
   - `HACK:` for workarounds that need proper solutions

2. **Include context**:
   - Why the debt exists
   - What needs to be done
   - Reference GitHub issues when available
   - Target version for resolution

3. **Update this document**:
   - Add new items to appropriate category
   - Include priority, impact, and estimated effort
   - Keep summary statistics current

4. **Add deprecation warnings** for breaking changes:
   - Use `warnings.warn()` with `DeprecationWarning`
   - Include clear message about what to do instead
   - Specify target version for removal

### For Developers Resolving Technical Debt

When resolving items from this document:

1. **Mark as complete**: Update this document or remove the item
2. **Update related issues**: Close referenced GitHub issues
3. **Update HISTORY.md**: Document the change in release notes
4. **Update summary statistics**: Keep counts accurate

---

## Related Documents

- `CLEANUP_VERIFICATION_REPORT.md` - Models.py refactoring verification
- `COMPATIBILITY_VERIFICATION_REPORT.md` - Backward compatibility analysis
- `VERIFICATION_SUMMARY.md` - Testing summary
- `HISTORY.md` - Release notes and changelog

---

## Document History

- **Initial Creation**: Current refactoring cycle
- **Purpose**: Track technical debt discovered during models.py refactoring analysis
- **Scope**: Library-wide technical debt, not limited to refactored code

---

*This document serves as a living record of known technical debt. It should be updated whenever new debt is identified or existing debt is resolved.*
