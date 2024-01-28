from os import path
from glob import glob
from minio import Minio
from reshuffle.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME


class MinioUploader:
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

    def upload_folder(self, folder: str, alias: str = None) -> None:
        if not alias:
            alias = folder.split("\\")[-1]
        for f in glob(folder + "/**"):
            if not path.isfile(f):
                self.upload_folder(f, path.join(alias, f.split("\\")[-1]))
            else:
                self.client.fput_object(
                    bucket_name=self.bucket_name,
                    object_name=path.join(alias, f.split("\\")[-1]).replace("\\", "/"),
                    file_path=f
                )

    def upload_file(self, file: str, alias: str = None) -> None:
        if not alias:
            alias = file.split("\\")[-1]
        self.client.fput_object(bucket_name=self.bucket_name, object_name=alias, file_path=file)


if __name__ == "__main__":
    pass
