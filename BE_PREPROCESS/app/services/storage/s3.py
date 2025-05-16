import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional, Union, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from pydantic import BaseModel

from config.base_config import APP_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)


class S3Input(BaseModel):
    """
    Data model for S3 operations.

    Attributes:
        bucket_name (str): Name of the S3 bucket.
        object_name (str): Key of the S3 object.
        file_path (Optional[str]): Local file path for upload or download.
    """

    bucket_name: str
    object_name: str
    file_path: Optional[str] = None


class AsyncS3Client:
    """
    Asynchronous AWS S3 Client that supports both high-level file transfers and low-level object operations.

    This client provides methods for:
      - Listing buckets.
      - Listing objects within a bucket (with optional directory prefix).
      - Downloading a file.
      - Uploading a file.
      - Uploading an object using put_object.
      - Getting an object.
      - Deleting an object.
    """

    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str) -> None:
        """
        Initialize the S3 client using boto3 and set up the executor.
        """
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.loop = asyncio.get_event_loop()

    async def list_buckets(self) -> List[Any]:
        """
        List all S3 buckets asynchronously.
        """
        try:
            response = await self.loop.run_in_executor(self.executor, self.s3_client.list_buckets)
            return cast(List[Any], response.get("Buckets", []))
        except (BotoCoreError, NoCredentialsError) as e:
            logger.error(f"Failed to list buckets: {e}")
            raise Exception(f"Failed to list buckets: {e}") from e

    async def list_objects(self, bucket_name: str, directory: Optional[str] = None) -> List[Any]:
        """
        List objects in the specified S3 bucket asynchronously,
        optionally filtered by a directory prefix.
        """
        try:
            response = await self.loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory if directory else ""),
            )
            return cast(List[Any], response.get("Contents", []))
        except ClientError as e:
            logger.error(f"Failed to list objects in {bucket_name}: {e}")
            raise Exception(f"Failed to list objects in {bucket_name}: {e}") from e

    async def download_file(self, input_data: S3Input) -> None:
        """
        Download a file from S3 asynchronously.
        """
        if not input_data.file_path:
            raise ValueError("file_path required for downloading a file")
        try:
            await self.loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.download_file(
                    input_data.bucket_name, input_data.object_name, input_data.file_path
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to download file {input_data.object_name}: {e}")
            raise Exception(f"Failed to download file {input_data.object_name}: {e}") from e

    async def upload_file(self, input_data: S3Input) -> None:
        """
        Upload a file to S3 asynchronously.
        """
        if not input_data.file_path:
            raise ValueError("file_path required for uploading a file")
        try:
            await self.loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.upload_file(
                    input_data.file_path, input_data.bucket_name, input_data.object_name
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to upload file {input_data.object_name}: {e}")
            raise Exception(f"Failed to upload file {input_data.object_name}: {e}") from e

    async def put_object(self, input_data: S3Input, extra_args: Optional[dict] = None) -> dict:
        """
        Upload an object to S3 asynchronously using the low-level put_object method.
        Reads the file as binary and uploads it.
        """
        if not input_data.file_path:
            raise ValueError("file_path required for put_object")
        try:

            def blocking_put():
                file_path: str = cast(str, input_data.file_path)
                with open(file_path, "rb") as file_data:
                    return self.s3_client.put_object(
                        Bucket=input_data.bucket_name, Key=input_data.object_name, Body=file_data, **(extra_args or {})
                    )

            response = await self.loop.run_in_executor(self.executor, blocking_put)
            return cast(dict, response)
        except (ClientError, FileNotFoundError) as e:
            logger.error(f"Failed to put object {input_data.object_name}: {e}")
            raise Exception(f"Failed to put object {input_data.object_name}: {e}") from e

    async def get_object(self, input_data: S3Input) -> Union[dict, None]:
        """
        Retrieve an object from S3 asynchronously using the low-level get_object method.
        If file_path is provided, writes the content to file asynchronously;
        otherwise, returns the response dictionary.
        """
        try:

            def blocking_get():
                return self.s3_client.get_object(
                    Bucket=input_data.bucket_name,
                    Key=input_data.object_name,
                )

            response = await self.loop.run_in_executor(self.executor, blocking_get)
            if input_data.file_path:

                def write_file():
                    file_path: str = cast(str, input_data.file_path)
                    with open(file_path, "wb") as f:
                        f.write(response["Body"].read())

                await self.loop.run_in_executor(self.executor, write_file)
                return None
            else:
                return cast(dict, response)
        except ClientError as e:
            logger.error(f"Failed to get object {input_data.object_name}: {e}")
            raise Exception(f"Failed to get object {input_data.object_name}: {e}") from e

    async def delete_object(self, input_data: S3Input) -> None:
        """
        Delete an object from S3 asynchronously.
        """
        try:
            await self.loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.delete_object(Bucket=input_data.bucket_name, Key=input_data.object_name),
            )
            logger.info(f"Deleted object {input_data.object_name} from bucket {input_data.bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to delete object {input_data.object_name}: {e}")
            raise Exception(f"Failed to delete object {input_data.object_name}: {e}") from e

    async def head_object(self, input_data: S3Input) -> dict:
        """
        Retrieve the metadata and other header information of an object from S3 asynchronously
        using the head_object method.
        """
        try:

            def blocking_head():
                return self.s3_client.head_object(Bucket=input_data.bucket_name, Key=input_data.object_name)

            response = await self.loop.run_in_executor(self.executor, blocking_head)
            return cast(dict, response)
        except ClientError as e:
            logger.error(f"Failed to get head_object for {input_data.object_name}: {e}")
            raise Exception(f"Failed to get head_object for {input_data.object_name}: {e}") from e


async def get_s3_client() -> AsyncS3Client:
    return AsyncS3Client(
        aws_access_key_id=cast(str, APP_CONFIG.s3config.access_key_id.get_secret_value()),
        aws_secret_access_key=cast(str, APP_CONFIG.s3config.secret_access_key.get_secret_value()),
        region_name=cast(str, APP_CONFIG.s3config.region_name),
    )
