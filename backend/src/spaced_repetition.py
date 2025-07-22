from models import DBFlashcard, ReviewFeedback
from datetime import datetime, timedelta

class SM2Algo: 

    QUALITY = {
        ReviewFeedback.BAD: 0,
        ReviewFeedback.MID: 3,
        ReviewFeedback.GOOD: 5
    }

    @classmethod
    def update_flashcard(cls, feedback: ReviewFeedback, flashcard: DBFlashcard):
        quality = cls.QUALITY[feedback]

        ### SM-2 Algorithm Implementation ###
        # 1. If quality is BAD reset repetitions
        if quality == 0:
            flashcard.repetitions = 0
            flashcard.interval = 1
        else:
            # 2. Update Easiness Factor
            new_ef = flashcard.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            flashcard.easiness_factor = max(1.3, new_ef)  # Easiness factor should not be less than 1.3

            # 3. Update repetitions and interval
            if flashcard.repetitions == 0:
                flashcard.interval = 1
            elif flashcard.repetitions == 1:
                flashcard.interval = 6
            else:
                flashcard.interval = round(flashcard.interval * flashcard.easiness_factor)
            
            flashcard.repetitions += 1

        # 4. Set next review date
        flashcard.next_review_at = datetime.now() + timedelta(days=flashcard.interval)        
        flashcard.last_reviewed_at = datetime.now()
        flashcard.review_count += 1
