"""
Usage:
$ export $(grep -v '^#' .env | xargs)
$ nmdcdb-mongodump
"""

import os
import subprocess
import warnings
from datetime import datetime, timezone
from pathlib import Path

import click
import dagster

from nmdc_runtime.site.repository import run_config_frozen__normal_env
from nmdc_runtime.site.resources import get_mongo
from nmdc_runtime.util import nmdc_jsonschema

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


@click.command()
@click.option("--just-schema-collections", is_flag=True, default=False)
def main(just_schema_collections):
    print("starting nmdcdb mongodump...")
    mongo = get_mongo(run_config_frozen__normal_env)
    mdb = mongo.db
    print("connected to database...")

    if just_schema_collections:
        collection_names = set(mdb.list_collection_names()) & set(
            nmdc_jsonschema["$defs"]["Database"]["properties"]
        )
    else:
        collection_names = set(mdb.list_collection_names())

    print("retrieved relevant collection names...")
    print(sorted(collection_names))
    print(f"filtering {len(collection_names)} collections...")
    heavy_collection_names = {
        "functional_annotation_set",
        "genome_feature_set",
        "functional_annotation_set_prev",  # needed for just_schema_collections==False
        "functional_annotation_agg",  # needed for just_schema_collections==False
    }
    collection_names = {c for c in collection_names if c not in heavy_collection_names}
    print(f"filtered collections to {len(collection_names)}:")
    print(sorted(collection_names))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"ensuring ~/nmdcdb-mongodump/{today} directory for exports")
    today_dir = Path("~/nmdcdb-mongodump").expanduser().joinpath(today)
    os.makedirs(str(today_dir), exist_ok=True)

    collections_excluded = set(mdb.list_collection_names()) - collection_names
    collections_excluded_str = " ".join(
        ["--excludeCollection=" + c for c in collections_excluded]
    )

    filename = f'nmdcdb.{"" if just_schema_collections else "less"}lite.archive.gz'
    filepath = today_dir.joinpath(filename)
    cmd = (
        f"mongodump --host \"{os.getenv('MONGO_HOST').replace('mongodb://','')}\" "
        f"-u \"{os.getenv('MONGO_USERNAME')}\" -p \"{os.getenv('MONGO_PASSWORD')}\" "
        f"--authenticationDatabase admin "
        f"-d \"{os.getenv('MONGO_DBNAME')}\" --gzip --archive={filepath} "
        f"{collections_excluded_str}"
    )
    print(cmd.replace(f"-p \"{os.getenv('MONGO_PASSWORD')}\"", ""))
    subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )


if __name__ == "__main__":
    main()
