# The regression gate in CI

The job installs the project, writes the Artifactory token into `~/.netrc` from a secret,
and runs the regression run with `--fail-on-gate`. Three things it needs that a laptop has:

- **The network.** The scoring service and Artifactory are reachable over Ramboll's network
  only, so the job runs on a self-hosted agent or runner inside it. A hosted runner cannot
  reach them.
- **Secrets**, stored in the CI system, never in the repository: the Artifactory token, and
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`,
  `OFFLINE_SCORING_BASE_URL`.
- **A released dataset.** A gate means something only on a `_v{M.m}` dataset. Until the
  first release, run the job without `--fail-on-gate`, and point the run at the release
  once there is one.

Run it on changes to the agent's prompts, tools and workflow, not on every commit: a run
calls the agent once per item and is billed in Langfuse units.

## Azure Pipelines

```yaml
trigger:
  branches: {include: [main]}
  paths: {include: [<agent folder>/*, evaluation/*]}

pool: <self-hosted pool inside the Ramboll network>

steps:
  - script: |
      printf 'machine artifactory.ramboll.com\n  login %s\n  password %s\n' \
        "$(ARTIFACTORY_USER)" "$(ARTIFACTORY_TOKEN)" > ~/.netrc
      chmod 600 ~/.netrc
    displayName: Artifactory credentials
  - script: |
      curl -LsSf https://astral.sh/uv/install.sh | sh
      export PATH="$HOME/.local/bin:$PATH"
      uv sync
      uv run python -m evaluation.run --fail-on-gate
    displayName: Regression evaluation
    env:
      LANGFUSE_PUBLIC_KEY: $(LANGFUSE_PUBLIC_KEY)
      LANGFUSE_SECRET_KEY: $(LANGFUSE_SECRET_KEY)
      LANGFUSE_BASE_URL: $(LANGFUSE_BASE_URL)
      OFFLINE_SCORING_BASE_URL: $(OFFLINE_SCORING_BASE_URL)
```

## GitHub Actions

```yaml
name: regression-evaluation
on:
  pull_request:
    paths: ["<agent folder>/**", "evaluation/**"]
jobs:
  evaluate:
    runs-on: [self-hosted]   # inside the Ramboll network
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - name: Artifactory credentials
        run: |
          printf 'machine artifactory.ramboll.com\n  login %s\n  password %s\n' \
            "${{ secrets.ARTIFACTORY_USER }}" "${{ secrets.ARTIFACTORY_TOKEN }}" > ~/.netrc
          chmod 600 ~/.netrc
      - name: Regression evaluation
        run: uv sync && uv run python -m evaluation.run --fail-on-gate
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
          LANGFUSE_BASE_URL: ${{ secrets.LANGFUSE_BASE_URL }}
          OFFLINE_SCORING_BASE_URL: ${{ secrets.OFFLINE_SCORING_BASE_URL }}
```

The run command prints the run's report (`eval-report`) as Markdown. To show it on the
job's summary page, write it there too:

- Azure Pipelines: `uv run eval-report evaluation/outputs/<run name> --latest 1 --output report.md`,
  then `echo "##vso[task.uploadsummary]$(pwd)/report.md"`.
- GitHub Actions: `uv run eval-report evaluation/outputs/<run name> --latest 1 >> "$GITHUB_STEP_SUMMARY"`.

Run that step even when the evaluation step failed (`condition: always()`, `if: always()`),
since a failed gate is when the report is read. The full artifacts land in
`evaluation/outputs/`; publish that folder as a build artifact when a failed gate needs
reading item by item without opening Langfuse.
