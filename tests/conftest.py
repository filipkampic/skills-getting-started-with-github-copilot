"""
Pytest configuration and shared fixtures for the test suite.
Provides a test client and clean test data for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Test data - minimal subset for fast, isolated tests
TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu"]
    }
}


@pytest.fixture
def client():
    """
    Provide a TestClient with clean test data.
    
    Replaces the app's in-memory activities with test data before the test,
    then restores original data after the test completes.
    """
    from src import app as app_module
    
    # Store original data
    original_activities = dict(app_module.activities)
    
    # Replace with test data
    app_module.activities.clear()
    app_module.activities.update(TEST_ACTIVITIES)
    
    # Create and yield the test client
    test_client = TestClient(app)
    yield test_client
    
    # Restore original data after test
    app_module.activities.clear()
    app_module.activities.update(original_activities)
