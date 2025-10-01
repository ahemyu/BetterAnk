"""
LLM service for generating flashcards using Gemini API via LangChain.
"""
import os
import base64
import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

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
                    model="gemini-2.5-flash",
                    temperature=0.7,
                    google_api_key=api_key,
                    timeout=30.0,
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
                Generate exactly {count} educational flashcards based on the following text.
                Each flashcard should have a clear question on the front and a concise answer on the back.
                Text: {text}
                Create {count} flashcards that test key concepts, definitions, or important information from this text.
                """
            message = HumanMessage(content=prompt)

        else:
            # Generate flashcards from image
            logger.debug(f"Generating flashcards from image (size: {len(image)} bytes)")
            image_b64 = base64.b64encode(image).decode()

            prompt = f"""
            Analyze this image and generate exactly {count} educational flashcards based on its content.
            Each flashcard should have a clear question on the front and a concise answer on the back.
            Create {count} flashcards that test key concepts, information, or details visible in this image.
            """

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                ]
            )

        logger.info("Invoking LLM model for flashcard generation")
        result = self.model.invoke([message])
        logger.info(f"Successfully generated {len(result.flashcards)} flashcards")
        return result


_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
