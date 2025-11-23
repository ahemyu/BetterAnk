"""Integration tests for deck endpoints."""

import pytest


@pytest.mark.integration
class TestCreateDeck:
    """Test deck creation endpoint."""

    def test_create_deck_success(self, client, auth_headers):
        """Test successful deck creation."""
        response = client.post(
            "/decks",
            headers=auth_headers,
            json={"name": "My Deck", "description": "A deck for learning"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Deck"
        assert data["description"] == "A deck for learning"
        assert "id" in data
        assert "created_at" in data

    def test_create_deck_without_description(self, client, auth_headers):
        """Test creating deck without optional description."""
        response = client.post(
            "/decks", headers=auth_headers, json={"name": "Minimal Deck"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Deck"

    def test_create_deck_unauthenticated(self, client):
        """Test creating deck without authentication fails."""
        response = client.post("/decks", json={"name": "Test Deck"})
        assert response.status_code == 401

    def test_create_deck_missing_name(self, client, auth_headers):
        """Test creating deck without name fails."""
        response = client.post(
            "/decks", headers=auth_headers, json={"description": "No name"}
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestGetDecks:
    """Test listing decks endpoint."""

    def test_get_decks_empty(self, client, auth_headers):
        """Test getting decks when user has none."""
        response = client.get("/decks", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_decks_with_data(self, client, auth_headers, test_deck):
        """Test getting decks returns user's decks."""
        response = client.get("/decks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_deck.id
        assert data[0]["name"] == test_deck.name

    def test_get_decks_pagination(self, client, auth_headers, db_session, test_user):
        """Test deck pagination with limit."""
        # Create multiple decks
        from src.models import DBDeck
        from datetime import datetime

        for i in range(5):
            deck = DBDeck(
                name=f"Deck {i}", user_id=test_user.id, created_at=datetime.now()
            )
            db_session.add(deck)
        db_session.commit()

        response = client.get("/decks?limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_decks_unauthenticated(self, client):
        """Test getting decks without authentication fails."""
        response = client.get("/decks")
        assert response.status_code == 401


@pytest.mark.integration
class TestGetDeck:
    """Test get single deck endpoint."""

    def test_get_deck_success(self, client, auth_headers, test_deck):
        """Test getting a specific deck."""
        response = client.get(f"/decks/{test_deck.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_deck.id
        assert data["name"] == test_deck.name
        assert data["description"] == test_deck.description

    def test_get_deck_not_found(self, client, auth_headers):
        """Test getting non-existent deck."""
        response = client.get("/decks/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_deck_unauthenticated(self, client, test_deck):
        """Test getting deck without authentication."""
        response = client.get(f"/decks/{test_deck.id}")
        assert response.status_code == 401

    def test_get_deck_other_user(self, client, db_session, test_deck):
        """Test user cannot access another user's deck."""
        # Create another user
        from src.models import DBUser
        from src.utils import hash_password

        other_user = DBUser(
            username="otheruser",
            email="other@example.com",
            hashed_password=hash_password("password123"),
        )
        db_session.add(other_user)
        db_session.commit()

        # Login as other user
        response = client.post(
            "/login", data={"username": "otheruser", "password": "password123"}
        )
        other_token = response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access first user's deck
        response = client.get(f"/decks/{test_deck.id}", headers=other_headers)
        assert response.status_code == 404


@pytest.mark.integration
class TestUpdateDeck:
    """Test deck update endpoint."""

    def test_update_deck_name(self, client, auth_headers, test_deck):
        """Test updating deck name."""
        response = client.put(
            f"/decks/{test_deck.id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == test_deck.id

    def test_update_deck_description(self, client, auth_headers, test_deck):
        """Test updating deck description."""
        response = client.put(
            f"/decks/{test_deck.id}",
            headers=auth_headers,
            json={"description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    def test_update_deck_both_fields(self, client, auth_headers, test_deck):
        """Test updating both name and description."""
        response = client.put(
            f"/decks/{test_deck.id}",
            headers=auth_headers,
            json={"name": "New Name", "description": "New Description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New Description"

    def test_update_deck_not_found(self, client, auth_headers):
        """Test updating non-existent deck."""
        response = client.put(
            "/decks/99999", headers=auth_headers, json={"name": "New Name"}
        )
        assert response.status_code == 404

    def test_update_deck_unauthenticated(self, client, test_deck):
        """Test updating deck without authentication."""
        response = client.put(f"/decks/{test_deck.id}", json={"name": "New Name"})
        assert response.status_code == 401


@pytest.mark.integration
class TestDeleteDeck:
    """Test deck deletion endpoint."""

    def test_delete_deck_success(self, client, auth_headers, test_deck):
        """Test successful deck deletion."""
        response = client.delete(f"/decks/{test_deck.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()

        # Verify deck is deleted
        get_response = client.get(f"/decks/{test_deck.id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_deck_not_found(self, client, auth_headers):
        """Test deleting non-existent deck."""
        response = client.delete("/decks/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_deck_unauthenticated(self, client, test_deck):
        """Test deleting deck without authentication."""
        response = client.delete(f"/decks/{test_deck.id}")
        assert response.status_code == 401


@pytest.mark.integration
class TestGetDeckFlashcards:
    """Test getting flashcards from a deck."""

    def test_get_deck_flashcards_empty(
        self, client, auth_headers, db_session, test_user
    ):
        """Test getting flashcards from empty deck."""
        from src.models import DBDeck
        from datetime import datetime

        deck = DBDeck(
            name="Empty Deck", user_id=test_user.id, created_at=datetime.now()
        )
        db_session.add(deck)
        db_session.commit()
        db_session.refresh(deck)

        response = client.get(f"/decks/{deck.id}/flashcards", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_deck_flashcards_with_data(
        self, client, auth_headers, test_deck, test_flashcard
    ):
        """Test getting flashcards from deck."""
        response = client.get(f"/decks/{test_deck.id}/flashcards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_flashcard.id

    def test_get_deck_flashcards_due_only(
        self, client, auth_headers, test_deck, db_session, test_user
    ):
        """Test filtering for due flashcards only."""
        from src.models import DBFlashcard
        from datetime import datetime, timedelta

        # Create a due flashcard
        due_card = DBFlashcard(
            front="Due",
            back="Now",
            user_id=test_user.id,
            deck_id=test_deck.id,
            created_at=datetime.now(),
            next_review_at=datetime.now() - timedelta(hours=1),
        )
        # Create a future flashcard
        future_card = DBFlashcard(
            front="Future",
            back="Later",
            user_id=test_user.id,
            deck_id=test_deck.id,
            created_at=datetime.now(),
            next_review_at=datetime.now() + timedelta(days=1),
        )
        db_session.add_all([due_card, future_card])
        db_session.commit()

        response = client.get(
            f"/decks/{test_deck.id}/flashcards?due=true", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should only include the due card, not the future one
        assert all(card["front"] != "Future" for card in data)

    def test_get_deck_flashcards_not_found(self, client, auth_headers):
        """Test getting flashcards from non-existent deck."""
        response = client.get("/decks/99999/flashcards", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.integration
class TestAddFlashcardToDeck:
    """Test adding flashcard to deck endpoint."""

    def test_add_flashcard_to_deck_success(
        self, client, auth_headers, test_deck, db_session, test_user
    ):
        """Test successfully adding flashcard to deck."""
        from src.models import DBFlashcard
        from datetime import datetime

        # Create flashcard not in any deck
        flashcard = DBFlashcard(
            front="Question",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
        )
        db_session.add(flashcard)
        db_session.commit()
        db_session.refresh(flashcard)

        response = client.put(
            f"/decks/{test_deck.id}/flashcard/{flashcard.id}", headers=auth_headers
        )
        assert response.status_code == 200

        # Verify flashcard is in deck
        get_response = client.get(
            f"/decks/{test_deck.id}/flashcards", headers=auth_headers
        )
        flashcard_ids = [f["id"] for f in get_response.json()]
        assert flashcard.id in flashcard_ids

    def test_add_flashcard_to_deck_not_found_flashcard(
        self, client, auth_headers, test_deck
    ):
        """Test adding non-existent flashcard to deck."""
        response = client.put(
            f"/decks/{test_deck.id}/flashcard/99999", headers=auth_headers
        )
        assert response.status_code == 404

    def test_add_flashcard_to_deck_not_found_deck(
        self, client, auth_headers, test_flashcard
    ):
        """Test adding flashcard to non-existent deck."""
        response = client.put(
            f"/decks/99999/flashcard/{test_flashcard.id}", headers=auth_headers
        )
        assert response.status_code == 404

    def test_add_flashcard_to_deck_unauthenticated(
        self, client, test_deck, test_flashcard
    ):
        """Test adding flashcard to deck without authentication."""
        response = client.put(f"/decks/{test_deck.id}/flashcard/{test_flashcard.id}")
        assert response.status_code == 401


@pytest.mark.integration
class TestSubdeckBehavior:
    """Test parent/subdeck specific logic."""

    def test_create_subdeck_success(self, client, auth_headers, test_deck):
        """Users can create a subdeck referencing a parent deck they own."""
        response = client.post(
            "/decks",
            headers=auth_headers,
            json={
                "name": "Child Deck",
                "description": "Nested",
                "parent_id": test_deck.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == test_deck.id

    def test_create_subdeck_parent_not_found(self, client, auth_headers):
        """Creating a subdeck with invalid parent fails."""
        response = client.post(
            "/decks",
            headers=auth_headers,
            json={"name": "Missing Parent", "parent_id": 99999},
        )
        assert response.status_code == 404

    def test_nested_subdeck_not_allowed(
        self, client, auth_headers, db_session, test_user, test_deck
    ):
        """Subdecks cannot themselves be parents for additional levels."""
        from src.models import DBDeck
        from datetime import datetime

        subdeck = DBDeck(
            name="Immediate Child",
            user_id=test_user.id,
            created_at=datetime.now(),
            parent_id=test_deck.id,
        )
        db_session.add(subdeck)
        db_session.commit()
        db_session.refresh(subdeck)

        response = client.post(
            "/decks",
            headers=auth_headers,
            json={"name": "Grandchild", "parent_id": subdeck.id},
        )
        assert response.status_code == 400

    def test_get_deck_includes_subdecks(
        self, client, auth_headers, db_session, test_user, test_deck
    ):
        """Deck detail can return immediate subdecks."""
        from src.models import DBDeck
        from datetime import datetime

        for idx in range(2):
            db_session.add(
                DBDeck(
                    name=f"Child {idx}",
                    user_id=test_user.id,
                    created_at=datetime.now(),
                    parent_id=test_deck.id,
                )
            )
        db_session.commit()

        response = client.get(
            f"/decks/{test_deck.id}?include_subdecks=true",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["subdecks"]) == 2

    def test_parent_flashcards_include_subdecks(
        self, client, auth_headers, db_session, test_user, test_deck
    ):
        """Requesting a parent deck aggregates flashcards from subdecks."""
        from src.models import DBDeck, DBFlashcard
        from datetime import datetime

        subdeck = DBDeck(
            name="Child",
            user_id=test_user.id,
            created_at=datetime.now(),
            parent_id=test_deck.id,
        )
        db_session.add(subdeck)
        db_session.commit()
        db_session.refresh(subdeck)

        db_session.add_all(
            [
                DBFlashcard(
                    front="Parent Card",
                    back="Answer",
                    user_id=test_user.id,
                    deck_id=test_deck.id,
                    created_at=datetime.now(),
                    next_review_at=datetime.now(),
                ),
                DBFlashcard(
                    front="Child Card",
                    back="Answer",
                    user_id=test_user.id,
                    deck_id=subdeck.id,
                    created_at=datetime.now(),
                    next_review_at=datetime.now(),
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"/decks/{test_deck.id}/flashcards",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_subdeck_flashcards_are_scoped(
        self, client, auth_headers, db_session, test_user, test_deck
    ):
        """Subdeck review pulls only its own flashcards."""
        from src.models import DBDeck, DBFlashcard
        from datetime import datetime

        subdeck = DBDeck(
            name="Child",
            user_id=test_user.id,
            created_at=datetime.now(),
            parent_id=test_deck.id,
        )
        db_session.add(subdeck)
        db_session.commit()
        db_session.refresh(subdeck)

        db_session.add_all(
            [
                DBFlashcard(
                    front="Parent Card",
                    back="Answer",
                    user_id=test_user.id,
                    deck_id=test_deck.id,
                    created_at=datetime.now(),
                    next_review_at=datetime.now(),
                ),
                DBFlashcard(
                    front="Child Card",
                    back="Answer",
                    user_id=test_user.id,
                    deck_id=subdeck.id,
                    created_at=datetime.now(),
                    next_review_at=datetime.now(),
                ),
            ]
        )
        db_session.commit()

        response = client.get(
            f"/decks/{subdeck.id}/flashcards",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["deck_id"] == subdeck.id
