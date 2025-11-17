"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    global activities
    # Store original state
    original_state = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, activity in original_state.items():
        activities[name]["participants"] = activity["participants"].copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_has_expected_activities(self, client):
        """Test that GET /activities returns expected activity names"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = ["Chess Club", "Programming Class", "Gym Class", 
                              "Basketball Team", "Tennis Club", "Art Studio",
                              "Music Band", "Debate Club", "Science Olympiad"]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing {field}"
    
    def test_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_valid_activity(self, client):
        """Test successful signup for a valid activity"""
        email = "test@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to activity"""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_duplicate_signup_fails(self, client):
        """Test that signing up twice for same activity fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_for_multiple_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify participant is in both
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client):
        """Test successful unregistration of an existing participant"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/unregister",
            json={"email": email}
        )
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        client.post(
            "/activities/Chess Club/unregister",
            json={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            json={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered_participant(self, client):
        """Test unregistering a participant not in the activity fails"""
        email = "notregistered@mergington.edu"
        response = client.post(
            "/activities/Chess Club/unregister",
            json={"email": email}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_signup_then_unregister(self, client):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        
        # Sign up
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Verify signup
        response2 = client.get("/activities")
        assert email in response2.json()["Chess Club"]["participants"]
        
        # Unregister
        response3 = client.post(
            "/activities/Chess Club/unregister",
            json={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify unregistration
        response4 = client.get("/activities")
        assert email not in response4.json()["Chess Club"]["participants"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_activity_name_with_spaces(self, client):
        """Test that activity names with spaces work correctly"""
        email = "spaces@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_email_validation_basic(self, client):
        """Test that various email formats are accepted"""
        test_emails = [
            "student@mergington.edu",
            "first.last@mergington.edu",
            "student123@mergington.edu"
        ]
        
        for i, email in enumerate(test_emails):
            # Use different activities to avoid duplicate signup errors
            activities_list = ["Chess Club", "Programming Class", "Gym Class"]
            response = client.post(
                f"/activities/{activities_list[i]}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
