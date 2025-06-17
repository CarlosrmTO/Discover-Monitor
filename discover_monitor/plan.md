# Discover Monitor - Test Coverage Improvement Plan

## Current Status (2025-06-18)

### Test Coverage
- **Overall Coverage**: 31% (Target: 80%)
- **app.py**: 94% coverage
- **scraper.py**: 12% coverage
- **main.py**: 0% coverage

### Completed Tasks
- [x] Set up testing infrastructure (pytest, pytest-cov)
- [x] Fix failing tests in `test_app.py` and `test_app_coverage.py`
- [x] Add comprehensive tests for filter logic
- [x] Add tests for export functionality (CSV, Excel, PDF)
- [x] Add error handling tests
- [x] Create `test_app_remaining.py` for additional test coverage

### Current Issues
1. **Test Failures**
   - `test_main_success` failing due to Streamlit session state mocking
   - Some UI-related tests are disabled due to environment issues

2. **Low Coverage**
   - `scraper.py` needs significant test coverage
   - `main.py` has no test coverage
   - Some edge cases in `app.py` still need testing

## Next Steps

### High Priority
1. **Fix Remaining Test Failures**
   - [ ] Fix `test_main_success` by properly mocking Streamlit session state
   - [ ] Re-enable and fix UI tests once environment issues are resolved

2. **Improve Test Coverage**
   - [ ] Add tests for `scraper.py` (target: 80% coverage)
   - [ ] Add tests for `main.py` (target: 80% coverage)
   - [ ] Add integration tests for the full data pipeline

3. **Documentation**
   - [ ] Update README with testing instructions
   - [ ] Document test coverage requirements and practices
   - [ ] Add code comments for complex test cases

### Medium Priority
1. **CI/CD Integration**
   - [ ] Set up GitHub Actions for automated testing
   - [ ] Add coverage reporting to PRs
   - [ ] Enforce minimum coverage requirements

2. **Test Optimization**
   - [ ] Identify and remove duplicate test cases
   - [ ] Optimize slow-running tests
   - [ ] Add test data factories for better test data management

## Technical Notes

### Testing Dependencies
- pytest
- pytest-cov
- pytest-mock
- pytest-playwright (for UI tests)

### Running Tests
```bash
# Run all tests with coverage report
pytest --cov=app --cov=scraper --cov=main --cov-report=term-missing

# Run a specific test file
pytest tests/test_app.py -v

# Run tests with HTML coverage report
pytest --cov=. --cov-report=html
```

### Known Issues
- UI tests require `pytest-xvfb` which is currently disabled
- Some tests may be flaky due to timing issues with Streamlit
- PDF export tests require additional dependencies (reportlab, fpdf)

## Progress Tracking

| Date       | Coverage | Key Changes |
|------------|----------|-------------|
| 2025-06-17 | 31%      | Initial test improvements, fixed export tests |
| 2025-06-17 | 94% app.py | Added comprehensive tests for app.py |
| 2025-06-17 | 12% scraper.py | Initial test coverage for scraper.py |
