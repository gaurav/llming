# process-babel-slurm-rules

This directory contains log files and an analysis script for Babel 1.15 bioinformatics pipeline runs on a SLURM HPC cluster using Snakemake.

## Script: `analyze_babel_logs.py`

Parses Snakemake/SLURM log files from the Babel 1.15 pipeline runs (Dec 2025) and generates:
- **`data/report.md`** — Markdown report with run summary, failed rules, job timing, CPU efficiency, retry analysis, and improvement suggestions.
- **`data/jobs.csv`** — One row per job execution with all parsed fields.

### Usage

```bash
cd process-babel-slurm-rules
uv run analyze_babel_logs.py data/babel-1.15-2025dec12 2>&1 | tee data/last-run.log
```

Or with custom options:

```bash
uv run analyze_babel_logs.py [LOG_DIR] --output-dir data/ --log-level INFO
```

- `LOG_DIR`: Directory with `sbatch-babel-*.err` files and `rule_*` subdirectories.
  Defaults to `data/babel-1.15-2025dec12`.
- `--output-dir` / `-o`: Output directory for reports. Defaults to `data/`.
- `--log-level`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`. Defaults to `INFO`.

### Log File Sources

**`sbatch-babel-1.15-run-N.err`** — Main Snakemake controller logs (one per sbatch run):
- Job submit/finish/error events with timestamps
- Resource allocations (`mem_mb`, `runtime`, `cpus_per_task`)
- SLURM job IDs and log paths
- CPU efficiency warnings

**`rule_RULENAME/SLURM_JOBID.log`** — Per-job execution logs:
- Detailed exception tracebacks on failure
- Error type (e.g., `HTTPError`, `EOFError`, `AssertionError`)

### Report Sections

1. **Run Summary** — Start/end time, duration, job counts per sbatch run
2. **Failed Rules** — Failed jobs with error type and whether they later succeeded
3. **Job Timing** — Allocated vs. actual runtime, flagging under/over-provisioned jobs
4. **CPU Efficiency** — SLURM efficiency warnings grouped by rule
5. **Rules Needing Retries** — Rules that ran across multiple sbatch runs
6. **Logging Improvement Suggestions** — Actionable recommendations

### Dependencies

Managed inline via `uv` script metadata:
- `click` — CLI
- `tqdm` — Progress bars

All parsing uses the Python standard library (`re`, `pathlib`, `datetime`, `csv`, `collections`, `dataclasses`).
