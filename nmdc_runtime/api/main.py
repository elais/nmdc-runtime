from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from nmdc_runtime.api.endpoints import (
    users,
    operations,
    sites,
    jobs,
    objects,
    object_types,
    capabilities,
    triggers,
    workflows,
    queries,
)

api_router = APIRouter()
api_router.include_router(users.router, tags=["users"])
api_router.include_router(operations.router, tags=["operations"])
api_router.include_router(sites.router, tags=["sites"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(objects.router, tags=["objects"])
api_router.include_router(capabilities.router, tags=["capabilities"])
api_router.include_router(triggers.router, tags=["triggers"])
api_router.include_router(workflows.router, tags=["workflows"])
api_router.include_router(object_types.router, tags=["object types"])
api_router.include_router(queries.router, tags=["queries"])

tags_metadata = [
    {
        "name": "workflows",
        "description": (
            """A workflow is a template for creating jobs.

Workflow jobs are typically created by the system via trigger associations between
workflows and object types. A workflow may also require certain capabilities of sites
in order for those sites to claim workflow jobs.
            """
        ),
    },
    {
        "name": "object types",
        "description": (
            """An object type is an object annotation that is useful for triggering workflows.

A data object may be annotated with one or more types, which in turn can be associated with
workflows through trigger resources.

The data-object type system may be used to trigger workflow jobs on a subset of data objects when a
new version of a workflow is deployed. This could be done by minting a special object type for the
occasion, annotating the subset of data objects with that type, and registering the association of
object type to workflow via a trigger resource.
            """
        ),
    },
    {
        "name": "triggers",
        "description": (
            """A trigger is an association between a workflow and a data object type.
            
When a data object is annotated with a type, perhaps shortly after object registration, the NMDC
Runtime will check, via trigger associations, for potential new jobs to create for any workflows.
            
            """
        ),
    },
    {
        "name": "sites",
        "description": (
            """A site corresponds to a physical place that may participate in job execution.

A site may register data objects and capabilties with NMDC. It may claim jobs to execute, and it may update job operations with execution info.

A site must be able to service requests for any data objects it has registered."""
        ),
    },
    {
        "name": "operations",
        "description": """An operation is a resource for tracking the execution of a job.

When a job is claimed by a site for execution, an operation resource is created.

An operation is akin to a "promise" or "future" in that it should eventually resolve to either a successful result, i.e. an execution resource, or to an error.

An operation is parameterized to return a result type, and a metadata type for storing progress information, that are both particular to the job type.

Operations may be paused, resumed, and/or cancelled.

Operations may expire, i.e. not be stored indefinitely. In this case, it is recommended that execution resources have longer lifetimes / not expire, so that information about successful results of operations are available.
        """,
    },
    {
        "name": "jobs",
        "description": """A job is a resource that isolates workflow configuration from execution.

Rather than directly creating a workflow operation by supplying a workflow ID along with configuration, NMDC creates a job that pairs a workflow with configuration. Then, a site can claim a job ID, allowing the site to execute the intended workflow without additional configuration.

A job can have multiple executions, and a workflow's executions are precisely the executions of all jobs created for that workflow.
        """,
    },
    {
        "name": "objects",
        "description": (
            "A [Data Repository Service (DRS) object](https://ga4gh.github.io/data-repository-service-schemas/preview/release/drs-1.1.0/docs/#_drs_datatypes) represents content necessary"
            " for a workflow job to execute, and/or output from a job execution."
            " An object may be a *blob*, analogous to a file, or a *bundle*, analogous to a folder."
            " Sites register objects, and sites must ensure "
            " that these objects are accessible to the NMDC data broker."
        ),
    },
    {
        "name": "capabilities",
        "description": (
            """A workflow may require an executing site to have particular capabilities.
            
These capabilities go beyond the simple ability to access the data object resources registered with
the runtime system. Sites register their capabilities, and sites are only able to claim workflow
jobs if they are known to have the capabilities required by the workflow.

"""
        ),
    },
    {
        "name": "queries",
        "description": (
            """A query is an operation (find, update, etc.) against the metadata store.

Metadata -- for studies, biosamples, omics processing, etc. -- is used by sites to execute jobs,
as the parameterization of job executions may depend not only on the content of data objects, but
also on objects' associated metadata.

Also, the function of many workflows is to extract or produce new metadata. Such metadata products
should be registered as data objects, and they may also be supplied by sites to the runtime system
as an update query (if the latter is not done, the runtime system will sense the new metadata and
issue an update query).

            """
        ),
    },
]

app = FastAPI(
    title="NMDC Runtime API",
    version="0.1.0",
    description=(
        "This is a draft of the NMDC Runtime API."
        " The resource layout currently covers aspects of workflow execution and automation,"
        " and is intended to facilitate discussion as more of the API is developed."
    ),
    openapi_tags=tags_metadata,
)
app.include_router(api_router)


origins = [
    "http://localhost:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# To build static redoc documentation:
# > cd docs/design && redoc-cli bundle http://0.0.0.0:8000/openapi.json

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
