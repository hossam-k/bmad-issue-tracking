"""The setup skill's verify list must name every deployed workflow file.

A file missing from the list is still copied, but the installer's verification step never
checks it, so a broken deploy goes unnoticed (CLAUDE.md: "Adding or removing a workflow file").
"""

import re

from conftest import WORKFLOWS_DIR

SETUP_SKILL = WORKFLOWS_DIR.parent.parent / "SKILL.md"


def _listed():
    text = SETUP_SKILL.read_text(encoding="utf-8")
    return set(re.findall(r"_bmad/_config/custom/workflows/([\w\-/]+\.yaml)", text))


def test_every_workflow_file_is_in_the_verify_list():
    on_disk = {str(p.relative_to(WORKFLOWS_DIR)) for p in WORKFLOWS_DIR.rglob("*.yaml")}
    missing = sorted(on_disk - _listed())
    assert not missing, f"workflow files missing from SKILL.md verify list: {missing}"


def test_verify_list_has_no_stale_entries():
    on_disk = {str(p.relative_to(WORKFLOWS_DIR)) for p in WORKFLOWS_DIR.rglob("*.yaml")}
    stale = sorted(_listed() - on_disk)
    assert not stale, f"SKILL.md verify list names files that do not exist: {stale}"
