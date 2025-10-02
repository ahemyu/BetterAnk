"""Integration tests for flashcard endpoints."""
import pytest
from datetime import datetime, timedelta


@pytest.mark.integration
class TestCreateFlashcard:
    """Test flashcard creation endpoint."""

    def test_create_flashcard_success(self, client, auth_headers, test_deck):
        """Test successful flashcard creation."""
        response = client.post(
            "/flashcards",
            headers=auth_headers,
            json={
                "front": "What is Python?",
                "back": "A programming language",
                "deck_id": test_deck.id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["front"] == "What is Python?"
        assert data["back"] == "A programming language"
        assert data["deck_id"] == test_deck.id
        assert "id" in data
        assert "created_at" in data
        assert "next_review_at" in data
        assert data["review_count"] == 0
        assert data["easiness_factor"] == 2.5
        assert data["interval"] == 1
        assert data["repetitions"] == 0

    def test_create_flashcard_without_deck(self, client, auth_headers):
        """Test creating flashcard without assigning to deck."""
        response = client.post(
            "/flashcards",
            headers=auth_headers,
            json={
                "front": "Question",
                "back": "Answer"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deck_id"] is None

    def test_create_flashcard_invalid_deck(self, client, auth_headers):
        """Test creating flashcard with non-existent deck."""
        response = client.post(
            "/flashcards",
            headers=auth_headers,
            json={
                "front": "Question",
                "back": "Answer",
                "deck_id": 99999
            }
        )
        assert response.status_code == 404

    def test_create_flashcard_unauthenticated(self, client):
        """Test creating flashcard without authentication."""
        response = client.post(
            "/flashcards",
            json={
                "front": "Question",
                "back": "Answer"
            }
        )
        assert response.status_code == 401

    def test_create_flashcard_missing_fields(self, client, auth_headers):
        """Test creating flashcard with missing required fields."""
        response = client.post(
            "/flashcards",
            headers=auth_headers,
            json={"front": "Only front"}
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestGetFlashcards:
    """Test listing flashcards endpoint."""

    def test_get_flashcards_empty(self, client, auth_headers):
        """Test getting flashcards when user has none."""
        response = client.get("/flashcards", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_flashcards_with_data(self, client, auth_headers, test_flashcard):
        """Test getting flashcards returns user's flashcards."""
        response = client.get("/flashcards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_flashcard.id
        assert data[0]["front"] == test_flashcard.front

    def test_get_flashcards_due_only(self, client, auth_headers, db_session, test_user):
        """Test filtering for due flashcards only."""
        from src.models import DBFlashcard

        # Create a due flashcard
        due_card = DBFlashcard(
            front="Due card",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now() - timedelta(hours=1)
        )
        # Create a future flashcard
        future_card = DBFlashcard(
            front="Future card",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now() + timedelta(days=1)
        )
        db_session.add_all([due_card, future_card])
        db_session.commit()

        response = client.get(
            "/flashcards?due=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        fronts = [card["front"] for card in data]
        assert "Due card" in fronts
        assert "Future card" not in fronts

    def test_get_flashcards_pagination(self, client, auth_headers, db_session, test_user):
        """Test flashcard pagination with limit."""
        from src.models import DBFlashcard

        # Create multiple flashcards
        for i in range(5):
            card = DBFlashcard(
                front=f"Question {i}",
                back=f"Answer {i}",
                user_id=test_user.id,
                created_at=datetime.now(),
                next_review_at=datetime.now()
            )
            db_session.add(card)
        db_session.commit()

        response = client.get("/flashcards?limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_flashcards_unauthenticated(self, client):
        """Test getting flashcards without authentication."""
        response = client.get("/flashcards")
        assert response.status_code == 401


@pytest.mark.integration
class TestGetFlashcard:
    """Test get single flashcard endpoint."""

    def test_get_flashcard_success(self, client, auth_headers, test_flashcard):
        """Test getting a specific flashcard."""
        response = client.get(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_flashcard.id
        assert data["front"] == test_flashcard.front
        assert data["back"] == test_flashcard.back

    def test_get_flashcard_not_found(self, client, auth_headers):
        """Test getting non-existent flashcard."""
        response = client.get("/flashcards/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_flashcard_unauthenticated(self, client, test_flashcard):
        """Test getting flashcard without authentication."""
        response = client.get(f"/flashcards/{test_flashcard.id}")
        assert response.status_code == 401

    def test_get_flashcard_other_user(self, client, db_session, test_flashcard):
        """Test user cannot access another user's flashcard."""
        from src.models import DBUser
        from src.utils import hash_password

        # Create another user
        other_user = DBUser(
            username="otheruser",
            email="other@example.com",
            hashed_password=hash_password("password123")
        )
        db_session.add(other_user)
        db_session.commit()

        # Login as other user
        response = client.post(
            "/login",
            data={"username": "otheruser", "password": "password123"}
        )
        other_token = response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access first user's flashcard
        response = client.get(
            f"/flashcards/{test_flashcard.id}",
            headers=other_headers
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestUpdateFlashcard:
    """Test flashcard update endpoint."""

    def test_update_flashcard_front(self, client, auth_headers, test_flashcard):
        """Test updating flashcard front."""
        response = client.put(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers,
            json={"front": "Updated question"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["front"] == "Updated question"
        assert data["back"] == test_flashcard.back

    def test_update_flashcard_back(self, client, auth_headers, test_flashcard):
        """Test updating flashcard back."""
        response = client.put(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers,
            json={"back": "Updated answer"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["back"] == "Updated answer"
        assert data["front"] == test_flashcard.front

    def test_update_flashcard_both_sides(self, client, auth_headers, test_flashcard):
        """Test updating both front and back."""
        response = client.put(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers,
            json={
                "front": "New question",
                "back": "New answer"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["front"] == "New question"
        assert data["back"] == "New answer"

    def test_update_flashcard_not_found(self, client, auth_headers):
        """Test updating non-existent flashcard."""
        response = client.put(
            "/flashcards/99999",
            headers=auth_headers,
            json={"front": "New"}
        )
        assert response.status_code == 404

    def test_update_flashcard_unauthenticated(self, client, test_flashcard):
        """Test updating flashcard without authentication."""
        response = client.put(
            f"/flashcards/{test_flashcard.id}",
            json={"front": "New"}
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestDeleteFlashcard:
    """Test flashcard deletion endpoint."""

    def test_delete_flashcard_success(self, client, auth_headers, test_flashcard):
        """Test successful flashcard deletion."""
        response = client.delete(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()

        # Verify flashcard is deleted
        get_response = client.get(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_flashcard_not_found(self, client, auth_headers):
        """Test deleting non-existent flashcard."""
        response = client.delete("/flashcards/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_flashcard_unauthenticated(self, client, test_flashcard):
        """Test deleting flashcard without authentication."""
        response = client.delete(f"/flashcards/{test_flashcard.id}")
        assert response.status_code == 401


@pytest.mark.integration
class TestReviewFlashcard:
    """Test flashcard review endpoint."""

    def test_review_flashcard_good(self, client, auth_headers, test_flashcard):
        """Test reviewing flashcard with GOOD feedback."""
        response = client.post(
            f"/flashcards/{test_flashcard.id}/review",
            headers=auth_headers,
            json={"feedback": "good"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["flashcard_id"] == test_flashcard.id
        assert data["feedback"] == "good"
        assert "review_at" in data

        # Verify flashcard was updated
        flashcard_response = client.get(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers
        )
        flashcard_data = flashcard_response.json()
        assert flashcard_data["review_count"] == 1
        assert flashcard_data["repetitions"] == 1

    def test_review_flashcard_mid(self, client, auth_headers, test_flashcard):
        """Test reviewing flashcard with MID feedback."""
        response = client.post(
            f"/flashcards/{test_flashcard.id}/review",
            headers=auth_headers,
            json={"feedback": "mid"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["feedback"] == "mid"

    def test_review_flashcard_bad(self, client, auth_headers, test_flashcard):
        """Test reviewing flashcard with BAD feedback."""
        response = client.post(
            f"/flashcards/{test_flashcard.id}/review",
            headers=auth_headers,
            json={"feedback": "bad"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["feedback"] == "bad"

        # Verify repetitions reset
        flashcard_response = client.get(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers
        )
        flashcard_data = flashcard_response.json()
        assert flashcard_data["repetitions"] == 0
        assert flashcard_data["interval"] == 1

    def test_review_flashcard_invalid_feedback(self, client, auth_headers, test_flashcard):
        """Test reviewing flashcard with invalid feedback."""
        response = client.post(
            f"/flashcards/{test_flashcard.id}/review",
            headers=auth_headers,
            json={"feedback": "invalid"}
        )
        assert response.status_code == 422

    def test_review_flashcard_not_found(self, client, auth_headers):
        """Test reviewing non-existent flashcard."""
        response = client.post(
            "/flashcards/99999/review",
            headers=auth_headers,
            json={"feedback": "good"}
        )
        assert response.status_code == 404

    def test_review_flashcard_unauthenticated(self, client, test_flashcard):
        """Test reviewing flashcard without authentication."""
        response = client.post(
            f"/flashcards/{test_flashcard.id}/review",
            json={"feedback": "good"}
        )
        assert response.status_code == 401

    def test_review_flashcard_updates_schedule(self, client, auth_headers, db_session, test_user):
        """Test that reviewing updates the next review date."""
        from src.models import DBFlashcard

        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()
        db_session.refresh(flashcard)

        original_next_review = flashcard.next_review_at

        # Review with good feedback
        client.post(
            f"/flashcards/{flashcard.id}/review",
            headers=auth_headers,
            json={"feedback": "good"}
        )

        # Get updated flashcard
        response = client.get(
            f"/flashcards/{flashcard.id}",
            headers=auth_headers
        )
        updated = response.json()

        # Next review should be in the future
        updated_next_review = datetime.fromisoformat(updated["next_review_at"].replace('Z', '+00:00'))
        assert updated_next_review > original_next_review


@pytest.mark.integration
class TestRemoveFlashcardFromDeck:
    """Test removing flashcard from deck endpoint."""

    def test_remove_flashcard_from_deck_success(self, client, auth_headers, test_flashcard, test_deck):
        """Test successfully removing flashcard from deck."""
        response = client.delete(
            f"/flashcards/{test_flashcard.id}/deck",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "removed from deck" in data["message"].lower()

        # Verify flashcard is no longer in deck
        flashcard_response = client.get(
            f"/flashcards/{test_flashcard.id}",
            headers=auth_headers
        )
        assert flashcard_response.json()["deck_id"] is None

    def test_remove_flashcard_not_in_deck(self, client, auth_headers, db_session, test_user):
        """Test removing flashcard that's not in any deck."""
        from src.models import DBFlashcard

        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            deck_id=None,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()
        db_session.refresh(flashcard)

        response = client.delete(
            f"/flashcards/{flashcard.id}/deck",
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_remove_flashcard_from_deck_not_found(self, client, auth_headers):
        """Test removing non-existent flashcard from deck."""
        response = client.delete(
            "/flashcards/99999/deck",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_remove_flashcard_from_deck_unauthenticated(self, client, test_flashcard):
        """Test removing flashcard from deck without authentication."""
        response = client.delete(f"/flashcards/{test_flashcard.id}/deck")
        assert response.status_code == 401
