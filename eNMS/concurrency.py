from typing import List, Optional

from eNMS.database import engine
from eNMS.database.functions import fetch, session_scope


def threaded_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[set] = None,
    payload: Optional[dict] = None,
    start_points: Optional[List[int]] = None,
) -> None:
    task = fetch("Task", allow_none=True, creation_time=aps_job_id or "")
    job = fetch("Job", id=job_id)
    if start_points:
        start_points = [fetch("Job", id=id) for id in start_points]
    payload = payload or job.initial_payload
    if targets:
        targets = {fetch("Device", id=device_id) for device_id in targets}
    job.run(targets=targets, payload=payload, task=task, start_points=start_points)


def device_process(args: tuple) -> None:
    engine.dispose()
    with session_scope() as session:
        (
            device_id,
            job_id,
            lock,
            results,
            runtime,
            payload,
            workflow_id,
            parent_timestamp,
        ) = args
        device = fetch("Device", session=session, id=device_id)
        workflow = fetch("Workflow", allow_none=True, session=session, id=workflow_id)
        job = fetch("Job", session=session, id=job_id)
        device_result = job.get_results(
            runtime, payload, device, workflow, parent_timestamp
        )
        with lock:
            results[device.name] = device_result


def device_thread(args: tuple) -> None:
    device = fetch("Device", id=args[0])
    workflow = fetch("Workflow", allow_none=True, id=args[6])
    job = fetch("Job", id=args[1])
    device_result = job.get_results(args[4], args[5], device, workflow, args[7])
    with args[2]:
        args[3][device.name] = device_result
