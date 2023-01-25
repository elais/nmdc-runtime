import json
import os
from functools import lru_cache
from pathlib import Path

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase


def get_nmdc_jsonschema_dict():
    """Get NMDC JSON Schema.

    May replace this with `from nmdc_runtime.util import get_nmdc_jsonschema_dict`
    once the whole codebase uses nmdc-schema~=v7.2.0
    """
    with (Path(__file__).parent / "nmdc.schema.json").open() as f:
        return json.load(f)


@lru_cache
def get_mongo_db() -> MongoDatabase:
    _client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        username=os.getenv("MONGO_USERNAME"),
        password=os.getenv("MONGO_PASSWORD"),
    )
    return _client[os.getenv("MONGO_DBNAME")]


@lru_cache()
def minting_service_id():
    return os.getenv("MINTING_SERVICE_ID")


@lru_cache()
def typecodes():
    rv = []
    schema_dict = get_nmdc_jsonschema_dict()
    for cls_name, defn in schema_dict["$defs"].items():
        match defn.get("properties"):
            case {"id": {"pattern": p}} if p.startswith("^(nmdc):"):
                rv.append(
                    {
                        "id": "nmdc:" + cls_name + "_" + "typecode",
                        "schema_class": "nmdc:" + cls_name,
                        "name": p.split(":", maxsplit=1)[-1].split("-", maxsplit=1)[0],
                    }
                )
            case _:
                pass
    return rv


@lru_cache()
def shoulders():
    return [
        {
            "id": "nmdc:minter_shoulder_11",
            "assigned_to": "nmdc:minter_service_11",
            "name": "11",
        },
    ]


@lru_cache
def services():
    return [{"id": "nmdc:minter_service_11", "name": "central minting service"}]


def requesters():
    """not cached because sites are created dynamically"""
    return [{"id": s["id"]} for s in get_mongo_db().sites.find()]


@lru_cache()
def schema_classes():
    return [{"id": d["schema_class"]} for d in typecodes()]
