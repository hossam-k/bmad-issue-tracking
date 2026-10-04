"""OpenProject tracker adapter: dispatch wiring, MCP tool usage, and the embedded Python.

The adapter lives in workflows/trackers/openproject/. The shared atomics in common/ delegate to it
when `platform` is "openproject". These tests pin that wiring, check every MCP tool call against
the tool's real signature, and execute the adapter's Python snippets on sample inputs.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import WORKFLOWS_DIR, flatten_steps, load_all_workflows, load_workflow

ADAPTER = "trackers/openproject"
WORKFLOWS = load_all_workflows()
ADAPTER_FILES = {rel: wf for rel, wf in WORKFLOWS.items() if rel.startswith(ADAPTER + "/")}

# The BMAD statuses a work package can take, in the order resolve-status maps them.
BMAD_STATUSES = [
    "backlog", "ready-for-dev", "in-progress", "review", "awaiting-operator",
    "done", "deferred", "optional", "closed",
]
KINDS = ["prd", "epic", "story", "retrospective"]

# Atomics that delegate to a same-named adapter file.
DISPATCHED = [
    "find-issue", "create-issue", "update-issue-status",
    "update-issue-description", "post-issue-comment",
]
# Atomics that have nothing to do on OpenProject (no labels).
LABEL_NOOPS = ["create-label", "ensure-labels", "ensure-dynamic-labels", "ensure-board"]

# MCP tools the adapter may call and the parameters each accepts (openproject-mcp tools/).
TOOL_PARAMS = {
    "list_work_packages": {
        "project_id", "assignee_id", "author_id", "unassigned_only", "type_id", "priority_id",
        "active_only", "version_id", "due_before", "due_after", "created_after", "updated_after",
        "overdue_only", "parent_id", "subject", "status_id", "all_statuses", "page_size", "offset",
    },
    "get_work_package": {"work_package_id", "project_id"},
    "create_work_package": {
        "project_id", "subject", "type_id", "description", "assignee_id", "responsible_id",
        "priority_id", "status_id", "category_id", "version_id", "parent_id", "estimated_time",
    },
    "update_work_package": {
        "work_package_id", "project_id", "subject", "description", "assignee_id", "responsible_id",
        "priority_id", "status_id", "type_id", "category_id", "version_id", "estimated_time", "parent_id",
    },
    "add_work_package_comment": {"work_package_id", "project_id", "comment"},
}
# Only comments are best-effort (as on GitLab/GitHub); every other failure must stop the workflow,
# because OpenProject is the system of record and a silent failure would desync it.
BEST_EFFORT = {"trackers/openproject/post-issue-comment.yaml"}


def tool_steps(wf):
    return [s for s in flatten_steps(wf["steps"]) if s["type"] == "TOOL"]


def fields(step):
    return {key: value for _, key, value in step["block"]}


def run_step_lines(rel, store_var):
    """Raw lines of the RUN step in `rel` that STOREs `store_var` (from `- RUN:` to the STORE line).

    Read from the file, not the step parser: the parser treats a python `else:` line as a YAML field.
    """
    lines = WORKFLOWS[rel]["lines"]
    store = next(i for i, l in enumerate(lines) if re.match(rf"^\s+STORE: {store_var}\s*$", l))
    start = max(i for i in range(store) if lines[i].lstrip().startswith("- RUN:"))
    return lines[start:store]


def python_for(rel, store_var):
    """The python -c source of the RUN step in `rel` that STOREs `store_var`."""
    seg = run_step_lines(rel, store_var)
    assert 'python -c "' in seg[0], f"{rel}: {store_var} is not stored by a python -c step"
    close = max(i for i, l in enumerate(seg) if l.startswith('"'))
    return "\n".join(seg[1:close])


def passed_args(rel, store_var):
    """The quoted {placeholder} arguments passed to the python snippet, in order."""
    seg = run_step_lines(rel, store_var)
    close = max(i for i, l in enumerate(seg) if l.startswith('"'))
    return re.findall(r'"\{(\w+)\}"', seg[close])


def branch_text(step, key):
    """The raw text lines of a CHECK branch (the parser does not see bare '- STOP' steps)."""
    value = next(v for _, k, v in step["block"] if k == key)
    return [l.strip() for l in value.split("\n") if l.strip()]


def run_python(code, *args):
    done = subprocess.run([sys.executable, "-c", code, *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


# --------------------------------------------------------------------------- wiring


@pytest.mark.parametrize("op", DISPATCHED)
def test_atomic_delegates_to_adapter_when_openproject(op):
    wf = WORKFLOWS[f"common/{op}.yaml"]
    first = wf["steps"][0]
    assert first["type"] == "CHECK" and first["raw_value"] == 'platform eq "openproject"', (
        f"common/{op}.yaml must start with a platform eq \"openproject\" dispatch"
    )
    assert branch_text(first, "TRUE") == [f"- INCLUDE: {ADAPTER}/{op}", "- STOP"], (
        f"common/{op}.yaml: the openproject branch must INCLUDE the adapter then STOP"
    )
    assert f"{ADAPTER}/{op}.yaml" in WORKFLOWS, f"adapter file missing: {ADAPTER}/{op}.yaml"


@pytest.mark.parametrize("name", ["create-label", "ensure-labels", "ensure-dynamic-labels"])
def test_label_atomics_are_noops_on_openproject(name):
    first = WORKFLOWS[f"common/{name}.yaml"]["steps"][0]
    assert first["raw_value"] == 'platform eq "openproject"'
    assert branch_text(first, "TRUE") == ["- STOP"]


def test_board_is_skipped_on_openproject():
    # ensure-board stops for every platform other than gitlab, which includes openproject.
    first = WORKFLOWS["common/ensure-board.yaml"]["steps"][0]
    assert first["raw_value"] == 'platform ne "gitlab"'
    assert branch_text(first, "TRUE") == ["- STOP"]


def test_sync_issues_reads_the_openproject_status_through_the_adapter():
    content = WORKFLOWS["common/sync-issues.yaml"]["content"]
    assert f"INCLUDE: {ADAPTER}/get-issue-status" in content


def test_check_config_validates_openproject():
    content = WORKFLOWS["common/check-config.yaml"]["content"]
    assert 'platform eq "openproject"' in content
    assert 'git_platform eq "openproject"' in content, "git_platform must not be openproject"
    for key in ("issue_tracking.git_host", "issue_tracking.git_project", "issue_tracking.openproject.mcp_server"):
        assert key in content


def test_adapter_has_no_cli_calls():
    """OpenProject is reached only through MCP tools, never glab/gh."""
    for rel, wf in ADAPTER_FILES.items():
        for step in flatten_steps(wf["steps"]):
            if step["type"] == "RUN":
                assert not re.search(r"\b(glab|gh)\b", step["raw_value"]), f"{rel}: CLI call in adapter"


# --------------------------------------------------------------------------- TOOL steps


def test_tool_steps_only_in_the_adapter():
    for rel, wf in WORKFLOWS.items():
        if rel.startswith(ADAPTER + "/"):
            continue
        assert not tool_steps(wf), f"{rel}: TOOL steps belong in {ADAPTER}/ only"


def test_adapter_calls_tools():
    assert any(tool_steps(wf) for wf in ADAPTER_FILES.values())


@pytest.mark.parametrize("rel, wf", list(ADAPTER_FILES.items()), ids=list(ADAPTER_FILES))
def test_tool_steps_use_known_tools_and_arguments(rel, wf):
    for step in tool_steps(wf):
        where = f"{rel}:L{step['start_line'] + 1}"
        tool, f = step["raw_value"].strip(), fields(step)
        assert tool in TOOL_PARAMS, f"{where}: unknown MCP tool '{tool}'"
        assert f.get("SERVER", "").strip("\"' ") == "{op_mcp_server}", f"{where}: SERVER must be {{op_mcp_server}}"
        keys = set(re.findall(r'(\w+):\s*"', f.get("ARGS", "")))
        assert keys, f"{where}: TOOL has no ARGS"
        assert keys <= TOOL_PARAMS[tool], f"{where}: {tool} has no parameter(s) {sorted(keys - TOOL_PARAMS[tool])}"


@pytest.mark.parametrize("rel, wf", list(ADAPTER_FILES.items()), ids=list(ADAPTER_FILES))
def test_only_comments_are_best_effort(rel, wf):
    for step in tool_steps(wf):
        on_error = fields(step).get("ON_ERROR", "stop")
        if rel in BEST_EFFORT:
            assert on_error == "warn", f"{rel}: comments are best-effort (ON_ERROR: warn)"
        else:
            assert on_error == "stop", f"{rel}: a failed call must stop the workflow"


@pytest.mark.parametrize("rel, wf", list(ADAPTER_FILES.items()), ids=list(ADAPTER_FILES))
def test_every_tool_needs_the_config_loaded(rel, wf):
    """{op_mcp_server} must be in scope: the file loads the config itself, or includes a file that does."""
    if not tool_steps(wf):
        return
    includes = {s["raw_value"].strip() for s in flatten_steps(wf["steps"]) if s["type"] == "INCLUDE"}
    assert f"{ADAPTER}/load-config" in includes or f"{ADAPTER}/resolve-status" in includes, (
        f"{rel}: calls a tool without loading the OpenProject config"
    )


MCP_DIR = Path(os.environ.get("OPENPROJECT_MCP_DIR", Path(__file__).resolve().parents[3] / "openproject-mcp"))


@pytest.mark.skipif(not (MCP_DIR / "src").is_dir(), reason="openproject-mcp checkout not found (set OPENPROJECT_MCP_DIR)")
def test_tool_table_matches_the_real_mcp_server():
    """TOOL_PARAMS is checked against the actual tool signatures when the MCP repo is available."""
    actual = {}
    for path in (MCP_DIR / "src").rglob("tools/*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and any(
                isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "tool" for d in node.decorator_list
            ):
                actual[node.name] = {a.arg for a in node.args.args}
    for tool, params in TOOL_PARAMS.items():
        assert tool in actual, f"{tool} is not an openproject-mcp tool"
        assert params == actual[tool], f"{tool}: expected {sorted(params)}, MCP has {sorted(actual[tool])}"


# --------------------------------------------------------------------------- config mapping


def test_load_config_covers_every_type_and_status():
    content = WORKFLOWS[f"{ADAPTER}/load-config.yaml"]["content"]
    for kind in KINDS:
        assert f"op_type_{kind}: issue_tracking.openproject.type_ids.{kind}" in content
    for status in BMAD_STATUSES:
        var = "op_status_" + status.replace("-", "_")
        assert f"{var}: issue_tracking.openproject.status_ids.{status}" in content


def test_resolve_status_arguments_follow_the_name_order():
    """argv position i must carry the id of names[i]: a mix-up would set the wrong status."""
    rel = f"{ADAPTER}/resolve-status.yaml"
    code = python_for(rel, "op_status_id")
    names = ast.literal_eval(re.search(r"names = (\[.*?\])", code).group(1))
    assert names == BMAD_STATUSES
    assert passed_args(rel, "op_status_id") == ["op_status_name"] + ["op_status_" + n.replace("-", "_") for n in names]


def test_create_issue_type_arguments_follow_the_kind_order():
    rel = f"{ADAPTER}/create-issue.yaml"
    code = python_for(rel, "op_type_id")
    assert ast.literal_eval(re.search(r"zip\((\[.*?\])", code).group(1)) == KINDS
    assert passed_args(rel, "op_type_id") == ["op_kind"] + [f"op_type_{k}" for k in KINDS]


# --------------------------------------------------------------------------- embedded python


PARSE = f"{ADAPTER}/parse-ref.yaml"


@pytest.mark.parametrize("ref, kind, epic, subject", [
    ("PRD: mobile-oidc", "prd", "", "PRD: mobile-oidc"),
    ("Epic 2: Auth", "epic", "2", "Epic 2:"),
    ("epic-2", "epic", "2", "Epic 2:"),
    ("2", "epic", "2", "Epic 2:"),
    ("Story 1.3: Login Form", "story", "1", "Story 1.3:"),
    ("1-3-login-form", "story", "1", "Story 1.3:"),
    ("12-10-big-epic", "story", "12", "Story 12.10:"),
    ("Retrospective: Epic 2", "retrospective", "2", "Retrospective: Epic 2"),
    ("epic-2-retrospective", "retrospective", "2", "Retrospective: Epic 2"),
    ("something else", "text", "", "something else"),
])
def test_parse_ref(ref, kind, epic, subject):
    got_kind = run_python(python_for(PARSE, "op_kind"), ref)
    got_epic = run_python(python_for(PARSE, "op_epic_num"), ref, got_kind)
    got_subject = run_python(python_for(PARSE, "op_subject"), ref, got_epic, got_kind)
    assert (got_kind, got_epic, got_subject) == (kind, epic, subject)


def test_story_subject_does_not_collide_across_epics():
    """'Story 1.3:' must not be a prefix of 'Story 11.3:' or 'Story 1.30:'."""
    prefix = "Story 1.3:"
    assert not "Story 11.3: x".startswith(prefix) and not "Story 1.30: x".startswith(prefix)


RESOLVE = f"{ADAPTER}/resolve-status.yaml"


def test_resolve_status_maps_by_name():
    ids = [str(100 + i) for i in range(9)]
    code = python_for(RESOLVE, "op_status_id")
    assert run_python(code, "in-progress", *ids) == "102"
    assert run_python(code, "closed", *ids) == "108"


def test_resolve_status_unmapped_stays_empty_and_keeps_positions():
    code = python_for(RESOLVE, "op_status_id")
    ids = ["1", "2", "3", "4", "5", "6", "", "8", "9"]  # deferred (index 6) unmapped
    assert run_python(code, "deferred", *ids) == ""
    assert run_python(code, "optional", *ids) == "8"  # not shifted by the empty id
    assert run_python(code, "no-such-status", *ids) == ""


SELECT = f"{ADAPTER}/select-wp.yaml"
WPS = json.dumps({"count": 3, "total": 3, "work_packages": [
    {"id": 11, "subject": "PRD: mobile-oidc-v2"},
    {"id": 12, "subject": "PRD: mobile-oidc"},
    {"id": 13, "subject": "Story 1.3: Login Form"},
]})


@pytest.mark.parametrize("want, mode, expected", [
    ("PRD: mobile-oidc", "exact", "12"),       # exact must not match the longer 'mobile-oidc-v2'
    ("PRD: mobile-oidc", "prefix", "11"),       # prefix would — which is why PRDs use exact
    ("Story 1.3:", "prefix", "13"),
    ("login", "contains", "13"),
    ("Story 9.9:", "prefix", ""),
])
def test_select_wp(tmp_path, want, mode, expected):
    f = tmp_path / "list.json"
    f.write_text(WPS, encoding="utf-8")
    assert run_python(python_for(SELECT, "op_selected"), str(f), want, mode) == expected


def test_select_wp_handles_an_empty_result(tmp_path):
    f = tmp_path / "list.json"
    f.write_text(json.dumps({"count": 0, "total": 0, "work_packages": []}), encoding="utf-8")
    assert run_python(python_for(SELECT, "op_selected"), str(f), "PRD: x", "exact") == ""


CREATE = f"{ADAPTER}/create-issue.yaml"


@pytest.mark.parametrize("labels, expected", [
    ("type:story\nstatus:ready-for-dev\nprd:x\nx:epic-1", "ready-for-dev"),
    ("type:prd\nprd:x", ""),
    ("type:retrospective\nstatus:done\nprd:x", "done"),
])
def test_create_issue_reads_the_initial_status_from_labels(labels, expected):
    assert run_python(python_for(CREATE, "op_status_name"), labels, ":") == expected


STATUS = f"{ADAPTER}/get-issue-status.yaml"


@pytest.mark.parametrize("wp, target_id, expected", [
    ({"id": 5, "status": {"id": 7, "title": "In progress"}}, "7", "status:in-progress"),
    ({"id": 5, "status": {"id": 7, "title": "In progress"}}, "12", "status:other"),
    ({"id": 5, "status": None}, "7", "status:other"),
    ({"id": 5, "status": {"id": 7}}, "", "status:other"),  # target status not mapped
])
def test_get_issue_status_label_matches_only_the_mapped_status(tmp_path, wp, target_id, expected):
    f = tmp_path / "wp.json"
    f.write_text(json.dumps(wp), encoding="utf-8")
    got = run_python(python_for(STATUS, "current_status_label"), str(f), target_id, ":", "in-progress")
    assert got == expected


def test_status_label_equals_what_sync_issues_compares_against():
    """sync-issues compares current_status_label to status{sep}{mapped_status}."""
    assert 'current_status_label eq "status{sep}{mapped_status}"' in WORKFLOWS["common/sync-issues.yaml"]["content"]
