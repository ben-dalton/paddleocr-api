import logging
from typing import Optional
from paddleocr import PaddleOCR
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class OCRService:
    """PaddleOCR service wrapper optimized for Google Cloud Run"""

    def __init__(self):
        self.ocr: Optional[PaddleOCR] = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """Initialize PaddleOCR with optimal settings for Cloud Run"""
        try:
            logger.info("Initializing PaddleOCR...")
            self.ocr = PaddleOCR(
                use_angle_cls=True,      # Handle rotated text
                lang='en',                # Default language
                use_gpu=False,            # Cloud Run uses CPU
                enable_mkldnn=True,       # Performance boost in containers
                cpu_threads=1,            # Single thread for stability
                show_log=False            # Reduce log noise
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def is_loaded(self) -> bool:
        """Check if PaddleOCR is loaded"""
        return self.ocr is not None

    def process_image(self, image_bytes: bytes) -> list:
        """
        Process image bytes and extract text with OCR

        Args:
            image_bytes: Raw image bytes

        Returns:
            List of OCR results, each containing [box, (text, confidence)]
        """
        if not self.is_loaded():
            raise RuntimeError("PaddleOCR is not initialized")

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary (handles PNG with transparency, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to numpy array for PaddleOCR
            image_array = np.array(image)

            # Perform OCR
            logger.info(f"Processing image of size: {image.size}")
            result = self.ocr.ocr(image_array, cls=True)

            # PaddleOCR returns None if no text is detected
            if result is None or len(result) == 0:
                logger.info("No text detected in image")
                return []

            # Extract first page results (result is a list of pages)
            if isinstance(result, list) and len(result) > 0:
                page_result = result[0]
                if page_result is None:
                    return []
                return page_result

            return []

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise


# Global instance
ocr_service = OCRService()
