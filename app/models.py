from pydantic import BaseModel
from typing import List


class OCRResult(BaseModel):
    """Single text detection result from OCR"""
    text: str
    confidence: float
    box: List[List[float]]


class OCRResponse(BaseModel):
    """Complete API response with all OCR detections"""
    success: bool
    results: List[OCRResult]
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    paddleocr_loaded: bool
