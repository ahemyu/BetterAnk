"""Unit tests for SM-2 spaced repetition algorithm."""
import pytest
from datetime import datetime, timedelta
from src.spaced_repetition import SM2Algo
from src.models import DBFlashcard, ReviewFeedback


@pytest.mark.unit
class TestSM2Algorithm:
    """Test the SM-2 spaced repetition algorithm implementation."""

    def test_initial_flashcard_state(self, db_session, test_user):
        """Test that flashcards start with correct default values."""
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

        assert flashcard.easiness_factor == 2.5
        assert flashcard.interval == 1
        assert flashcard.repetitions == 0
        assert flashcard.review_count == 0

    def test_good_feedback_first_review(self, db_session, test_user):
        """Test GOOD feedback on first review."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()

        original_next_review = flashcard.next_review_at
        SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)

        assert flashcard.repetitions == 1
        assert flashcard.interval == 1  # First review interval is 1 day
        # EF increases by 0.1 for quality=5: 2.5 + 0.1 = 2.6
        assert flashcard.easiness_factor == 2.6
        assert flashcard.review_count == 1
        assert flashcard.last_reviewed_at is not None
        assert flashcard.next_review_at > original_next_review

    def test_good_feedback_second_review(self, db_session, test_user):
        """Test GOOD feedback on second review."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
            repetitions=1,
            interval=1,
            easiness_factor=2.5,
            review_count=1
        )
        db_session.add(flashcard)
        db_session.commit()

        SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)

        assert flashcard.repetitions == 2
        assert flashcard.interval == 6  # Second review interval is 6 days
        assert flashcard.review_count == 2

    def test_good_feedback_third_review(self, db_session, test_user):
        """Test GOOD feedback on third and subsequent reviews."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
            repetitions=2,
            interval=6,
            easiness_factor=2.5,
            review_count=2
        )
        db_session.add(flashcard)
        db_session.commit()

        SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)

        assert flashcard.repetitions == 3
        # EF increases to 2.6, then: interval = round(6 * 2.6) = round(15.6) = 16
        assert flashcard.interval == 16
        assert flashcard.review_count == 3

    def test_mid_feedback_updates_ef(self, db_session, test_user):
        """Test MID feedback updates easiness factor."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
            easiness_factor=2.5
        )
        db_session.add(flashcard)
        db_session.commit()

        original_ef = flashcard.easiness_factor
        SM2Algo.update_flashcard(ReviewFeedback.MID, flashcard)

        # MID = quality 3, should decrease EF
        # EF' = EF + (0.1 - (5-3)*(0.08 + (5-3)*0.02))
        # EF' = 2.5 + (0.1 - 2*(0.08 + 2*0.02))
        # EF' = 2.5 + (0.1 - 2*0.12) = 2.5 + (0.1 - 0.24) = 2.36
        assert flashcard.easiness_factor < original_ef
        assert flashcard.easiness_factor == pytest.approx(2.36, abs=0.01)
        assert flashcard.repetitions == 1

    def test_bad_feedback_resets_repetitions(self, db_session, test_user):
        """Test BAD feedback resets progress."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
            repetitions=5,
            interval=30,
            easiness_factor=2.5,
            review_count=5
        )
        db_session.add(flashcard)
        db_session.commit()

        SM2Algo.update_flashcard(ReviewFeedback.BAD, flashcard)

        # BAD feedback should reset repetitions and interval
        assert flashcard.repetitions == 0
        assert flashcard.interval == 1
        assert flashcard.review_count == 6  # Review count still increments
        # EF should not change (or stay at minimum)
        assert flashcard.easiness_factor >= 1.3

    def test_easiness_factor_minimum(self, db_session, test_user):
        """Test that easiness factor doesn't go below 1.3."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
            easiness_factor=1.3  # Already at minimum
        )
        db_session.add(flashcard)
        db_session.commit()

        # Apply BAD feedback multiple times
        for _ in range(3):
            SM2Algo.update_flashcard(ReviewFeedback.BAD, flashcard)

        # EF should not go below 1.3
        assert flashcard.easiness_factor >= 1.3

    def test_interval_progression(self, db_session, test_user):
        """Test interval progression over multiple reviews."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()

        intervals = []

        # Simulate 5 consecutive GOOD reviews
        for _ in range(5):
            SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)
            intervals.append(flashcard.interval)

        # Intervals should be: 1, 6, 15, 38, 94 (approximately)
        assert intervals[0] == 1
        assert intervals[1] == 6
        # Subsequent intervals grow exponentially
        for i in range(2, len(intervals)):
            assert intervals[i] > intervals[i-1]

    def test_next_review_date_calculation(self, db_session, test_user):
        """Test that next review date is calculated correctly."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()

        before_review = datetime.now()
        SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)

        # Next review should be approximately 'interval' days from now
        expected_next_review = before_review + timedelta(days=flashcard.interval)

        # Allow 5 second tolerance for test execution time
        time_diff = abs((flashcard.next_review_at - expected_next_review).total_seconds())
        assert time_diff < 5

    def test_last_reviewed_at_updated(self, db_session, test_user):
        """Test that last_reviewed_at is updated."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now(),
            last_reviewed_at=None
        )
        db_session.add(flashcard)
        db_session.commit()

        assert flashcard.last_reviewed_at is None

        before_review = datetime.now()
        SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)

        assert flashcard.last_reviewed_at is not None
        assert flashcard.last_reviewed_at >= before_review

    def test_review_count_increments(self, db_session, test_user):
        """Test that review count always increments."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()

        # Test with different feedbacks
        for i, feedback in enumerate([ReviewFeedback.GOOD, ReviewFeedback.MID, ReviewFeedback.BAD], 1):
            SM2Algo.update_flashcard(feedback, flashcard)
            assert flashcard.review_count == i

    def test_quality_mapping(self):
        """Test that feedback maps to correct quality values."""
        assert SM2Algo.QUALITY[ReviewFeedback.BAD] == 0
        assert SM2Algo.QUALITY[ReviewFeedback.MID] == 3
        assert SM2Algo.QUALITY[ReviewFeedback.GOOD] == 5

    def test_multiple_bad_then_good_recovery(self, db_session, test_user):
        """Test recovery after multiple bad reviews."""
        flashcard = DBFlashcard(
            front="Test",
            back="Answer",
            user_id=test_user.id,
            created_at=datetime.now(),
            next_review_at=datetime.now()
        )
        db_session.add(flashcard)
        db_session.commit()

        # Get to repetition 3
        for _ in range(3):
            SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)

        assert flashcard.repetitions == 3

        # Multiple bad reviews
        for _ in range(2):
            SM2Algo.update_flashcard(ReviewFeedback.BAD, flashcard)
            assert flashcard.repetitions == 0
            assert flashcard.interval == 1

        # Should be able to progress again
        SM2Algo.update_flashcard(ReviewFeedback.GOOD, flashcard)
        assert flashcard.repetitions == 1
        assert flashcard.interval == 1
