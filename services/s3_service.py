import boto3
import uuid
from core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

async def upload_image_to_s3(file):
    try:
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        s3_client.upload_fileobj(
            file.file,
            settings.AWS_S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )

        file_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
        return file_url
    except Exception as e:
        print(f"S3 업로드 실패: {e}")
        return None
    

async def delete_image_from_s3(image_url: str):
    try:
        filename = image_url.split("/")[-1]

        # ✅ S3에서 파일 삭제
        s3_client.delete_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=filename
        )
        return True
    except Exception as e:
        print(f"S3 삭제 실패: {e}")
        return False
