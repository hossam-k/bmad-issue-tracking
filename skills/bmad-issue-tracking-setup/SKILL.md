---
name: bmad-issue-tracking-setup
description: 'One-time setup for issue tracking integration. Use after installing the module to deploy TOML overrides and shared tasks.'
---

# Issue Tracking Setup

One-time setup for BMAD Issue Tracking integration. Deploys TOML overrides to `_bmad/custom/` and a shared task to `_bmad/_config/custom/`.

## Prerequisites

- BMAD Method module (BMM) 6.12.0+ installed
- `uv` available (required by BMM 6.12.0+ skills; the workflow YAMLs invoke Python via `uv run python`)
- For OpenProject as the issue tracker: an OpenProject MCP server (`openproject-mcp`) registered for the project, with a version that provides `list_statuses` and the `subject` / `all_statuses` / `parent_id` options (step 7b verifies this)
- This module installed via the new Skills-as-modules installer (manifest `module = "issue-tracking"`, version ≥3.0.0).

## Instructions

<task>
<action>IMPORTANT: When a step asks you to configure a value with a default, you MUST present the default as a suggestion and wait for the user's answer before writing anything. Never silently apply a default.</action>

<step n="1" goal="Verify BMM installation">
<action>Detect the BMM version. Try the legacy path first, then fall back to the new Skills-as-modules layout:</action>
<action>1. **Legacy install** — read the `# Version:` header in `_bmad/bmm/config.yaml` (single-file BMM ≤ 6.11.0).</action>
<action>2. **New install (Skills-as-modules)** — read the `version` field in `.agents/skills/bmad-sprint-planning/module-manifest.toml` (per-skill BMM 6.13.0-next and later). If that skill is not installed, scan the first manifest under `.agents/skills/bmad-*/module-manifest.toml` whose `module = "method"`.</action>
<action>Extract the semver. Accept it only if ≥ 6.12.0.</action>
<check if="version < 6.12.0 or not found">
  <output>ERROR: BMM 6.12.0+ required. BMad adopted the flat per-skill Skills-as-modules install format in 6.12.0 (replacing the legacy `_bmad/{bmm,bmb,cis,core}/` subdirectory layout). BMM ≤ 6.11.0 cannot consume this module's `scripts/`-declared binaries or the flat `_bmad/{method,toolbox}/` deploy targets. Run `npx skills add bmad-code-org/BMAD-METHOD` first.</output>
  <action>Stop here</action>
</check>
<action>Verify `uv` is available by running `uv --version`. If missing, report the BMM 6.12.0 requirement (`uv` is mandatory for BMM 6.12.0+ skills).</action>
</step>

<step n="2" goal="Deploy TOML overrides">
<action>Locate the TOML overrides. Check these locations in order:</action>
1. `~/.bmad/cache/custom-modules/github.com/jrevillard/bmad-issue-tracking/skills/bmad-issue-tracking-setup/assets/custom/`
2. Ask the user for the path to the cloned `bmad-issue-tracking` repo

<action>IMPORTANT: Always overwrite existing TOML files — this is an update, not a first install. New versions may have changed TOML content.</action>

<action>Copy all TOML files to `_bmad/custom/`, overwriting existing files:</action>

```bash
cp -f <path>/*.toml _bmad/custom/
```

<action>Remove any `bmad-*.toml` files in `_bmad/custom/` that no longer exist in the source (files may have been renamed or removed in a new version).</action>

<action>The following TOML files should now exist in `_bmad/custom/`:</action>
- `bmad-build.toml` (requires BMM 6.11.0+; manual one-shot flow — push + wait CI + update issue + post comment on completion)
- `bmad-build-auto.toml` (requires BMM 6.11.0+; bmad-loop flow — same unified dispatch as bmad-build)
- `bmad-code-review.toml` (requires BMM 6.11.0+; delegates to common/post-dev-complete-review-finish.yaml)
- `bmad-correct-course.toml` (requires BMM 6.11.0+)
- `bmad-create-architecture.toml` (requires BMM 6.11.0+)
- `bmad-create-epics-and-stories.toml` (requires BMM 6.11.0+)
- `bmad-create-prd.toml` (requires BMM 6.11.0+, superseded by bmad-prd.toml)
- `bmad-create-story.toml` (requires BMM 6.11.0+; shim — deprecated upstream, bmad-build is the official path. Delegates to common/post-dev-complete-create-story.yaml)
- `bmad-dev-story.toml` (requires BMM 6.11.0+; shim — deprecated upstream, bmad-build is the official path. Delegates to common/post-dev-complete-dev-finish.yaml)
- `bmad-edit-prd.toml` (requires BMM 6.11.0+, superseded by bmad-prd.toml)
- `bmad-prd.toml` (requires BMM 6.11.0+; unified PRD override)
- `bmad-retrospective.toml` (requires BMM 6.11.0+)
- `bmad-sprint-planning.toml` (requires BMM 6.11.0+; owns the sprint-status artifact)
- `bmad-sprint-status.toml` (requires BMM 6.11.0+; consolidated into bmad-sprint-planning, retained as shim alias)
- `bmad-ux.toml` (requires BMM 6.11.0+; replaces bmad-create-ux-design, removed in 6.11.0)

