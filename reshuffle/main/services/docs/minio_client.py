from os import path
from glob import glob
from minio import Minio
from reshuffle.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME


class MinioClient:
    """
    ...
    """

    def __init__(self) -> None:
        self.__client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        self.__bucket_name = MINIO_BUCKET_NAME
        if not self.__client.bucket_exists(self.__bucket_name):
            self.__client.make_bucket(self.__bucket_name)

    def upload_folder(self, folder: str, alias: str = None) -> None:
        if not alias:
            alias = folder.split("\\")[-1]
        for f in glob(folder + "/**"):
            if not path.isfile(f):
                self.upload_folder(f, path.join(alias, f.split("\\")[-1]))
            else:
                self.__client.fput_object(
                    bucket_name=self.__bucket_name,
                    object_name=path.join(alias, f.split("\\")[-1]).replace("\\", "/"),
                    file_path=f
                )

    def upload_file(self, file: str, alias: str = None) -> None:
        if not alias:
            alias = file.split("\\")[-1]
        self.__client.fput_object(bucket_name=self.__bucket_name, object_name=alias, file_path=file)

    def delete_object(self, alias: str) -> None:
        for o in self.__client.list_objects(bucket_name=self.__bucket_name, prefix=alias, recursive=True):
            self.__client.remove_object(bucket_name=self.__bucket_name, object_name=o.object_name)


if __name__ == "__main__":
    pass
