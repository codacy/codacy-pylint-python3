[![Codacy Badge](https://api.codacy.com/project/badge/Grade/a22666a62ace46ff8c98f5575a7c87e4)](https://www.codacy.com/gh/codacy/codacy-pylint-python3?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=codacy/codacy-pylint-python3&amp;utm_campaign=Badge_Grade)
[![Build Status](https://circleci.com/gh/codacy/codacy-pylint.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/codacy/codacy-pylint)

# Codacy Pylint for Python 3

This is the docker engine we use at Codacy to have [Pylint](http://www.pylint.org/) support.
You can also create a docker to integrate the tool and language of your choice!
See the [codacy-engine-scala-seed](https://github.com/codacy/codacy-engine-scala-seed) repository for more information.

## Usage

You can create the docker by doing:

  ```bash
  docker build -t codacy-pylint-python3:latest .
  ```

The docker is ran with the following command:

  ```bash
  docker run -it -v $srcDir:/src codacy-pylint-python3:latest
  ```

## Generate Docs

 1. Update the version in `docs/patterns.json`
 2. Run the DocGenerator:

```bash
sbt "doc-generator/run"
```

## Test

We use the [codacy-plugins-test](https://github.com/codacy/codacy-plugins-test) to test our external tools integration.
You can follow the instructions there to make sure your tool is working as expected.

## Agent Playbook: Updating This Repository End-to-End

This section is written for an AI coding agent (or a human) tasked with updating this repo — most commonly bumping the wrapped Pylint version, but also base image / dependency bumps. Follow it top to bottom; it tells you what to change, how to regenerate derived files, how to test locally, and how to interpret CI so you can iterate on failures without guessing.

### 1. What this repository is

This is a **Codacy engine**: a small Python program (`src/codacy_pylint.py`, run directly as the Docker `ENTRYPOINT`/`CMD` — there is no Scala runtime engine class here) that packages [Pylint](https://pylint.org/) as a Docker image Codacy's platform can run against a customer's Python source code. Dependencies (`pylint`, `Django`/`Flask` plugins used to exercise framework-aware checks, etc.) are installed via `pip` from `requirements.txt` into a `python:3.14-alpine3.23` base image (see `Dockerfile`).

There is a **separate, small Scala/sbt subproject** (`doc-generator/`, built with sbt 1.11.6 per `project/build.properties`) whose only job is to regenerate the `docs/` directory — it is not part of the shipped engine image. `docs/` is machine-consumed configuration, not just documentation:

- `docs/patterns.json` — the full list of Pylint rules ("patterns") Codacy knows about, their category/level/parameters/defaults, and which are enabled out of the box. Generated file, do not hand-edit.
- `docs/description/description.json` + `docs/description/*.md` — human-readable titles/descriptions per pattern, used in the Codacy UI. Generated file, do not hand-edit.
- `docs/tests/*.py` and `docs/multiple-tests/*` — fixtures used by `codacy-plugins-test` to validate the engine actually produces the results it claims to for real code samples.
- `docs/tool-description.md` — short blurb about the tool, hand-maintained.

All three generated artifacts above come from **`doc-generator/src/main/scala/codacy/pylint/Main.scala`**, which reads the pinned `pylint==<version>` from `requirements.txt`, then scrapes `https://pylint.pycqa.org/en/v<version>/user_guide/checkers/features.html` (via `scala-scraper`) for the rule list and converts each rule's HTML description to Markdown via `pandoc`. This means the generator needs **network access**, and **`pandoc`** installed locally (it also hardcodes a small blacklist of rules, a set of "enabled by default" pattern IDs, and per-rule parameter definitions directly in the Scala source — review these when rules are added/removed/renamed upstream).

### 2. Files that encode versions — check all of these on every update

| File | What it controls | What to check |
|---|---|---|
| `requirements.txt` → `pylint==` | The Pylint release bundled in the image, and the exact version `doc-generator/Main.scala` scrapes docs for | Bump to the target version. Confirm `https://pylint.pycqa.org/en/v<version>/user_guide/checkers/features.html` exists upstream before regenerating docs. |
| `requirements.txt` → `Django==`, `Flask==`, `pylint-django==`, `jsonpickle==`, `asttokens==`, etc. | Framework/runtime deps used by the plugin checkers and by `codacy_pylint.py` itself | Prior bump commits (e.g. `fa898a0`, the `bump-pylint-v4` PR) bump these alongside pylint in the same commit — check for newer compatible releases and CVEs (dependabot also opens PRs for these individually). |
| `Dockerfile` → base image (`python:3.14-alpine3.23`) | Python runtime/OS the packaged app runs on | Historically bumped in lockstep with the pylint version (see git history) even when not strictly required — verify the new Pylint version still supports the Python version in the base image. |
| `.circleci/config.yml` → `codacy/base` orb, `codacy/plugins-test` orb | Shared CircleCI steps (checkout/version, sbt build, docker build/publish, tagging) and the `codacy-plugins-test` runner | Check the latest published orb versions; not usually tied to a Pylint bump specifically. |
| `project/build.properties` / `project/plugins.sbt` | sbt version / `codacy-sbt-plugin` version used only to build `doc-generator` | Rarely needs touching; check only if the doc-generator build itself fails to load. |
| `src/codacy_pylint.py` | Engine glue code (reads Codacy's config JSON, builds the `pylintrc`, invokes `pylint`) | Not version-pinned, but past bumps have needed small compatibility fixes here (e.g. `e5b9687` changed a `'patterns' in tools[0]` truthiness check) when the upstream config-reading contract shifted — read it and diff behavior if the new Pylint version changes CLI/config semantics. |

### 3. Step-by-step update procedure

1. **Bump `pylint==` (and compatible companion packages)** in `requirements.txt`, and the base image tag in `Dockerfile` if warranted.
2. **Regenerate the docs.** Requires `pandoc` on `PATH` and network access: `sbt "doc-generator/run"`. This overwrites `docs/patterns.json` and `docs/description/*`; review the diff for new/removed/renamed rules, changed defaults, and stale fixtures under `docs/tests/`/`docs/multiple-tests/`.
3. **Format/compile the Scala doc-generator** if you touched `Main.scala`: `sbt "scalafmt::test; sbt:scalafmt::test"` (CI job `check_scalafmt` runs this).
4. **Build the Docker image and run the built-in smoke test**: `docker build -t codacy-pylint-python3:latest . && docker run --rm codacy-pylint-python3:latest codacy_pylint_test.py`.
5. **Run `codacy-plugins-test` locally** before pushing — clone https://github.com/codacy/codacy-plugins-test and run its DockerTest commands (this repo's CI runs it with `run_multiple_tests: true`, i.e. both the single-pattern tests under `docs/tests/` and the `docs/multiple-tests/*` scenarios) against your local image tag.
6. **Iterate on failures**, re-running only the relevant test command after each fix.
7. **Commit** the version bump(s) together with the regenerated `docs/` files (and any `src/codacy_pylint.py` compatibility fixes) in one change.
8. **Push and open a PR.** CI (`.circleci/config.yml`) runs `checkout_and_version` -> `check_scalafmt` -> `generate_docs` (regenerates docs in CI too, requires pandoc) -> `build_docker_and_test` -> `plugins_test` -> `publish_docker` (master only) -> `tag_version`.
9. **Poll the PR's real CI checks until they all pass — local validation is NOT the finish line.** After every push, run `gh pr checks <pr-url>` and keep re-polling (short sleep while any check is `pending`) until all checks finish. If a check fails, fetch its actual log (the CircleCI job's log — don't guess), find the true root cause, fix it, push again (never `--no-verify`, never force-push), and re-poll. Repeat until every check is green. **The CI environment's toolchain can differ from your local one** (CI's `generate_docs` job re-scrapes Pylint's live docs site and re-runs pandoc — if that output differs from what you committed locally, the diff will show up as an unexpected change in a later job), so a clean local run does not guarantee CI passes. Only stop iterating when every check passes, or you hit a genuine product/infra decision that needs a human — in which case explain it in the PR rather than guessing.

### 4. Common failure modes and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `generate_docs` / local `sbt "doc-generator/run"` produces a huge unrelated diff | Pylint's docs site restructured its checker sections between versions | Compare `#...-checker-messages` anchor IDs in `Main.scala` against the new version's `features.html`; add/remove/rename anchors as needed |
| `codacy_pylint_test.py` fails in `build_docker_and_test` | Engine glue code assumption broken by the new Pylint CLI/config format | Diff Pylint's release notes for CLI/config changes; patch `src/codacy_pylint.py` accordingly (see the `e5b9687` precedent) |
| `plugins_test` fails on a specific fixture under `docs/tests/` or `docs/multiple-tests/` | Rule renamed/removed/added upstream, or its message/output format changed | Regenerate docs, and update the expected fixture output to match the new (verified correct) behavior |
| CI `publish_docker`/`tag_version` don't run on your branch | Expected — gated to the default branch only | Nothing to fix |

### 5. Definition of done

- Version bump(s) reflected in all files that encode them (`requirements.txt`, `Dockerfile`, and CI config if applicable).
- Generated docs (`docs/patterns.json`, `docs/description/*`) regenerated and committed, with fixture inconsistencies resolved.
- `src/codacy_pylint.py` updated if the new Pylint version changed CLI/config behavior it depends on.
- Docker image builds successfully and the built-in `codacy_pylint_test.py` smoke test passes.
- `codacy-plugins-test` commands all pass locally against the freshly built image.
- **After pushing and opening/updating the PR, every CI check on it is green.** Poll `gh pr checks <pr-url>` and iterate on any failure (fetch the real CI log, fix, push, re-poll) until all pass — a passing local build is not sufficient, because the CI toolchain can differ from your local one (see step 9).

## What is Codacy?

[Codacy](https://www.codacy.com/) is an Automated Code Review Tool that monitors your technical debt, helps you improve your code quality, teaches best practices to your developers, and helps you save time in Code Reviews.

### Among Codacy’s features

- Identify new Static Analysis issues
- Commit and Pull Request Analysis with GitHub, BitBucket/Stash, GitLab (and also direct git repositories)
- Auto-comments on Commits and Pull Requests
- Integrations with Slack, HipChat, Jira, YouTrack
- Track issues in Code Style, Security, Error Proneness, Performance, Unused Code and other categories

Codacy also helps keep track of Code Coverage, Code Duplication, and Code Complexity.

Codacy supports PHP, Python, Ruby, Java, JavaScript, and Scala, among others.

### Free for Open Source

Codacy is free for Open Source projects.
