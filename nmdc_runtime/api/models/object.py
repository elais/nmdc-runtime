import datetime
import http
from enum import Enum
from typing import Optional, List, Dict, Union

from pydantic import (
    BaseModel,
    Json,
    AnyUrl,
    constr,
    conint,
    HttpUrl,
    root_validator,
)


class AccessMethodType(str, Enum):
    s3 = "s3"
    gs = "gs"
    ftp = "ftp"
    gsiftp = "gsiftp"
    globus = "globus"
    htsget = "htsget"
    https = "https"
    file = "file"


class AccessURL(BaseModel):
    headers: Optional[List[Json[Dict[str, str]]]]
    url: AnyUrl


class AccessMethod(BaseModel):
    access_id: Optional[str]
    access_url: Optional[AccessURL]
    region: Optional[str]
    type: AccessMethodType

    @root_validator
    def at_least_one_of_access_id_and_url(cls, values):
        access_id, access_url = values.get("access_id"), values.get("access_url")
        if access_id is None and access_url is None:
            raise ValueError(
                "At least one of access_url and access_is must be provided."
            )
        return values


ChecksumType = (
    str  # Cannot be an Enum because "sha-256" (contains a dash) is a valid value.
)


class Checksum(BaseModel):
    checksum: str
    type: ChecksumType


DrsId = constr(regex=r"^[A-Za-z0-9.-_~]+$")
PortableFilename = constr(regex=r"^[A-Za-z0-9.-_]+$")


class ContentsObject(BaseModel):
    contents: Optional[List["ContentsObject"]]
    drs_uri: Optional[List[AnyUrl]]
    id: Optional[DrsId]
    name: PortableFilename


ContentsObject.update_forward_refs()

Mimetype = constr(regex=r"^\w+/[-+.\w]+$")
SizeInBytes = conint(strict=True, ge=0)


class DrsObject(BaseModel):
    access_methods: Optional[List[AccessMethod]]
    aliases: Optional[List[str]]
    checksums: List[Checksum]
    contents: Optional[List[ContentsObject]]
    created_time: datetime.datetime
    description: Optional[str]
    id: DrsId
    mime_type: Optional[Mimetype]
    name: Optional[PortableFilename]
    self_uri: AnyUrl
    size: SizeInBytes
    updated_time: Optional[datetime.datetime]
    version: Optional[str]

    @root_validator()
    def no_contents_means_single_blob(cls, values):
        contents, access_methods = values.get("contents"), values.get("access_methods")
        if contents is None and access_methods is None:
            raise ValueError(
                "no contents means single blob, which requires access_methods"
            )
        return values


class Error(BaseModel):
    msg: Optional[str]
    status_code: http.HTTPStatus


class DrsObjectBase(BaseModel):
    aliases: Optional[List[str]]
    description: Optional[str]
    mime_type: Optional[Mimetype] = "application/json"
    name: Optional[PortableFilename]


class DrsObjectBlobIn(DrsObjectBase):
    pass


class DrsObjectBundleIn(DrsObjectBase):
    contents: List[ContentsObject]


Seconds = conint(strict=True, gt=0)


class DrsObjectPresignedUrlPut(BaseModel):
    url: HttpUrl
    expires_in: Seconds = 300


class DrsObjectOutBase(DrsObjectBase):
    checksums: List[Checksum]
    created_time: datetime.datetime
    id: DrsId
    self_uri: AnyUrl
    size: SizeInBytes
    updated_time: Optional[datetime.datetime]
    version: Optional[str]


class DrsObjectBlobOut(DrsObjectOutBase):
    access_methods: List[AccessMethod]


class DrsObjectBundleOut(DrsObjectOutBase):
    access_methods: Optional[List[AccessMethod]]
    contents: List[ContentsObject]