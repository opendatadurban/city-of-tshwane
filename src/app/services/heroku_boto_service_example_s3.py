import logging
import os
import boto3
from botocore.exceptions import ClientError
from os import getenv


class S3Service:
    __instance = None

    def __new__(cls):
        """
        Singleton pattern to ensure only one instance of the class is created
        and credentials are loaded once (to save time)

        No credentials are passed into the client on ECS, as the task role is used

        Credential loading order:
        https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#cli-configure-quickstart-precedence
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials

        Typing is still not supported for boto3
        https://github.com/boto/boto3/issues/1055#issuecomment-1380848223
        """
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            __service_name = "s3"
            cls.__instance.cache_timeout_secs = 60 * 30
            __cloud_access_key = getenv("AWS_CLOUD_ACCESS_KEY")
            __cloud_secret_key = getenv("AWS_CLOUD_SECRET_KEY")
            __region = getenv("AWS_REGION")
            cls.__instance.session = boto3.Session(
                aws_access_key_id=__cloud_access_key,
                aws_secret_access_key=__cloud_secret_key,
                region_name=__region,
            )

            cls.__instance.s3_client = cls.__instance.session.client(
                service_name=__service_name,
            )
        return cls.__instance

    def create_bucket(self, bucket_name: str, region: str) -> bool:
        """Create an S3 bucket in a specified region

        If a region is not specified, the bucket is created in the S3 default
        region (us-east-1).

        :param bucket_name: Bucket to create
        :param region: String region to create bucket in, e.g., 'us-west-2'
        :return: True if bucket created, else False
        """

        # Create bucket
        try:
            location = {"LocationConstraint": region}
            self.s3_client.create_bucket(
                Bucket=bucket_name, CreateBucketConfiguration=location
            )
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def list_bucket_names(self) -> list[str]:
        bucket_name_list: list[str] = list()
        response = self.s3_client.list_buckets()
        for bucket in response["Buckets"]:
            bucket_name_list.append(bucket["Name"])
        return bucket_name_list

    def upload_file(
        self, file_name: str, bucket: str, object_name: str | None = None
    ) -> bool:
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        # Upload the file
        try:
            response = self.s3_client.upload_file(
                file_name, bucket, object_name
            )
        except ClientError as e:
            logging.error(e)
            return False
        return True
