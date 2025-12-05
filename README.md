# PaddleOCR API

A containerized OCR API wrapper for PaddleOCR, optimized for deployment on Google Cloud Run.

## Features

- FastAPI-based REST API
- PaddleOCR for accurate text detection and recognition
- Supports multiple image formats (JPG, PNG, BMP, TIFF, WebP)
- Handles rotated text
- Returns structured JSON with text, confidence scores, and bounding boxes
- Optimized for Google Cloud Run (free tier)
- Docker containerized for easy deployment

## Project Structure

```
paddleocr-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── ocr_service.py       # PaddleOCR wrapper logic
│   └── models.py            # Pydantic models
├── tests/
│   └── test_api.py
├── Dockerfile               # Optimized for Cloud Run
├── requirements.txt
├── .dockerignore
├── .gcloudignore
└── README.md
```

## Prerequisites

### For Local Development
- Python 3.11+
- pip

### For Cloud Deployment
- Google Cloud account (free tier)
- gcloud CLI installed: https://cloud.google.com/sdk/docs/install
- Docker (optional, for local testing)

## Installation

### Local Setup

1. Clone or navigate to the project directory:
```bash
cd paddleocr-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn app.main:app --reload --port 8080
```

5. Access the API:
- API: http://localhost:8080
- Interactive docs: http://localhost:8080/docs
- Health check: http://localhost:8080/health

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the service is running and PaddleOCR is loaded.

**Response:**
```json
{
  "status": "healthy",
  "paddleocr_loaded": true
}
```

### 2. OCR Processing
**POST** `/ocr`

Upload an image file for OCR processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

**Example with curl:**
```bash
curl -X POST http://localhost:8080/ocr \
  -F "file=@path/to/image.jpg"
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "text": "Detected text here",
      "confidence": 0.95,
      "box": [
        [10.0, 20.0],
        [100.0, 20.0],
        [100.0, 50.0],
        [10.0, 50.0]
      ]
    }
  ],
  "processing_time_ms": 1234.56
}
```

**Response Fields:**
- `success`: Boolean indicating if OCR was successful
- `results`: Array of detected text regions
  - `text`: Extracted text
  - `confidence`: Confidence score (0-1)
  - `box`: Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
- `processing_time_ms`: Processing time in milliseconds

### 3. Root Endpoint
**GET** `/`

Returns API information and available endpoints.

## Docker

### Build Image
```bash
docker build -t paddleocr-api .
```

### Run Container Locally
```bash
docker run -p 8080:8080 paddleocr-api
```

### Test
```bash
curl http://localhost:8080/health
```

## Google Cloud Run Deployment

### Prerequisites

1. Create a Google Cloud account (free tier)
2. Install gcloud CLI
3. Login and set project:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

4. Enable required APIs:
```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Deploy (Option A: Direct from Source)

This is the simplest method - Cloud Build will build and deploy automatically:

```bash
gcloud run deploy paddleocr-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 1
```

### Deploy (Option B: Pre-built Docker Image)

1. Build and tag the image:
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/paddleocr-api .
```

2. Push to Google Container Registry:
```bash
docker push gcr.io/YOUR_PROJECT_ID/paddleocr-api
```

3. Deploy to Cloud Run:
```bash
gcloud run deploy paddleocr-api \
  --image gcr.io/YOUR_PROJECT_ID/paddleocr-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 1
```

### Configuration Options

- `--memory`: Memory allocation (2Gi recommended for PaddleOCR)
- `--cpu`: CPU allocation (1 vCPU sufficient for light usage)
- `--timeout`: Request timeout in seconds (300 = 5 minutes)
- `--max-instances`: Maximum concurrent instances (1 for free tier)
- `--allow-unauthenticated`: Make API publicly accessible
- `--region`: Deployment region (choose closest to your users)

### After Deployment

Cloud Run will provide a URL like:
```
https://paddleocr-api-[hash]-uc.a.run.app
```

