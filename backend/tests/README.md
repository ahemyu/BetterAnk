# BetterAnk Backend Tests

Comprehensive test suite for the BetterAnk backend API.

## Test Structure

### Integration Tests
Integration tests verify the API endpoints together with the database and services, ensuring components work correctly together. These tests are marked with `@pytest.mark.integration`.

- **`test_authentication.py`**: Tests for user registration, login, and authentication
- **`test_decks.py`**: Tests for deck CRUD operations and deck-flashcard relationships
- **`test_flashcards.py`**: Tests for flashcard CRUD, reviews, and spaced repetition
- **`test_llm.py`**: Tests for LLM-powered flashcard generation from text and images

### Unit Tests
Unit tests verify specific components in isolation. These tests are marked with `@pytest.mark.unit`.

- **`test_sm2_algorithm.py`**: Tests for the SM-2 spaced repetition algorithm implementation

## Installation

Install test dependencies:

```bash
cd backend
pip install -e ".[test]"
```

This will install:
- pytest
- pytest-asyncio
- httpx (for FastAPI test client)
- faker (for generating test data)

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run only integration tests
```bash
pytest -m integration
```

### Run only unit tests
```bash
pytest -m unit
```

### Run specific test file
```bash
pytest tests/test_authentication.py
```

### Run specific test class
```bash
pytest tests/test_authentication.py::TestRegistration
```

### Run specific test
```bash
pytest tests/test_authentication.py::TestRegistration::test_register_new_user
```

### Run with coverage (optional)
```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

## Test Database

Tests use an in-memory SQLite database for fast, isolated testing. Each test gets a fresh database session via the `db_session` fixture in `conftest.py`.

## Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

- **`db_session`**: Fresh database session for each test
- **`client`**: FastAPI test client with database override
- **`test_user`**: Pre-created test user (username: "testuser")
- **`auth_headers`**: Authentication headers for the test user
- **`test_deck`**: Pre-created test deck belonging to test user
- **`test_flashcard`**: Pre-created test flashcard in test deck

## Test Coverage

The test suite covers:

### Authentication (test_authentication.py)
- ✅ User registration (success, duplicate username, duplicate email, validation)
- ✅ User login (success, wrong password, non-existent user)
- ✅ Get current user (authenticated, unauthenticated, invalid token)
- ✅ Delete user account

### Decks (test_decks.py)
- ✅ Create deck (with/without description)
- ✅ List decks (empty, with data, pagination)
- ✅ Get single deck (success, not found, unauthorized)
- ✅ Update deck (name, description, both)
- ✅ Delete deck
- ✅ Get deck flashcards (empty, with data, due filter)
- ✅ Add flashcard to deck

### Flashcards (test_flashcards.py)
- ✅ Create flashcard (with/without deck, validation)
- ✅ List flashcards (empty, with data, due filter, pagination)
- ✅ Get single flashcard (success, not found, unauthorized)
- ✅ Update flashcard (front, back, both)
- ✅ Delete flashcard
- ✅ Review flashcard (good/mid/bad feedback, schedule updates)
- ✅ Remove flashcard from deck

### LLM Generation (test_llm.py)
- ✅ Generate flashcards from text (success, with deck, errors)
- ✅ Generate flashcards from image (success, with deck, errors)
- ✅ Custom card count
- ✅ Validation and error handling

### SM-2 Algorithm (test_sm2_algorithm.py)
- ✅ Initial flashcard state
- ✅ Feedback processing (good, mid, bad)
- ✅ Interval progression (1, 6, exponential growth)
- ✅ Easiness factor updates and minimum threshold
- ✅ Repetition resets on bad feedback
- ✅ Next review date calculation
- ✅ Review count tracking
- ✅ Recovery after multiple failures

## Authentication Testing

Most endpoints require authentication. Tests use the `auth_headers` fixture which:
1. Creates a test user
2. Logs in to get a JWT token
3. Returns headers with the Bearer token

Example:
```python
def test_example(client, auth_headers):
    response = client.get("/protected-endpoint", headers=auth_headers)
    assert response.status_code == 200
```

## Mocking External Services

LLM tests mock the `get_llm_service()` function to avoid hitting the actual Gemini API during testing:

```python
@patch('src.llm_service.get_llm_service')
def test_example(mock_get_service, client, auth_headers):
    mock_service = Mock()
    mock_service.generate_flashcards.return_value = FlashcardBatch(...)
    mock_get_service.return_value = mock_service
    # ... test code
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. No external dependencies (PostgreSQL, Gemini API) are required - tests use:
- In-memory SQLite database
- Mocked LLM service

Example GitHub Actions workflow:
```yaml
- name: Install dependencies
  run: pip install -e ".[test]"

- name: Run tests
  run: pytest -v
```

## Writing New Tests

1. Add test file to `tests/` directory following naming convention `test_*.py`
2. Import pytest and mark tests appropriately (`@pytest.mark.contract` or `@pytest.mark.unit`)
3. Use existing fixtures from `conftest.py`
4. Follow the existing test structure (arrange, act, assert)
5. Test both success and failure cases
6. Test authentication requirements
7. Verify response status codes and data structure

Example:
```python
import pytest

@pytest.mark.integration
class TestMyEndpoint:
    def test_success_case(self, client, auth_headers):
        response = client.post("/my-endpoint", headers=auth_headers, json={...})
        assert response.status_code == 200
        assert "expected_field" in response.json()

    def test_unauthenticated(self, client):
        response = client.post("/my-endpoint", json={...})
        assert response.status_code == 401
```

## Troubleshooting

### Tests fail with "table already exists"
- This usually means the database wasn't cleaned up properly
- Check that you're using the `db_session` fixture
- Verify `Base.metadata.drop_all()` is called in fixture teardown

### Import errors
- Make sure you're running tests from the `backend` directory
- Verify all dependencies are installed: `pip install -e ".[test]"`

### Authentication failures in tests
- Check that `test_user` fixture is being used
- Verify the password matches in fixture and login attempt
- Ensure `auth_headers` fixture is available in test parameters

## Next Steps

After making changes to the backend:

1. Run the full test suite: `pytest`
2. Check for failures and fix them
3. Add new tests for new features
4. Ensure all tests pass before committing
5. Consider running with coverage to identify untested code

The tests provide a safety net for refactoring and ensure the API contract remains stable for frontend clients.