<action>Note: All TOML files are in pointer format — they reference workflow YAML files deployed in step 3.</action>
<action>Verify each TOML file is valid by checking it contains a `[workflow]` section and at least one hook key (`on_complete`, `activation_steps_append`, etc.).</action>
</step>

<step n="3" goal="Deploy workflow language files">
<action>The TOML overrides reference workflow language YAML files. These are deployed separately to keep the TOML files as simple pointers.</action>

<action>Locate the workflow language files. They are siblings of the `custom/` directory (in the same `assets/` parent):</action>
1. `~/.bmad/cache/custom-modules/github.com/jrevillard/bmad-issue-tracking/skills/bmad-issue-tracking-setup/assets/`
2. Ask the user for the path to the cloned `bmad-issue-tracking` repo

<action>IMPORTANT: Always overwrite existing files — new versions may have changed workflow content.</action>

<action>Copy the workflow language specification and workflow YAML files, overwriting existing files:</action>

```bash
cp -f <path>/bmad-workflow-lang.md _bmad/_config/custom/
mkdir -p _bmad/_config/custom/workflows
cp -rf <path>/workflows/* _bmad/_config/custom/workflows/
```

<action>Remove any workflow YAML files in `_bmad/_config/custom/workflows/` that no longer exist in the source (files may have been renamed or removed in a new version).</action>

