import asyncio
from typing import TypedDict
from database_handle.models.audios import StatusEnum
from database_handle.queries.audios import AudioQueries
from services import minio_service
from database_handle.database import get_sessionmanager

service = minio_service.minio_service

EVENT_OBJECT_CREATED = "s3:ObjectCreated:"


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


async def _handle_record(uuid: str) -> None:
    async with get_sessionmanager().session() as session:
        await AudioQueries(session).update_audio(
            audio_id=uuid, status=StatusEnum.available
        )


def listen_to_minio(loop: asyncio.AbstractEventLoop) -> None:
    for event in service.listen_to_bucket():
        minio_event: MinioEvent = event
        for record in minio_event.get("Records", []):
            event_name = record["eventName"]
            key = record["s3"]["object"]["key"]
            print(f"{key=}")
            print(f"{event_name=}")
            uuid = record["s3"]["object"]["userMetadata"]["X-Amz-Meta-Uuid"]
            print(uuid)
            if event_name.startswith(EVENT_OBJECT_CREATED):
                future = asyncio.run_coroutine_threadsafe(_handle_record(uuid), loop)
                future.result()
