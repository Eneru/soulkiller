"""Independent synthetic source and scan findings for worker policy tests."""

SUPERVISOR_SOURCE = """import subprocess
def run_command(command):
    return subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=False, close_fds=True, start_new_session=True,
        env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
"""


def clean_report() -> dict[str, object]:
    """Use independently declared IDs/locations for a minimal approved source."""
    return {
        "errors": [],
        "results": [
            {"test_id": "B404", "filename": "src/soulkiller_text/supervise.py", "line_number": 1},
            {
                "test_id": "B603",
                "filename": "src/soulkiller_text/supervise.py",
                "line_number": 3,
            },
        ],
    }