<action>Verify the following files exist:</action>
- `_bmad/_config/custom/bmad-workflow-lang.md`
- `_bmad/_config/custom/workflows/common/check-config.yaml`
- `_bmad/_config/custom/workflows/common/check-mr-ci.yaml`
- `_bmad/_config/custom/workflows/common/create-issue.yaml`
- `_bmad/_config/custom/workflows/common/create-label.yaml`
- `_bmad/_config/custom/workflows/common/ensure-board.yaml`
- `_bmad/_config/custom/workflows/common/ensure-dynamic-labels.yaml`
- `_bmad/_config/custom/workflows/common/ensure-issue.yaml`
- `_bmad/_config/custom/workflows/common/ensure-mr.yaml`
- `_bmad/_config/custom/workflows/common/ensure-labels.yaml`
- `_bmad/_config/custom/workflows/common/find-issue.yaml`
- `_bmad/_config/custom/workflows/common/find-mr.yaml`
- `_bmad/_config/custom/workflows/common/derive-prd-key.yaml`
- `_bmad/_config/custom/workflows/common/find-prd.yaml`
- `_bmad/_config/custom/workflows/common/find-prd-key.yaml`
- `_bmad/_config/custom/workflows/common/find-stories.yaml`
- `_bmad/_config/custom/workflows/common/get-failed-jobs.yaml`
- `_bmad/_config/custom/workflows/common/get-mr-pipeline.yaml`
- `_bmad/_config/custom/workflows/common/mark-mr-ready.yaml`
- `_bmad/_config/custom/workflows/common/merge-mr.yaml`
- `_bmad/_config/custom/workflows/common/post-build-dispatch.yaml`
- `_bmad/_config/custom/workflows/common/post-build-dispatch-auto.yaml`
- `_bmad/_config/custom/workflows/common/post-build-dispatch-interactive.yaml`
- `_bmad/_config/custom/workflows/common/post-dev-complete.yaml`
- `_bmad/_config/custom/workflows/common/post-dev-complete-create-story.yaml`
- `_bmad/_config/custom/workflows/common/post-dev-complete-dev-finish.yaml`
- `_bmad/_config/custom/workflows/common/post-dev-complete-review-finish.yaml`
- `_bmad/_config/custom/workflows/common/post-issue-comment.yaml`
- `_bmad/_config/custom/workflows/common/resolve-issue-ref.yaml`
- `_bmad/_config/custom/workflows/common/resolve-mr-repo.yaml`
- `_bmad/_config/custom/workflows/common/set-story-status.yaml`
- `_bmad/_config/custom/workflows/common/sync-issues.yaml`
- `_bmad/_config/custom/workflows/common/update-issue-description.yaml`
- `_bmad/_config/custom/workflows/common/update-issue-status.yaml`
- `_bmad/_config/custom/workflows/common/wait-for-green-ci.yaml`
- `_bmad/_config/custom/workflows/common/write-ci-status.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/create-issue.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/find-issue.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/find-wp.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/get-issue-status.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/load-config.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/parse-ref.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/post-issue-comment.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/resolve-status.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/select-wp.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/update-issue-description.yaml`
- `_bmad/_config/custom/workflows/trackers/openproject/update-issue-status.yaml`
- `_bmad/_config/custom/workflows/issue-sync/prepare.yaml`
- `_bmad/_config/custom/workflows/issue-sync/sync.yaml`
- `_bmad/_config/custom/workflows/bmad-prd/activation.yaml`
- `_bmad/_config/custom/workflows/bmad-prd/complete.yaml`
- `_bmad/_config/custom/workflows/bmad-ux/activation.yaml`
- `_bmad/_config/custom/workflows/bmad-ux/complete.yaml`
- `_bmad/_config/custom/workflows/code-review/activation.yaml`
- `_bmad/_config/custom/workflows/correct-course/activation.yaml`
- `_bmad/_config/custom/workflows/correct-course/complete.yaml`
- `_bmad/_config/custom/workflows/create-architecture/activation.yaml`
- `_bmad/_config/custom/workflows/create-architecture/complete.yaml`
- `_bmad/_config/custom/workflows/create-epics-and-stories/activation.yaml`
- `_bmad/_config/custom/workflows/create-epics-and-stories/complete.yaml`
- `_bmad/_config/custom/workflows/create-prd/activation.yaml`
- `_bmad/_config/custom/workflows/create-prd/complete.yaml`
- `_bmad/_config/custom/workflows/create-story/activation.yaml`
- `_bmad/_config/custom/workflows/dev-story/activation.yaml`
- `_bmad/_config/custom/workflows/edit-prd/activation.yaml`
- `_bmad/_config/custom/workflows/edit-prd/complete.yaml`
- `_bmad/_config/custom/workflows/retrospective/activation.yaml`
- `_bmad/_config/custom/workflows/retrospective/complete.yaml`
- `_bmad/_config/custom/workflows/sprint-planning/activation.yaml`
- `_bmad/_config/custom/workflows/sprint-planning/complete.yaml`
- `_bmad/_config/custom/workflows/sprint-status/activation.yaml`
- `_bmad/_config/custom/workflows/sprint-status/complete.yaml`
</step>

<step n="4" goal="Deploy bmad-loop CI status gate (optional)">
<action>Deploy `ci-status.sh` only if the consuming project uses bmad-loop (has a `.bmad-loop/` directory after `bmad-loop init`). No bmad-loop plugins are needed — the `bmad-build-auto.toml` `on_complete` hook drives the issue tracking + CI write.</action>

<action>**Worktree isolation is required.** Our CI gate and close-trace-mr plugin only function when bmad-loop runs with `[scm] isolation = "worktree"`. Without it, the verify command runs in the main checkout where it can't reliably find inputs, and close-trace-mr never executes (the plugin isn't seeded into worktrees). Confirm `[scm] isolation = "worktree"` in `.bmad-loop/policy.toml`; if absent or set to anything else, set it to `"worktree"`. Warn the user — changing this also affects merge-back behavior (`target_branch`, `delete_branch`); they may want to review those in the same edit.</action>

<action>**`worktree_seed` copies gitignored paths only.** bmad-loop docs: "A git worktree checks out tracked files only". For the CI gate to land in every story worktree, our files MUST be gitignored AND listed in `worktree_seed`. Otherwise the verify command fails with "No such file or directory" on the first story.</action>

