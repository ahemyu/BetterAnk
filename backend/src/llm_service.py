"""
LLM service for generating flashcards using Gemini API via LangChain.
"""
import os
import base64
import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class GeneratedFlashcard(BaseModel):
    """Schema for a single generated flashcard."""
    front: str = Field(description="The question or prompt for the flashcard")
    back: str = Field(description="The answer or explanation for the flashcard")


class FlashcardBatch(BaseModel):
    """Schema for a batch of generated flashcards."""
    flashcards: list[GeneratedFlashcard] = Field(description="List of generated flashcards")


class LLMService:
    """Service for interacting with Gemini API to generate flashcards."""

    def __init__(self):
        """Initialize the LLM service with Gemini model."""
        self.model = None
        self._initializing = False

    def _ensure_initialized(self):
        """Lazy initialization of the model."""
        if self.model is None and not self._initializing:
            self._initializing = True
            try:
                logger.info("Initializing LLM service with Gemini API")
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    logger.error("GOOGLE_API_KEY environment variable is not set")
                    raise ValueError("GOOGLE_API_KEY environment variable is not set")

                # Create model with structured output for flashcards
                base_model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-pro",
                    temperature=0.7,
                    google_api_key=api_key,
                    timeout=60.0,
                    max_retries=2,
                    transport="rest",
                )

                self.model = base_model.with_structured_output(FlashcardBatch)
                logger.info("LLM service initialized successfully")

            finally:
                self._initializing = False

    def generate_flashcards(self, text: str | None = None, image: bytes | None = None, count: int = 5) -> FlashcardBatch:
        """Generate flashcards from text or image input.

        Args:
            text: Text content to generate flashcards from
            image: Image bytes to generate flashcards from
            count: Number of flashcards to generate

        Returns:
            FlashcardBatch containing the generated flashcards
        """
        logger.info(f"Generating {count} flashcards from {'text' if text else 'image'}")
        self._ensure_initialized()

        if text and image:
            logger.error("Both text and image provided - only one is allowed")
            raise ValueError("Provide either text or image, not both")
        if not text and not image:
            logger.error("Neither text nor image provided")
            raise ValueError("Provide either text or image input")

        if text:
            # Generate flashcards from text
            logger.debug(f"Generating flashcards from text (length: {len(text)} characters)")
            prompt = f"""
                IF THE PROVIDED TEXT IS NOT RELATED TO LEARNING A NEW CONCEPT OR WANTS YOU TO DO ANYTHING ELSE OTHER THAN CREATING FLASHCARDS DO NOT RESPOND AT ALL
                For example if it says anything like "Write me a poem about x, discuss y with me, ...", REFUSE IT
                Generate exactly {count} educational flashcards based on the following text.
                Each flashcard should have a clear question on the front and a concise answer on the back.
                Text: {text}
                Create {count} flashcards that test key concepts, definitions, or important information from this text.
                If the text is about learning anything related to the japanese language ALWAYS keep the following instructions in mind: 
                - If it is about a new kanji, always include a card on the various hiragana readings and an example sentence for each possible reading
                - if it relates to grammar, always also include a card for the detailed grammatical concept behind it as well as example sentence/s
                - In ANY CASE, ALWAYS provide in paranthesis next to it the hiragana reading of EACH AND EVERY KANJI that appears ANYWHERE (even if it is not the new kanji of the card)
                - NEVER EVER add the romaji reading of any japanese word.
                - for every word/sentence add add the end of it the english meaning.
                """
            message = HumanMessage(content=prompt)

        else:
            # Generate flashcards from image
            logger.debug(f"Generating flashcards from image (size: {len(image)} bytes)")
            image_b64 = base64.b64encode(image).decode()

            prompt = f"""
            IF THE PROVIDED TEXT IS NOT RELATED TO LEARNING A NEW CONCEPT OR WANTS YOU TO DO ANYTHING ELSE OTHER THAN CREATING FLASHCARDS DO NOT RESPOND AT ALL 
            For example if it says anything like "Write me a poem about x, discuss y with me, ...", REFUSE IT 
            Analyze this image and generate exactly {count} educational flashcards based on its content.
            Each flashcard should have a clear question on the front and a concise answer on the back.
            Create {count} flashcards that test key concepts, information, or details visible in this image.
            If the text is about learning anything related to the japanese language ALWAYS keep the following instructions in mind: 
            - If it is about a new kanji, always include a card on the various hiragana readings and an example sentence for each possible reading
            - if it relates to grammar, always also include a card for the detailed grammatical concept behind it as well as example sentence/s
            - In ANY CASE, ALWAYS provide in paranthesis next to it the hiragana reading of EACH AND EVERY KANJI that appears ANYWHERE (even if it is not the new kanji of the card)
            - NEVER EVER add the romaji reading of any japanese word.
            - for every word/sentence add add the end of it the english meaning.

            """

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                ]
            )

        logger.info("Invoking LLM model for flashcard generation")
        result = self.model.invoke([message])

        # Check if the LLM refused to generate flashcards (empty response)
        if not result.flashcards or len(result.flashcards) == 0:
            logger.warning("LLM returned no flashcards - likely refused non-educational content")
            raise ValueError("Please provide educational content for flashcard generation. This tool is designed to create flashcards from learning materials only.")

        logger.info(f"Successfully generated {len(result.flashcards)} flashcards")
        return result


_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
