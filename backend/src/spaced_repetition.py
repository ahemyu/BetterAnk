import logging
from src.models import DBFlashcard, ReviewFeedback
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SM2Algo: 

    QUALITY = {
        ReviewFeedback.BAD: 0,
        ReviewFeedback.MID: 3,
        ReviewFeedback.GOOD: 5
    }

    @classmethod
    def update_flashcard(cls, feedback: ReviewFeedback, flashcard: DBFlashcard):
        quality = cls.QUALITY[feedback]
        logger.debug(f"Updating flashcard {flashcard.id} with feedback: {feedback} (quality: {quality})")
        logger.debug(f"Current state - repetitions: {flashcard.repetitions}, interval: {flashcard.interval}, EF: {flashcard.easiness_factor}")

        ### SM-2 Algorithm Implementation ###
        # 1. If quality is BAD reset repetitions
        if quality == 0:
            logger.debug(f"Flashcard {flashcard.id}: BAD feedback - resetting repetitions")
            flashcard.repetitions = 0
            flashcard.interval = 1
        else:
            # 2. Update Easiness Factor
            new_ef = flashcard.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            flashcard.easiness_factor = max(1.3, new_ef)  # Easiness factor should not be less than 1.3
            logger.debug(f"Flashcard {flashcard.id}: Updated EF to {flashcard.easiness_factor}")

            # 3. Update repetitions and interval
            if flashcard.repetitions == 0:
                flashcard.interval = 1
            elif flashcard.repetitions == 1:
                flashcard.interval = 6
            else:
                flashcard.interval = round(flashcard.interval * flashcard.easiness_factor)

            flashcard.repetitions += 1
            logger.debug(f"Flashcard {flashcard.id}: Updated interval to {flashcard.interval} days, repetitions: {flashcard.repetitions}")

        # 4. Set next review date
        flashcard.next_review_at = datetime.now() + timedelta(days=flashcard.interval)
        flashcard.last_reviewed_at = datetime.now()
        flashcard.review_count += 1
        logger.info(f"Flashcard {flashcard.id} updated: next review in {flashcard.interval} days ({flashcard.next_review_at})")