<check if=".bmad-loop/ directory exists">
  <true>
    <action>Copy `ci-status.sh` to the repo root:</action>
    ```bash
    mkdir -p .bmad-loop
    cp -f <path>/scripts/bmad-loop/ci-gate/ci-status.sh .bmad-loop/ci-status.sh
    chmod +x .bmad-loop/ci-status.sh
    ```
    <action>Make the file gitignored so bmad-loop's `worktree_seed` will copy it into each worktree:</action>
    ```bash
    # Untrack if previously committed (file stays on disk)
    git rm --cached .bmad-loop/ci-status.sh 2>/dev/null || true
    # Append to .gitignore idempotently
    grep -qxF '.bmad-loop/ci-status.sh' .gitignore || echo '.bmad-loop/ci-status.sh' >> .gitignore
    ```
    <action>Also gitignore the close-trace-mr plugin directory (step 5 deploys it) so it gets seeded into worktrees too:</action>
    ```bash
    grep -qxF '.bmad-loop/plugins/close-trace-mr/' .gitignore || echo '.bmad-loop/plugins/close-trace-mr/' >> .gitignore
    ```
    <action>Edit `.bmad-loop/policy.toml` (preserve existing keys). Set `[scm] isolation = "worktree"` if not already, and ensure `worktree_seed` lists both our paths:</action>
    ```toml
    [scm]
    isolation = "worktree"               # REQUIRED by our integration
    worktree_seed = [".bmad-loop/ci-status.sh", ".bmad-loop/plugins/close-trace-mr"]

    [verify]
    commands = ["bash .bmad-loop/ci-status.sh"]
    ```
    <action>Verify: `.bmad-loop/ci-status.sh` exists and is executable; `git check-ignore .bmad-loop/ci-status.sh` exits 0 (gitignored); `.bmad-loop/plugins/close-trace-mr/` is gitignored; `.bmad-loop/policy.toml` has the `[verify] commands`, `[scm] isolation = "worktree"`, and `[scm] worktree_seed` entries (with both paths listed).</action>
    <action>If `.bmad-loop/plugins/story-track-dev` or `.bmad-loop/plugins/story-track-review` exist, remove them and delete their `[plugins] enabled` entries from `.bmad-loop/policy.toml` (superseded by the `on_complete` hook).</action>
  </true>
  <false>
    <output>Skipping ci-status — project does not use bmad-loop (no `.bmad-loop/` directory). Without bmad-loop, the integration has nowhere to live.</output>
  </false>
</check>
</step>

<step n="5" goal="Deploy bmad-loop close-trace-mr plugin (optional)">
<action>Deploy the `close-trace-mr` bmad-loop plugin only when the project uses both `bmad-loop` AND `bmad-issue-tracking`. The plugin auto-closes the trace MR/PR opened by `common/ensure-mr.yaml` after `bmad-loop`'s local merge — without it, the trace MR stays open in the project list with an outdated diff.</action>

<check if=".bmad-loop/ directory exists AND _bmad/custom/issue-tracking.yaml exists">
  <true>
    <action>Locate the plugin source. Check these locations in order:</action>
    1. `~/.bmad/cache/custom-modules/github.com/jrevillard/bmad-issue-tracking/skills/bmad-issue-tracking-setup/scripts/close-trace-mr/`
    2. Ask the user for the path to the cloned `bmad-issue-tracking` repo

    <action>Copy the plugin into the project's bmad-loop plugins directory:</action>
    ```bash
    mkdir -p .bmad-loop/plugins
    cp -rf <path>/scripts/close-trace-mr .bmad-loop/plugins/
    chmod +x .bmad-loop/plugins/close-trace-mr/close-trace-mr.sh
    ```

    <action>The plugin directory is already gitignored (`.bmad-loop/plugins/close-trace-mr/`) and listed in `worktree_seed` (set by step 4). bmad-loop copies the whole directory into each new worktree at run start, so the plugin is available regardless of which branch a story was cut from. Confirm both via `git check-ignore .bmad-loop/plugins/close-trace-mr/` (exit 0) and the policy.toml `worktree_seed` entry.</action>

    <action>Verify the following files exist in the main checkout (they will be present — copied above; bmad-loop re-copies them per worktree at run time):</action>
    - `.bmad-loop/plugins/close-trace-mr/plugin.toml`
    - `.bmad-loop/plugins/close-trace-mr/close-trace-mr.sh` (executable)
    - `.bmad-loop/plugins/close-trace-mr/close_trace_mr.py`
    - `.bmad-loop/plugins/close-trace-mr/README.md`

    <action>Plugin discovery is automatic on the next bmad-loop run (bmad-loop walks `.bmad-loop/plugins/*` and parses each `plugin.toml`). The plugin auto-detects `platform`, `host`, `project` from `_bmad/custom/issue-tracking.yaml` (the single source of truth, written by steps 6 and 7). For env-specific overrides (CI runner vs developer laptop, multi-platform repos), use the plugin's env var overrides (`CLOSE_TRACE_MR_PLATFORM_OVERRIDE`, `CLOSE_TRACE_MR_HOST_OVERRIDE`, `CLOSE_TRACE_MR_PROJECT_OVERRIDE`) instead of duplicating values in policy.toml. To opt out without removing the files, add to `.bmad-loop/policy.toml`:</action>
    ```toml
    [plugins.close-trace-mr.settings]
    close_trace_mr = false
    ```

    <action>Run the plugin's tests to confirm the deployment is healthy:</action>
    ```bash
    uv run --no-project --directory .bmad-loop/plugins/close-trace-mr \
        python -m pytest tests/ -v
    ```
  </true>
  <false>
    <output>Skipping close-trace-mr — project needs BOTH `.bmad-loop/` AND `_bmad/custom/issue-tracking.yaml` to benefit. The plugin no-ops cleanly otherwise.</output>
  </false>
