import sys
import time
from typing import List, OrderedDict

import schedule as sched

from mapswipe_workers.auth import firebaseDB
from mapswipe_workers.definitions import MessageType, logger
from mapswipe_workers.utils.slack_helper import send_slack_message


def get_projects(status: str) -> OrderedDict:
    """Load 'active' projects from Firebase."""
    fb_db = firebaseDB()
    projects = (
        fb_db.reference("v2/projects/").order_by_child("status").equal_to(status).get()
    )
    logger.info(f"got {len(projects)} {status} projects from firebase")
    return projects


def filter_projects_by_name_and_progress(
    projects: OrderedDict, filter_string: str, progress_threshold: int
) -> List[str]:
    """Filter projects by name (lowercase) and progress."""
    selected_project_ids = []
    for project_id in projects.keys():
        name = projects[project_id]["name"]
        progress = projects[project_id]["progress"]
        if filter_string.lower() in name.lower() and progress >= progress_threshold:
            selected_project_ids.append(project_id)

    logger.info(
        f"selected {len(selected_project_ids)} project(s) which contain(s) "
        f"'{filter_string}' in the project name and progress >= {progress_threshold}%."
    )
    return selected_project_ids


def set_status_in_firebase(project_id: str, project_name: str, new_status: str) -> None:
    """Change status of a project in Firebase."""
    # change status in firebase
    fb_db = firebaseDB()
    fb_db.reference(f"v2/projects/{project_id}/status").set(new_status)
    logger.info(f"set project status to '{new_status}' for project {project_id}")

    # send slack message
    if new_status == "finished":
        send_slack_message(
            MessageType.PROJECT_STATUS_FINISHED, project_name, project_id
        )
    elif new_status == "active":
        send_slack_message(MessageType.PROJECT_STATUS_ACTIVE, project_name, project_id)


def run_update_project_status(filter_string: str) -> None:
    """Run the workflow to update project status for all filtered projects."""
    logger.info("### Start update project status workflow ###")
    active_projects = get_projects(status="active")
    finished_projects = filter_projects_by_name_and_progress(
        active_projects,
        filter_string,
        progress_threshold=100,
    )

    inactive_projects = get_projects(status="inactive")
    # We sort projects by their attribute "projectNumber" to ensure that
    # always the lowest one will be set to "status=active" next.
    inactive_projects = OrderedDict(
        sorted(inactive_projects.items(), key=lambda x: int(x[1]["projectNumber"]))
    )

    new_active_projects = filter_projects_by_name_and_progress(
        inactive_projects,
        filter_string,
        progress_threshold=0,
    )[0 : len(finished_projects)]

    # Here we check that there is at least one inactive project
    # which can be activated in the app.
    # We do this to avoid that there is no project left in the app.
    if len(new_active_projects) > 0:
        for project_id in finished_projects:
            project_name = active_projects[project_id]["name"]
            set_status_in_firebase(project_id, project_name, new_status="finished")

        for project_id in new_active_projects:
            project_name = inactive_projects[project_id]["name"]
            set_status_in_firebase(project_id, project_name, new_status="active")
    logger.info("### Finished update project status workflow ###")


if __name__ == "__main__":
    """Use this command to run in docker container.
    docker-compose run -d mapswipe_workers_creation python3 python_scripts/update_project_status.py "test" 30  # noqa

    You need to use two arguments for the script
    - filter string, e.g. "test"
    - time interval in minutes, e.g. 30

    Make sure that you don't run this script too frequently as it pulls data from firebase and
    this will have implications on costs. Running this script once every 15-30 minutes should be totally fine.
    This means that there can be a "delay" in setting a project to finished about roughly the same time.
    """
    try:
        filter_string = sys.argv[1]
        time_interval = int(sys.argv[2])
    except IndexError:
        logger.info("Please provide the filter_string and time_interval arguments.")
        sys.exit(1)

    sched.every(time_interval).minutes.do(
        run_update_project_status, filter_string=filter_string
    ).run()

    while True:
        sched.run_pending()
        time.sleep(1)
