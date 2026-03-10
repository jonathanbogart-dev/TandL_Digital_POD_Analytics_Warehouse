"""Dataset file management API.

Endpoints
---------
POST   /api/datasets/{name}?mode=replace   Upload a .js file; replace existing data.
POST   /api/datasets/{name}?mode=append    Upload a .js file; append to existing data.
GET    /api/datasets                       List all datasets (registry metadata).
GET    /api/datasets/{name}                Return dataset records as a JSON array.
DELETE /api/datasets/{name}                Remove a dataset from the store.

The .js file format expected on upload
---------------------------------------
Any file that contains a single JavaScript assignment of the form:

    window.IDENTIFIER = [ ... ];

where the value is a valid JSON array of objects.  The ``window.IDENTIFIER``
wrapper is the same convention used by existing dashboard dataset files
(e.g. ``voya_backend_dataset_rebuilt.js``).  The server strips the wrapper,
parses the array as JSON, and persists it.
"""

import re
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, UploadFile
from pydantic import BaseModel

from api.js_parser import parse_js_dataset
from api.storage import delete_dataset, load_dataset, load_registry, save_dataset

router = APIRouter(tags=["datasets"])

_VALID_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class DatasetMeta(BaseModel):
    name: str
    source_filename: str
    row_count: int
    rows_in_upload: int
    created_at: str
    updated_at: str


class UploadResult(BaseModel):
    name: str
    mode: str
    rows_in_upload: int
    total_rows: int


# ---------------------------------------------------------------------------
# Route helpers
# ---------------------------------------------------------------------------

def _require_valid_name(name: str) -> None:
    if not _VALID_NAME.match(name):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid dataset name. Use lowercase letters, digits, and "
                "underscores; must start with a letter; max 64 characters."
            ),
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/datasets", response_model=list[DatasetMeta])
def list_datasets() -> list[DatasetMeta]:
    """Return metadata for all stored datasets, ordered by name."""
    registry = load_registry()
    return sorted(
        [DatasetMeta(**v) for v in registry.values()],
        key=lambda m: m.name,
    )


@router.get("/datasets/{name}")
def get_dataset(name: str) -> list[dict]:
    """Return all records for a dataset as a JSON array."""
    _require_valid_name(name)
    try:
        return load_dataset(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")


@router.post("/datasets/{name}", response_model=UploadResult, status_code=201)
async def upload_dataset(
    name: str,
    file: UploadFile,
    mode: Annotated[Literal["replace", "append"], Query()] = "replace",
) -> UploadResult:
    """Upload a .js dataset file.

    - **replace** (default): overwrites any existing data for this name.
    - **append**: parses new records from the file and adds them to the end of
      the existing dataset.

    The file must contain a ``window.IDENTIFIER = [...]`` assignment whose
    value is a valid JSON array of objects.
    """
    _require_valid_name(name)

    if not file.filename or not file.filename.endswith(".js"):
        raise HTTPException(
            status_code=400,
            detail="Only .js files are accepted. Rename your file if needed.",
        )

    raw = await file.read()
    try:
        content = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not decode file as UTF-8: {exc}"
        )

    try:
        new_records = parse_js_dataset(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not new_records:
        raise HTTPException(
            status_code=422, detail="The uploaded file contains zero records."
        )

    entry = save_dataset(name, new_records, file.filename or f"{name}.js", mode)

    return UploadResult(
        name=name,
        mode=mode,
        rows_in_upload=entry["rows_in_upload"],
        total_rows=entry["row_count"],
    )


@router.delete("/datasets/{name}", status_code=204)
def remove_dataset(name: str) -> None:
    """Delete a dataset and remove it from the registry."""
    _require_valid_name(name)
    try:
        delete_dataset(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")
