"""
Test suite for Mergington High School Activities API

All tests follow the AAA (Arrange-Act-Assert) pattern:
- ARRANGE: Set up test data and preconditions
- ACT: Execute the action being tested
- ASSERT: Verify the results
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client: TestClient):
        """
        ARRANGE: Client is ready with test data (2 activities)
        ACT: GET /activities
        ASSERT: Returns both activities
        """
        # Arrange
        expected_activity_names = {"Chess Club", "Programming Class"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        assert set(activities.keys()) == expected_activity_names

    def test_get_activities_returns_correct_structure(self, client: TestClient):
        """
        ARRANGE: Client ready
        ACT: GET /activities
        ASSERT: Each activity has required fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict)
            assert set(activity_data.keys()) == required_fields
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_correct_participant_counts(self, client: TestClient):
        """
        ARRANGE: Test data with known participant counts
        ACT: GET /activities
        ASSERT: Participant counts match test data
        """
        # Arrange
        expected_counts = {
            "Chess Club": 1,
            "Programming Class": 1
        }

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, expected_count in expected_counts.items():
            actual_count = len(activities[activity_name]["participants"])
            assert actual_count == expected_count


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client: TestClient):
        """
        ARRANGE: Client ready
        ACT: GET / (without following redirects)
        ASSERT: Returns 307 redirect to /static/index.html
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client: TestClient):
        """
        ARRANGE: Activity exists, student not yet registered
        ACT: POST /activities/{activity_name}/signup with new email
        ASSERT: Student added, returns 200 with success message
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Verify student is not already registered
        activities_before = client.get("/activities").json()
        assert new_email not in activities_before[activity_name]["participants"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        # Assert
        assert response.status_code == 200
        response_json = response.json()
        assert "message" in response_json
        assert new_email in response_json["message"]
        assert activity_name in response_json["message"]

        # Verify participant was actually added
        activities_after = client.get("/activities").json()
        assert new_email in activities_after[activity_name]["participants"]
        assert len(activities_after[activity_name]["participants"]) > len(activities_before[activity_name]["participants"])

    def test_signup_activity_not_found(self, client: TestClient):
        """
        ARRANGE: Nonexistent activity name
        ACT: POST /activities/{nonexistent}/signup
        ASSERT: Returns 404 error
        """
        # Arrange
        fake_activity = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json
        assert "not found" in response_json["detail"].lower()

    def test_signup_student_already_registered(self, client: TestClient):
        """
        ARRANGE: Student already signed up for activity
        ACT: POST /activities/{activity_name}/signup with existing email
        ASSERT: Returns 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club from test data

        # Verify student is already registered
        activities = client.get("/activities").json()
        assert existing_email in activities[activity_name]["participants"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        response_json = response.json()
        assert "detail" in response_json
        assert "already signed up" in response_json["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client: TestClient):
        """
        ARRANGE: Activity with existing participants
        ACT: Sign up two different new students
        ASSERT: Both students added successfully
        """
        # Arrange
        activity_name = "Programming Class"
        student1 = "alice@mergington.edu"
        student2 = "bob@mergington.edu"

        # Act - Sign up first student
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student1}
        )

        # Act - Sign up second student
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student2}
        )

        # Assert both signups succeeded
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify both students are in the activity
        activities = client.get("/activities").json()
        participants = activities[activity_name]["participants"]
        assert student1 in participants
        assert student2 in participants


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_success(self, client: TestClient):
        """
        ARRANGE: Student is registered for activity
        ACT: POST /activities/{activity_name}/unregister with their email
        ASSERT: Student removed, returns 200 with success message
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"

        # Verify student is registered before removal
        activities_before = client.get("/activities").json()
        assert email_to_remove in activities_before[activity_name]["participants"]
        count_before = len(activities_before[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )

        # Assert
        assert response.status_code == 200
        response_json = response.json()
        assert "message" in response_json
        assert "Unregistered" in response_json["message"]
        assert email_to_remove in response_json["message"]

        # Verify participant was actually removed
        activities_after = client.get("/activities").json()
        assert email_to_remove not in activities_after[activity_name]["participants"]
        assert len(activities_after[activity_name]["participants"]) == count_before - 1

    def test_unregister_activity_not_found(self, client: TestClient):
        """
        ARRANGE: Nonexistent activity name
        ACT: POST /activities/{nonexistent}/unregister
        ASSERT: Returns 404 error
        """
        # Arrange
        fake_activity = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        response_json = response.json()
        assert "detail" in response_json
        assert "not found" in response_json["detail"].lower()

    def test_unregister_student_not_registered(self, client: TestClient):
        """
        ARRANGE: Student not registered for activity
        ACT: POST /activities/{activity_name}/unregister with unregistered email
        ASSERT: Returns 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        unregistered_email = "notregistered@mergington.edu"

        # Verify student is not registered
        activities = client.get("/activities").json()
        assert unregistered_email not in activities[activity_name]["participants"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": unregistered_email}
        )

        # Assert
        assert response.status_code == 400
        response_json = response.json()
        assert "detail" in response_json
        assert "not signed up" in response_json["detail"].lower()

    def test_unregister_multiple_students(self, client: TestClient):
        """
        ARRANGE: Activity with multiple participants
        ACT: Unregister each student one by one
        ASSERT: All students removed successfully
        """
        # Arrange
        activity_name = "Programming Class"
        
        # First, sign up new students
        new_student1 = "charlie@mergington.edu"
        new_student2 = "diana@mergington.edu"
        client.post(f"/activities/{activity_name}/signup", params={"email": new_student1})
        client.post(f"/activities/{activity_name}/signup", params={"email": new_student2})

        activities = client.get("/activities").json()
        count_before = len(activities[activity_name]["participants"])

        # Act - Remove first student
        response1 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": new_student1}
        )

        # Act - Remove second student
        response2 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": new_student2}
        )

        # Assert both removals succeeded
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify both students are removed
        activities_after = client.get("/activities").json()
        participants = activities_after[activity_name]["participants"]
        assert new_student1 not in participants
        assert new_student2 not in participants
        assert len(participants) == count_before - 2


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_then_unregister_flow(self, client: TestClient):
        """
        ARRANGE: Test data ready
        ACT: Sign up a student, then unregister them
        ASSERT: Both operations succeed and activity state is correct
        """
        # Arrange
        activity_name = "Chess Club"
        email = "integration@mergington.edu"

        activities_initial = client.get("/activities").json()
        initial_count = len(activities_initial[activity_name]["participants"])

        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert signup succeeded
        assert signup_response.status_code == 200
        activities_after_signup = client.get("/activities").json()
        assert email in activities_after_signup[activity_name]["participants"]
        assert len(activities_after_signup[activity_name]["participants"]) == initial_count + 1

        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert unregister succeeded
        assert unregister_response.status_code == 200
        activities_final = client.get("/activities").json()
        assert email not in activities_final[activity_name]["participants"]
        assert len(activities_final[activity_name]["participants"]) == initial_count

    def test_cannot_unregister_after_failed_signup(self, client: TestClient):
        """
        ARRANGE: Student never signed up
        ACT: Try to unregister a student who never registered
        ASSERT: Signup would have failed, unregister also fails
        """
        # Arrange
        activity_name = "Tennis Club"  # Not in test data
        email = "failedstudent@mergington.edu"

        # Act - Try signup to nonexistent activity
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert signup failed
        assert signup_response.status_code == 404

        # Act - Try unregister from same nonexistent activity
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert unregister also fails
        assert unregister_response.status_code == 404
