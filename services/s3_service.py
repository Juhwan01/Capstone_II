from typing import List, Optional
import boto3
import uuid
import sys
import os
from fastapi import UploadFile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

async def upload_images_to_s3(files: List[UploadFile]) -> Optional[List[str]]:
   

    image_urls = []
    try:
        for file in files:
            if not hasattr(file, 'file'):
                continue  # 잘못된 파일은 건너뛰기
                
            # 파일 포인터를 시작 위치로 되돌림
            await file.seek(0)
            
            # 유니크한 파일명 생성
            file_extension = file.filename.split(".")[-1].lower()
            unique_filename = f"{uuid.uuid4()}.{file_extension}"

            try:
                s3_client.upload_fileobj(
                    file.file,
                    settings.AWS_S3_BUCKET_NAME,
                    unique_filename,
                    ExtraArgs={"ContentType": file.content_type}
                )

                file_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
                image_urls.append(file_url)
                
            except Exception as e:
                print(f"개별 파일 업로드 실패: {e}")
                continue

        return image_urls if image_urls else None

    except Exception as e:
        print(f"🚨 S3 업로드 실패: {e}")
        return None

async def delete_images_from_s3(image_urls: list):
    """
    S3에서 여러 개의 이미지 파일 삭제
    """
    try:
        for image_url in image_urls:
            filename = image_url.split("/")[-1]
            s3_client.delete_object(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=filename
            )
        return True
    except Exception as e:
        print(f"S3 삭제 실패: {e}")
        return False