</check>
</step>

<step n="6" goal="Configure issue_tracking">
<action>Check if `_bmad/custom/issue-tracking.yaml` already exists.</action>
<check if="config file exists">
  <false>
    <action>Create `_bmad/custom/issue-tracking.yaml` with the following content (this file is independent from BMM and survives BMM updates):</action>

    ```yaml
    issue_tracking:
      enabled: true
      platform: gitlab  # gitlab, github or openproject — configure in next step
      # worktree_base, host, project configured in steps 4-5
    ```
  </false>
</check>
<check if="worktree_base is already set">
  <true>
    <output>worktree_base already configured: {worktree_base}.</output>
  </true>
  <false>
    <action>Ask the user for their worktree base directory. Default: `_bmad/worktrees`</action>
    <action>Set `issue_tracking.worktree_base` to the user's answer in `_bmad/custom/issue-tracking.yaml`.</action>
  </false>
</check>
<action>Ensure the worktree base directory is in `.gitignore`. Read the configured `worktree_base` value and check if it is listed. If not, append it.</action>
</step>

<step n="7" goal="Configure platform and connection">
<action>Detect the git remote by running `git remote get-url origin`.</action>
<action>Determine the git remote platform from the remote URL (gitlab.com → gitlab, github.com → github, GHE/GitLab self-hosted → ask user).</action>
<action>Extract `git_host` (hostname) and `git_project` (group/project or owner/repo) from the remote URL.</action>
<action>Always set `issue_tracking.git_platform` to the git remote platform in `_bmad/custom/issue-tracking.yaml`.</action>
<check if="platform is already set">
  <true>
    <output>Platform already configured: {platform}.</output>
  </true>
  <false>
    <action>Ask the user which platform they use for issue tracking: GitLab, GitHub or OpenProject.</action>
    <action>Set `issue_tracking.platform` to the chosen value.</action>
  </false>
</check>
<check if="git_platform is already set">
  <true>
    <output>git_platform already configured: {git_platform}.</output>
  </true>
  <false>
    <action>Set `issue_tracking.git_platform` to the git remote platform in `_bmad/custom/issue-tracking.yaml`.</action>
  </false>
</check>
<check if="platform is openproject">
  <output>NOTE: OpenProject only tracks the work (PRDs, epics, stories and retrospectives become work packages). Branches, MRs/PRs and CI stay on the git remote ({git_platform}), so `git_platform`, `git_host` and `git_project` are required.</output>
</check>
<check if="platform differs from git remote platform">
  <output>NOTE: The issue tracker ({platform}) differs from the git remote ({git_platform}). This is valid — e.g. code on GitLab but issues on GitHub, or issues in OpenProject. MRs/PRs will target the git remote, so `git_host` and `git_project` are also needed.</output>
  <check if="git_host is already set">
    <true>
      <output>git_host already configured: {git_host}.</output>
    </true>
    <false>
      <action>Set `issue_tracking.git_host` to the git remote hostname (already extracted from the remote URL above).</action>
    </false>
  </check>
  <check if="git_project is already set">
    <true>
      <output>git_project already configured: {git_project}.</output>
    </true>
    <false>
      <action>Set `issue_tracking.git_project` to the git remote project path (already extracted from the remote URL above).</action>
    </false>
  </check>
