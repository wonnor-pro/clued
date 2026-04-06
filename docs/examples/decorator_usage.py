"""Deeply nested decorator example for clued."""

from clued import clue, clue_on_error


@clue_on_error("fetching record type={record_type} id={record_id}")
def db_fetch(record_type: str, record_id: int) -> dict[str, int]:
    if record_id <= 0:
        raise ValueError(f"no record: {record_type}/{record_id}")
    return {"id": record_id}


@clue_on_error("resolving")
def resolve_dep(dep: str, user_id: int) -> dict[str, int]:
    return db_fetch(record_type=dep, record_id=user_id)


@clue_on_error("pipeline")
def run_step(step: str, job_id: str, user_id: int) -> dict[str, int]:
    with clue("loading config", step=step):
        db_fetch(record_type="config", record_id=int(job_id.split("-")[1]))
    return resolve_dep(dep=step, user_id=user_id)


@clue_on_error("execute job={job_id} tenant={tenant}")
def execute_job(job_id: str, tenant: str) -> None:
    run_step(step="validate", job_id=job_id, user_id=-1)  # -1 triggers deep failure


if __name__ == "__main__":
    execute_job(job_id="job-42", tenant="acme")
