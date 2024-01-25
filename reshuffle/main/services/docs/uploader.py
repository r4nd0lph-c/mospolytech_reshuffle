from minio import Minio
from minio.error import S3Error
from reshuffle.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME


class FileUploader:
    """
    ...
    """

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket_name = MINIO_BUCKET_NAME
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload(self, object_name:str, file_path: str) -> None:
        try:
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path
            )
        except S3Error as e:
            print(e)


if __name__ == "__main__":
    pass
