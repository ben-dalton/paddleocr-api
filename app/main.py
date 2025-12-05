import time
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import OCRResponse, OCRResult, HealthResponse
from app.ocr_service import ocr_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PaddleOCR API",
    description="OCR API wrapper for PaddleOCR deployed on Google Cloud Run",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service is running and PaddleOCR is loaded
    """
    return HealthResponse(
        status="healthy",
        paddleocr_loaded=ocr_service.is_loaded()
    )


@app.post("/ocr", response_model=OCRResponse)
async def perform_ocr(file: UploadFile = File(...)):
    """
    Perform OCR on uploaded image file

    Args:
        file: Image file (jpg, png, bmp, tiff, webp)

    Returns:
        OCRResponse with detected text, bounding boxes, and confidence scores
    """
    start_time = time.time()

    try:
        # Validate file extension
        file_ext = None
        if file.filename:
            file_ext = '.' + file.filename.lower().split('.')[-1]
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
                )

        # Read file contents
        image_bytes = await file.read()

        # Validate file size
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )

        # Validate file is not empty
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        logger.info(f"Processing file: {file.filename}, size: {len(image_bytes)} bytes")

        # Perform OCR
        ocr_results = ocr_service.process_image(image_bytes)

        # Parse results
        results = []
        for line in ocr_results:
            # PaddleOCR returns: [box, (text, confidence)]
            if len(line) >= 2:
                box = line[0]
                text_info = line[1]

                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text = text_info[0]
                    confidence = float(text_info[1])

                    results.append(OCRResult(
                        text=text,
                        confidence=confidence,
                        box=box
                    ))

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(f"OCR completed: {len(results)} text regions detected in {processing_time_ms:.2f}ms")

        return OCRResponse(
            success=True,
            results=results,
            processing_time_ms=processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "PaddleOCR API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ocr": "/ocr (POST with multipart/form-data)",
            "docs": "/docs"
        }
    }