Test it:
```bash
curl https://YOUR_CLOUD_RUN_URL/health
```

### View Logs

```bash
gcloud run logs read paddleocr-api --limit 50
```

### Monitor Usage

```bash
gcloud run services describe paddleocr-api --region us-central1
```

Or visit: Google Cloud Console → Cloud Run → paddleocr-api → Metrics

## Cost Estimation

### Google Cloud Run Free Tier (Monthly)
- 2M requests
- 360,000 GB-seconds (memory)
- 180,000 vCPU-seconds

### Expected Cost for Light Usage
For ~100 requests/month (3-4 per day):
- Requests: 100 (0.005% of free tier)
- Memory: ~1,000 GB-seconds (0.28% of free tier)
- CPU: ~500 vCPU-seconds (0.28% of free tier)

**Result: $0/month** (well within free tier)

### Cold Starts
- First request after idle: ~2-5 seconds (loading PaddleOCR)
- Subsequent requests: Fast (PaddleOCR stays loaded)
- For personal testing, cold starts are acceptable
- To eliminate cold starts: Set `--min-instances 1` (costs ~$5/month)

## Security

### Input Validation
- Maximum file size: 10MB
- Allowed formats: JPG, PNG, BMP, TIFF, WebP
- File type validation

### Container Security
- Non-root user (appuser)
- Minimal base image (python:3.11-slim)
- No secrets in image

### Network Security
- HTTPS by default (Cloud Run provides SSL)
- CORS enabled (configure in `app/main.py` for production)

## Limitations

- CPU-only inference (no GPU on Cloud Run)
- English language default (can be extended to other languages)
- Single image processing (no batch endpoint yet)
- 10MB max file size

## Extending

### Add Language Support

Edit `app/ocr_service.py`:
```python
self.ocr = PaddleOCR(
    lang='ch',  # Chinese
    # Other supported: 'fr', 'german', 'korean', 'japan', etc.
    ...
)
```

### Add Batch Processing

Create a new endpoint in `app/main.py` that accepts multiple files.

### Add PDF Support

Install `pdf2image` and convert PDF pages to images before OCR.

## Troubleshooting

### Local Development

**Issue**: PaddleOCR fails to initialize
- Solution: Ensure all system dependencies are installed
- On macOS: `brew install opencv`
- On Linux: Install packages from Dockerfile

**Issue**: Import errors
- Solution: Ensure virtual environment is activated
- Solution: Reinstall dependencies: `pip install -r requirements.txt`

### Cloud Run

**Issue**: Deployment fails
- Check logs: `gcloud run logs read paddleocr-api --limit 50`
- Ensure APIs are enabled
- Verify billing is enabled (free tier still requires billing account)

**Issue**: Out of memory errors
- Increase memory: `--memory 4Gi`
- Reduce concurrency: `--concurrency 1`

**Issue**: Timeout errors
- Increase timeout: `--timeout 600` (max: 3600 seconds)

## Example Usage with Python

```python
import requests

url = "https://YOUR_CLOUD_RUN_URL/ocr"

with open("image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

data = response.json()
for result in data["results"]:
    print(f"Text: {result['text']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Box: {result['box']}")
    print()
```

## License

This project is a wrapper for PaddleOCR. Please refer to PaddleOCR's license for usage terms.

## Support

For issues or questions:
- PaddleOCR Documentation: https://github.com/PaddlePaddle/PaddleOCR
- Google Cloud Run Documentation: https://cloud.google.com/run/docs
- FastAPI Documentation: https://fastapi.tiangolo.com

## What's Next?

After deployment, you can:
1. Add authentication (API keys, OAuth)
2. Implement rate limiting
3. Add result caching with Cloud Storage
4. Support multiple languages
5. Add batch processing
6. Integrate with Cloud Vision API for comparison
7. Add monitoring and alerting

Enjoy your free OCR API!
