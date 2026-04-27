from typing import TypedDict
from services import minio_service

service = minio_service.minio_service

EVENT_OBJECT_CREATED = "s3:ObjectCreated:"
EVENT_OBJECT_REMOVED = "s3:ObjectRemoved:"


class S3Object(TypedDict):
    key: str
    size: int
    eTag: str
    contentType: str
    sequencer: str


class S3Bucket(TypedDict):
    name: str
    arn: str


class S3(TypedDict):
    bucket: S3Bucket
    object: S3Object


class MinioRecord(TypedDict):
    eventName: str
    eventTime: str
    s3: S3


class MinioEvent(TypedDict):
    Records: list[MinioRecord]


def listen_to_minio():
    for event in service.listen_to_bucket():
        minio_event: MinioEvent = event
        for record in minio_event.get("Records", []):
            event_name = record["eventName"]
            key = record["s3"]["object"]["key"]
            if event_name.startswith(EVENT_OBJECT_CREATED):
                print(f"Created: {key}")
            elif event_name.startswith(EVENT_OBJECT_REMOVED):
                print(f"Removed: {key}")
