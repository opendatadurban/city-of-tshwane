from locust import HttpUser, task, between
from typing import Optional
import json
import random

API_V1_STR = "/api/v1"


class UserBehavior(HttpUser):
    host = "http://localhost:8080"
    wait_time = between(1, 3)  # Wait between 1-3 seconds between tasks
    token: Optional[str] = None
    user_id: Optional[str] = None
    item_ids: list[str] = []

    def on_start(self):
        """Create test user and login on start."""
        # Create a random user
        email = f"test_user_{random.randint(1000, 9999)}@example.com"
        password = "testpassword123"

        # Register user
        response = self.client.post(
            f"{API_V1_STR}/users/signup",
            json={
                "email": email,
                "password": password,
                "full_name": "Test User",
            },
        )
        if response.status_code == 201:
            self.user_id = response.json()["id"]

            # Login to get token
            response = self.client.post(
                f"{API_V1_STR}/login/access-token",
                data={
                    "username": email,
                    "password": password,
                },
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.client.headers = {"Authorization": f"Bearer {self.token}"}

    def on_stop(self):
        """Cleanup: Delete test user and items."""
        if self.token:
            self.client.delete(f"{API_V1_STR}/users/me")
            self.token = None
            self.user_id = None
            self.item_ids = []

    # Authentication Tasks
    @task(1)
    def test_token(self):
        """Verify token is valid."""
        self.client.post(f"{API_V1_STR}/login/test-token")

    # User Management Tasks
    @task(2)
    def get_current_user(self):
        """Get current user profile."""
        self.client.get(f"{API_V1_STR}/users/me")

    @task(1)
    def update_user_profile(self):
        """Update user profile."""
        self.client.patch(
            f"{API_V1_STR}/users/me",
            json={"full_name": f"Updated User {random.randint(1, 1000)}"},
        )

    # Item Management Tasks
    @task(3)
    def create_item(self):
        """Create a new item."""
        response = self.client.post(
            f"{API_V1_STR}/items/",
            json={
                "title": f"Test Item {random.randint(1, 1000)}",
                "description": "This is a test item description",
            },
        )
        if response.status_code == 201:
            self.item_ids.append(response.json()["id"])

    @task(4)
    def get_items(self):
        """Get list of items."""
        self.client.get(f"{API_V1_STR}/items/")

    @task(2)
    def get_specific_item(self):
        """Get a specific item if available."""
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            self.client.get(f"{API_V1_STR}/items/{item_id}")

    @task(2)
    def update_item(self):
        """Update an item if available."""
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            self.client.put(
                f"{API_V1_STR}/items/{item_id}",
                json={
                    "title": f"Updated Item {random.randint(1, 1000)}",
                    "description": "This is an updated test item description",
                },
            )

    @task(1)
    def delete_item(self):
        """Delete an item if available."""
        if self.item_ids:
            item_id = self.item_ids.pop()
            self.client.delete(f"{API_V1_STR}/items/{item_id}")


class AdminBehavior(HttpUser):
    host = "http://localhost:8080"
    wait_time = between(1, 3)
    token: Optional[str] = None

    def on_start(self):
        """Login as admin user."""
        # Note: Assumes an admin user exists with these credentials
        response = self.client.post(
            f"{API_V1_STR}/login/access-token",
            data={
                "username": "admin@example.com",
                "password": "changethis",
            },
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers = {"Authorization": f"Bearer {self.token}"}

    @task(2)
    def get_all_users(self):
        """Get list of all users."""
        self.client.get(f"{API_V1_STR}/users/")

    @task(1)
    def get_specific_user(self):
        """Get a specific user."""
        response = self.client.get(f"{API_V1_STR}/users/")
        if response.status_code == 200:
            users = response.json()["users"]
            if users:
                user = random.choice(users)
                self.client.get(f"{API_V1_STR}/users/{user['id']}")

    @task(1)
    def update_user(self):
        """Update a user."""
        response = self.client.get(f"{API_V1_STR}/users/")
        if response.status_code == 200:
            users = response.json()["users"]
            if users:
                user = random.choice(users)
                self.client.patch(
                    f"{API_V1_STR}/users/{user['id']}",
                    json={
                        "full_name": f"Updated Name {random.randint(1, 1000)}"
                    },
                )