</check>
<check if="platform does NOT differ from git remote platform">
  <check if="git_host is set">
    <output>NOTE: Platform and git remote match — `git_host` is no longer needed. Removing it.</output>
    <action>Remove `issue_tracking.git_host` from `_bmad/custom/issue-tracking.yaml`.</action>
  </check>
  <check if="git_project is set">
    <output>NOTE: Platform and git remote match — `git_project` is no longer needed. Removing it.</output>
    <action>Remove `issue_tracking.git_project` from `_bmad/custom/issue-tracking.yaml`.</action>
  </check>
</check>
<check if="host is already set">
  <true>
    <output>host already configured: {host}.</output>
  </true>
  <false>
    <action>Ask the user for the issue tracker host (e.g. `gitlab.company.com` or `github.com`; for OpenProject the hostname without scheme, e.g. `openproject.company.com`). Set `issue_tracking.host` in `_bmad/custom/issue-tracking.yaml`.</action>
  </false>
</check>
<check if="project is already set">
  <true>
    <output>project already configured: {project}.</output>
  </true>
  <false>
    <check if="platform is openproject">
      <true>
        <output>The OpenProject project is chosen from a list in step 7b.</output>
      </true>
      <false>
        <action>Ask the user for the issue tracker project path (e.g. `my-group/my-project`). Set `issue_tracking.project` in `_bmad/custom/issue-tracking.yaml`.</action>
      </false>
    </check>
  </false>
</check>
</step>

<step n="7b" goal="Configure OpenProject (only when platform is openproject)">
<check if="platform is NOT openproject">
  <action>Skip this step.</action>
