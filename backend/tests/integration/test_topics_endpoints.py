"""
Integration tests for Topics & Interests API endpoints.
Tests all 7 topics/interests endpoints from Sprint 2.
"""
import pytest
from fastapi import status


class TestTopicsDiscovery:
    """Test topic discovery and listing endpoints."""

    def test_list_topics_success(self, client, student_headers, sample_topics):
        """Test listing all topics."""
        response = client.get("/api/v1/topics", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "topics" in data
        assert "pagination" in data
        assert len(data["topics"]) >= 3  # Sample topics

    def test_list_topics_filter_by_subject(
        self, client, student_headers, sample_topics
    ):
        """Test filtering topics by subject."""
        response = client.get("/api/v1/topics?subject=Physics", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for topic in data["topics"]:
            assert topic["subject"] == "Physics"

    def test_list_topics_filter_by_grade(self, client, student_headers, sample_topics):
        """Test filtering topics by grade level."""
        response = client.get("/api/v1/topics?grade_level=10", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned topics should include grade 10
        for topic in data["topics"]:
            assert 10 in topic.get("grade_levels", [])

    def test_list_topics_pagination(self, client, student_headers, sample_topics):
        """Test topic pagination."""
        # First page
        response = client.get("/api/v1/topics?limit=2", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["topics"]) <= 2

        if data["pagination"]["has_more"]:
            # Second page
            next_cursor = data["pagination"]["next_cursor"]
            response2 = client.get(
                f"/api/v1/topics?limit=2&cursor={next_cursor}", headers=student_headers
            )
            assert response2.status_code == status.HTTP_200_OK

    def test_get_topic_details_success(self, client, student_headers, sample_topics):
        """Test getting detailed topic information."""
        topic_id = sample_topics[0].topic_id

        response = client.get(f"/api/v1/topics/{topic_id}", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["topic"]["topic_id"] == topic_id
        assert "prerequisites" in data
        assert "related_topics" in data

    def test_get_topic_not_found(self, client, student_headers):
        """Test getting non-existent topic."""
        response = client.get(
            "/api/v1/topics/nonexistent_topic", headers=student_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_topic_prerequisites(
        self, client, student_headers, sample_topics, db_session
    ):
        """Test getting topic prerequisites with completion status."""
        # Set up prerequisites
        topic = sample_topics[2]
        topic.prerequisites = [sample_topics[0].topic_id, sample_topics[1].topic_id]
        db_session.commit()

        response = client.get(
            f"/api/v1/topics/{topic.topic_id}/prerequisites", headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all("completed" in prereq for prereq in data)


class TestTopicsSearch:
    """Test topic search functionality."""

    def test_search_topics_success(self, client, student_headers, sample_topics):
        """Test searching topics by name."""
        response = client.get("/api/v1/topics/search?q=Newton", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "query" in data
        assert data["query"] == "Newton"

        # All results should contain "Newton" in name or description
        for result in data["results"]:
            topic = result["topic"]
            assert (
                "newton" in topic["name"].lower()
                or "newton" in (topic.get("description") or "").lower()
            )

    def test_search_topics_relevance_scoring(
        self, client, student_headers, sample_topics
    ):
        """Test that search results have relevance scores."""
        response = client.get("/api/v1/topics/search?q=Law", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for result in data["results"]:
            assert "relevance_score" in result
            assert 0 <= result["relevance_score"] <= 1

    def test_search_topics_min_query_length(self, client, student_headers):
        """Test that short queries are rejected."""
        response = client.get("/api/v1/topics/search?q=a", headers=student_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_topics_limit(self, client, student_headers, sample_topics):
        """Test search result limiting."""
        response = client.get(
            "/api/v1/topics/search?q=Newton&limit=1", headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["results"]) <= 1


class TestInterestsCatalog:
    """Test interests catalog endpoints."""

    def test_list_interests_success(self, client, student_headers, sample_interests):
        """Test listing all interests."""
        response = client.get("/api/v1/interests", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "interests" in data
        assert "total_count" in data
        assert "categories" in data
        assert len(data["interests"]) >= 5  # Sample interests

    def test_list_interests_includes_popularity(
        self, client, student_headers, sample_interests
    ):
        """Test that interests include popularity scores."""
        response = client.get("/api/v1/interests", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for interest in data["interests"]:
            assert "popularity" in interest
            assert 0 <= interest["popularity"] <= 1

    def test_list_interest_categories(self, client, student_headers, sample_interests):
        """Test listing interest categories."""
        response = client.get("/api/v1/interests/categories", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "categories" in data

        for category in data["categories"]:
            assert "category_id" in category
            assert "name" in category
            assert "interests" in category
            assert "interest_count" in category
            assert category["interest_count"] == len(category["interests"])

    def test_get_interest_details(self, client, student_headers, sample_interests):
        """Test getting individual interest details."""
        interest_id = sample_interests[0].interest_id

        response = client.get(
            f"/api/v1/interests/{interest_id}", headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["interest_id"] == interest_id
        assert "name" in data
        assert "category" in data

    def test_get_interest_not_found(self, client, student_headers):
        """Test getting non-existent interest."""
        response = client.get(
            "/api/v1/interests/nonexistent_interest", headers=student_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
