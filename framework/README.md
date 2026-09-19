# IntelliX framework kernel

This directory is the executable, vendor-neutral engineering contract.

## Start a project

1. Copy `templates/PROJECT.yaml` to `intellix.yaml` and configure it.
2. From the framework repository, install the pinned kernel snapshot:
   `python3 framework/sync.py --source-root . --target-root /path/to/project`.
3. Generate short entry-point adapters with
   `python3 framework/generate_adapters.py --source-root . --target-root /path/to/project`.
4. Create product, architecture, SPEC and ADR artifacts referenced by the project.
5. Copy `templates/TASK.yaml` to `tasks/TASK-NNN.yaml` for each unit of work.
6. Validate in the project with `python3 framework/validate.py --root . --all`.

Every project declares both a business `project.profile` and a required
`project.governance_profile` (`micro`, `standard` or `regulated`). Governance
profile gates are defined by `framework/framework.yaml` and are added to, never
substituted for, the minimum gates derived from task risk.

`intellix.lock.json` is generated, not manually edited. It pins the framework
version, source, normative file manifest and SHA-256 digest. Use `sync.py --check`
to detect missing, stale or modified snapshots without writing. Synchronization is
one-way from the framework repository to the project; it never imports project
files back into the framework source.

The digest covers the normative kernel, not the copied control-plane validator.
Running the copied `framework/validate.py` is an operational consistency check,
not a tamper-proof security boundary. Authoritative evidence must run the validator
from an intact reviewed framework source (or CI revision) against the explicit
client root, for example:
`python3 /trusted/intellix-plugin/framework/validate.py --root /path/to/project --all`.

## Exact-revision CI evidence

Configure `quality.ci.repository` and `quality.ci.required_checks` in
`intellix.yaml`, then query GitHub for the full reviewed commit SHA:

```bash
GITHUB_TOKEN=... python3 framework/ci.py \
  --root . \
  --revision 0123456789abcdef0123456789abcdef01234567 \
  --output .intellix/runtime/ci/TASK-NNN.json
```

The token is read only from the named environment variable and is never written
to evidence. Missing, stale, incomplete, failed, malformed, unauthorized or
unavailable results fail closed. The output is a local audit copy of a GitHub API
query; hand-authored JSON and model statements are not authoritative evidence.
CI success does not satisfy the human gate. Without a protected approval from a
separately credentialed external identity, merge eligibility remains blocked.

## Validate

```bash
python3 framework/validate.py --root . --framework
python3 framework/validate.py --root . --project intellix.yaml
python3 framework/validate.py --root . --task tasks/TASK-001.yaml
python3 framework/validate.py --root . --tasks-dir tasks
python3 framework/sync.py --source-root /path/to/framework-repo --target-root . --check
python3 framework/ci.py --root . --revision <full-commit-sha>
```

The `.yaml` contracts use JSON-compatible YAML deliberately, so the validator
has no third-party dependency. Unknown fields fail closed. See
`docs/architecture/MULTIAGENT-FRAMEWORK.md` for the operating model and
`docs/MULTIAGENT-FRAMEWORK-MIGRATION.md` for incremental adoption.
