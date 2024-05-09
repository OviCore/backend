from flask import Flask, request
from fastapi import APIRouter
from werkzeug.utils import secure_filename
import boto3
import io

app = Flask(__name__)
s3 = boto3.client('s3')
router = APIRouter()

def upload_image_to_s3(file):
    if file:
        filename = secure_filename(file.filename)
        # Create an in-memory byte stream
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        # Reset stream position
        in_memory_file.seek(0)
        # Upload file to S3
        s3.upload_fileobj(in_memory_file, 'your-bucket-name', filename)
        return 'File uploaded successfully to S3', 200
    else:
        return 'No selected file', 400

@router.get("/status/")
async def health():
    # Check if aws is working
    s3.list_buckets()
    return {"status": "ok"}

@router.post("/upload_image/")
async def upload_image():
    file = request.files['file']
    return upload_image_to_s3(file)

def add_aws(app):
    app.include_router(router, prefix="/aws", tags=["aws"])