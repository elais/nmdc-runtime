import json
import os
import subprocess
import tempfile

from dagster import solid, List, String
from terminusdb_client.woqlquery import WOQLQuery as WQ


@solid
def hello(context):
    """
    A solid definition. This example solid outputs a single string.

    For more hints about writing Dagster solids, see our documentation overview on Solids:
    https://docs.dagster.io/overview/solids-pipelines/solids
    """
    out = "Hello, NMDC!"
    context.log.info(out)
    return out


@solid
def log_env(context):
    env = subprocess.check_output("printenv", shell=True).decode()
    out = [line for line in env.splitlines() if line.startswith("DAGSTER_")]
    context.log.info("\n".join(out))


@solid(required_resource_keys={"terminus"})
def list_databases(context) -> List[String]:
    client = context.resources.terminus.client
    list_ = client.list_databases()
    context.log.info(f"databases: {list_}")
    return list_


@solid(required_resource_keys={"mongo"})
def mongo_stats(context) -> List[str]:
    db = context.resources.mongo.db
    collection_names = db.list_collection_names()
    context.log.info(str(collection_names))
    return collection_names


@solid(required_resource_keys={"terminus"})
def update_schema(context):
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            context.log.info("shallow-cloning nmdc-schema repo")
            subprocess.check_output(
                "git clone https://github.com/microbiomedata/nmdc-schema.git"
                f" --branch main --single-branch {tmpdirname}/nmdc-schema",
                shell=True,
            )
            context.log.info("generating TerminusDB JSON-LD from NMDC LinkML")
            subprocess.check_output(
                f"gen-terminusdb {tmpdirname}/nmdc-schema/src/schema/nmdc.yaml"
                f" > {tmpdirname}/nmdc.terminus.json",
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            if e.stdout:
                context.log.debug(e.stdout.decode())
            if e.stderr:
                context.log.error(e.stderr.decode())
            context.log.debug(str(e.returncode))
            raise e

        with open(f"{tmpdirname}/nmdc.terminus.json") as f:
            woql_dict = json.load(f)

    context.log.info("Updating terminus schema via WOQLQuery")
    rv = WQ(query=woql_dict).execute(
        context.resources.terminus.client, "update schema via WOQL"
    )
    context.log.info(str(rv))
    return rv