</check>
<check if="platform is openproject">
  <action>Ask the user for the name of the MCP server that exposes the OpenProject tools. Default: `open-project` (its tools are called `mcp__<server>__<tool>`). Set `issue_tracking.openproject.mcp_server` to the answer.</action>
  <action>Call `mcp__{mcp_server}__who_am_i` to verify the server is connected and authenticated.</action>
  <check if="the tool is not available or the call fails">
    <output>The OpenProject MCP server '{mcp_server}' is not available in this session. Register it for this project by adding it to `.mcp.json` (the token is read from your environment, so it is not committed):

    {
      "mcpServers": {
        "{mcp_server}": {
          "command": "uvx",
          "args": ["--from", "git+https://github.com/espace/openproject-mcp", "openproject-mcp"],
          "env": {
            "OPENPROJECT_URL": "https://<your-openproject-host>",
            "OPENPROJECT_TOKEN": "${OPENPROJECT_TOKEN}"
          }
        }
      }
    }

    Unattended runs (bmad-loop) need the server as well, which is why project scope (`.mcp.json`) is preferred over user scope. Set OPENPROJECT_TOKEN to an OpenProject API token, open a new session and re-run /bmad-issue-tracking-setup.</output>
    <action>Set `issue_tracking.enabled: false` (issue tracking stays in file-system mode until setup is re-run). Do NOT write the `issue_tracking.openproject` block. End this step.</action>
  </check>
  <action>Call `mcp__{mcp_server}__list_statuses`. If the tool does not exist, the MCP server is too old: tell the user to update openproject-mcp (this module needs `list_statuses` and the `subject`, `all_statuses` and `parent_id` options), set `issue_tracking.enabled: false`, and end this step.</action>

  <action>Call `mcp__{mcp_server}__list_projects`, show each project's id and name, and ask the user which project holds the BMAD work packages. Set `issue_tracking.project` to that project's id, written as a quoted string (e.g. `project: "123"`).</action>

  <action>Call `mcp__{mcp_server}__list_work_package_types`, show id and name, and ask which type to use for each BMAD item: `prd`, `epic`, `story`, `retrospective`. Suggest the closest names (for example an Epic type for `epic`, a User story or Feature type for `story`, a Task for `retrospective`) and wait for the answer. Every kind needs a type.</action>

  <action>Show the statuses from `list_statuses` (id, name, and whether OpenProject treats the status as closed). Ask which status to use for each BMAD status: `backlog`, `ready-for-dev`, `in-progress`, `review`, `awaiting-operator`, `done`, `deferred`, `optional`, `closed`. Suggest by name (New for backlog, In progress for in-progress, a closed status for done and closed) and wait for the answer. A BMAD status may be left unmapped: the sync then leaves that work package's status unchanged and warns.</action>
  <check if="the status chosen for `done` or `closed` is not marked closed in OpenProject">
    <output>WARN: '{status_name}' is not a closed status in OpenProject, so work packages mapped to BMAD '{bmad_status}' will not show as closed. Choose a closed status, or continue knowing they stay open.</output>
  </check>

  <action>Write the mapping under `issue_tracking` in `_bmad/custom/issue-tracking.yaml`. Write every key, using an empty string for an unmapped status, and quote the ids:</action>

  ```yaml
  issue_tracking:
    openproject:
      mcp_server: open-project
      type_ids:
        prd: "7"
        epic: "7"
        story: "8"
        retrospective: "3"
      status_ids:
        backlog: "1"
        ready-for-dev: "2"
        in-progress: "7"
        review: "8"
        awaiting-operator: "4"
        done: "12"
        deferred: ""
        optional: ""
        closed: "12"
  ```

  <action>Never add a key named `platform`, `host` or `project` inside the `openproject` block: tools that read this file line by line (the close-trace-mr plugin) would confuse it with the top-level keys.</action>
  <action>Set `issue_tracking.enabled: true`.</action>
  <output>Reminder: OpenProject only accepts status changes that its workflow allows for the type and role. Use an account (the MCP's API token) that may move work packages between these statuses, or the sync will stop at the first status OpenProject rejects.</output>
</check>
</step>

<step n="8" goal="Verify CLI connectivity">
<action>Run the auth check for each platform that has a CLI (use `--hostname` for self-hosted instances):</action>
- Issue tracker on GitLab: `glab auth status --hostname {host}`
- Issue tracker on GitHub: `gh auth status --hostname {host}`
- Git remote (MRs/PRs and CI) when it differs from the issue tracker, which is always the case for OpenProject: `glab auth status --hostname {git_host}` when `git_platform` is gitlab, `gh auth status --hostname {git_host}` when it is github
- OpenProject: no CLI — its connection was verified with the MCP `who_am_i` call in step 7b

<check if="auth fails">
  <output>WARN: CLI not authenticated. Issue tracking will fall back to file-system until authenticated.</output>
</check>
</step>

<step n="9" goal="Configure branch patterns">
<action>Explain: "Branch patterns control automatic branch and MR/PR creation when developing PRD stories. Placeholders: `{prd_key}` (e.g. `auth-refactor`), `{story_key}` (e.g. `3-4-automatic-department-routing`)."</action>

<action>Ask the user for their PRD branch pattern. Default: `feat/{prd_key}/prd`</action>
<action>Ask the user for their story branch pattern. Default: `feat/{prd_key}/{story_key}`</action>

<check if="PRD pattern does not contain `{prd_key}`">
  <output>WARN: PRD branch pattern must contain `{prd_key}` placeholder. Using default.</output>
  <action>Set PRD pattern to `feat/{prd_key}/prd`</action>
</check>

<check if="story pattern does not contain `{prd_key}` or does not contain `{story_key}`">
  <output>WARN: Story branch pattern must contain both `{prd_key}` and `{story_key}` placeholders. Using default.</output>
  <action>Set story pattern to `feat/{prd_key}/{story_key}`</action>
</check>

<action>Write `branch_patterns` under `issue_tracking` in `_bmad/custom/issue-tracking.yaml`:</action>

```yaml
issue_tracking:
  enabled: true
  platform: <platform>  # gitlab, github or openproject
  git_platform: <git_platform>  # git remote platform (same as platform in nominal case)
  host: <host>
  project: <project>  # for openproject: the OpenProject project id, quoted
  worktree_base: <configured_worktree_base>
  # Only present when git remote differs from issue tracker (always for openproject):
  # git_host: <git_hostname>
  # git_project: <git_group>/<git_project>
  # Only present when platform is openproject (written in step 7b): the `openproject:` block
  # with mcp_server, type_ids and status_ids.
  branch_patterns:
    prd: "<resolved PRD pattern>"
    story: "<resolved story pattern>"
```

<action>Verify the section was written correctly by reading it back.</action>
</step>

</task>
