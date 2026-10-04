"""MR/PR and CI steps follow the git remote, never the issue tracker.

The issue tracker (`platform`) may be gitlab, github or openproject, while merge requests,
pull requests and pipelines always live on the git remote (`git_platform`). These tests pin
the routing rules that make that split work.
"""

import re

import pytest
from conftest import load_all_workflows, collect_includes

# Commands/API paths that act on the git remote's MRs/PRs and CI.
GIT_REMOTE_RE = re.compile(
    r"glab mr |glab ci |gh pr |gh run |/merge_requests|/pipelines|/pulls/"
)
STEP_START_RE = re.compile(r"^(\s*)- (\w+):")
PLATFORM_LINE_RE = re.compile(r"^\s+PLATFORM:\s*\w+\s*$")

# Files that read git-remote coordinates and so must resolve them via the shared helper.
RESOLVER = "common/resolve-mr-repo"
# find-mr / ensure-mr take mr_repo as a documented INPUT from their caller.
TAKES_MR_REPO_AS_INPUT = {"common/find-mr.yaml", "common/ensure-mr.yaml", "common/resolve-mr-repo.yaml"}


def _run_steps(lines):
    """Yield (line_no, text) for each RUN step, text spanning the step and its sub-fields."""
    i = 0
    while i < len(lines):
        m = STEP_START_RE.match(lines[i])
        if m and m.group(2) == "RUN":
            indent = len(m.group(1))
            j = i + 1
            while j < len(lines):
                n = STEP_START_RE.match(lines[j])
                if n and len(n.group(1)) <= indent:
                    break
                j += 1
            yield i + 1, "\n".join(lines[i:j])
            i = j
        else:
            i += 1


WORKFLOWS = list(load_all_workflows().items())


@pytest.mark.parametrize("rel, wf", WORKFLOWS, ids=[r for r, _ in WORKFLOWS])
def test_mr_and_ci_commands_are_not_gated_on_the_tracker(rel, wf):
    """A step that touches MRs/PRs/pipelines may use GIT_PLATFORM, never PLATFORM."""
    offenders = []
    for line_no, text in _run_steps(wf["lines"]):
        has_tracker_gate = any(PLATFORM_LINE_RE.match(l) for l in text.split("\n")[1:])
        if has_tracker_gate and GIT_REMOTE_RE.search(text.split("\n")[0] + text):
            offenders.append(f"L{line_no}")
    assert not offenders, (
        f"{rel}: MR/PR/CI step gated on PLATFORM (tracker) instead of GIT_PLATFORM: {offenders}"
    )


@pytest.mark.parametrize("rel, wf", WORKFLOWS, ids=[r for r, _ in WORKFLOWS])
def test_mr_repo_comes_from_the_resolver(rel, wf):
    """mr_repo and the mr_* coordinates are only ever set by common/resolve-mr-repo."""
    if rel == "common/resolve-mr-repo.yaml":
        return
    content = wf["content"]
    assert not re.search(r"variable:\s*mr_(repo|host|project|project_enc)\b", content), (
        f"{rel}: sets an mr_* coordinate itself; INCLUDE {RESOLVER} instead"
    )


@pytest.mark.parametrize("rel, wf", WORKFLOWS, ids=[r for r, _ in WORKFLOWS])
def test_users_of_mr_coordinates_resolve_them(rel, wf):
    """A workflow that runs commands with mr_* coordinates must INCLUDE the resolver
    (directly, or through common/check-mr-ci), unless it takes mr_repo as a documented input."""
    if rel in TAKES_MR_REPO_AS_INPUT:
        return
    uses = any(
        re.search(r"\{mr_(repo|host|project|project_enc)\}", text)
        for _, text in _run_steps(wf["lines"])
    )
    if not uses:
        return
    includes = collect_includes(wf)
    assert RESOLVER in includes or "common/check-mr-ci" in includes, (
        f"{rel}: uses mr_* coordinates without INCLUDE {RESOLVER}"
    )


@pytest.mark.parametrize("rel, wf", WORKFLOWS, ids=[r for r, _ in WORKFLOWS])
def test_issue_references_come_from_resolve_issue_ref(rel, wf):
    """MR/PR descriptions get their issue reference from common/resolve-issue-ref
    (which knows #N, cross-host URLs and OpenProject OP#N), never a hard-coded '#{issue_id}'."""
    if rel == "common/resolve-issue-ref.yaml":
        return
    assert not re.search(r"(Closes|Related to) #\{issue_id\}", wf["content"]), (
        f"{rel}: hard-codes an issue reference; use common/resolve-issue-ref"
    )


def test_resolver_covers_same_platform_and_cross_platform():
    wf = dict(WORKFLOWS)["common/resolve-mr-repo.yaml"]
    c = wf["content"]
    assert "git_platform eq platform" in c  # same-platform reuses host/project
    assert "issue_tracking.git_host" in c and "issue_tracking.git_project" in c  # otherwise config


def test_issue_ref_resolver_knows_openproject():
    c = dict(WORKFLOWS)["common/resolve-issue-ref.yaml"]["content"]
    assert 'platform eq "openproject"' in c
    assert "OP#{issue_id}" in c
