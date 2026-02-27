# process-babel-slurm-rules

Analyzes log files from Babel bioinformatics pipeline runs on a SLURM HPC cluster (via Snakemake) and generates reports for tuning resource declarations and understanding pipeline reliability.

## Quick start

```bash
cd process-babel-slurm-rules
uv run analyze_babel_logs.py path/to/logs --output-dir results/babel-1.15-2025dec12 2>&1 | tee results/babel-1.15-2025dec12/last-run.log
```

## Expected input layout

The script expects a single directory containing two types of log files produced by a Snakemake + SLURM run:

```
babel-1.15-2025dec12/
├── sbatch-babel-1.15-run-1.err      # Snakemake controller log, run 1
├── sbatch-babel-1.15-run-2.err      # Snakemake controller log, run 2
├── ...                               # one .err file per sbatch invocation
├── rule_get_HMDB/
│   └── 74071.log                    # per-job SLURM execution log
├── rule_get_ensembl/
│   └── 74085.log
└── ...                               # one rule_RULENAME/ dir per rule
```

### `sbatch-babel-*.err` — Snakemake controller logs

One file per `sbatch` invocation (a pipeline may need several if earlier runs fail). Each file contains:

- **Job submissions** — rule name, Snakemake job ID, allocated resources (`mem_mb`, `runtime` in minutes, `cpus_per_task`), and the SLURM job ID assigned
- **Completions** — finish timestamp per job ID
- **Failures** — error notice per rule at exit
- **CPU efficiency warnings** — SLURM's post-job efficiency report, e.g. `Job 74503.0 for rule 'rule_generate_pubmed_compendia' has low CPU efficiency: 0.0%`

Key line patterns the parser looks for:

```
INFO snakemake.logging [2025-12-08T21:09:28+0000]:  Rule: get_HMDB, Jobid: 36
    resources: mem_mb=64000, disk_mb=50000, runtime=120, cpus_per_task=4
Job 36 has been submitted with SLURM jobid 74071 (log: babel_outputs/logs/rule_get_HMDB/74071.log).
INFO snakemake.logging [2025-12-08T21:10:02+0000]: Finished jobid: 36 (Rule: get_HMDB)
ERROR snakemake.logging [2025-12-09T20:54:10+0000]: Error in rule get_HMDB, jobid: 36
WARNING snakemake.logging [2025-12-09T20:54:10+0000]: Job 74071.0 for rule 'rule_get_HMDB' (python) has low CPU efficiency: 0.0%.
```

### `rule_RULENAME/SLURM_JOBID.log` — per-job execution logs

One file per SLURM job, nested under a directory named after the rule. For rules with Snakemake wildcards (e.g. `export_compendia_to_duckdb` with `filename=GeneFamily`), there may be a wildcard-value subdirectory:

```
rule_export_compendia_to_duckdb/
└── GeneFamily/
    └── 74219.log
```

These logs are only parsed when a job fails. The parser looks for `RuleException:` followed by the error class and message:

```
RuleException:
HTTPError in file ".../datacollect.snakefile", line 630:
HTTP Error 504: Gateway Time-out
```

Common error types seen in practice: `HTTPError`, `EOFError` (corrupt gzip), `JSONDecodeError`, `AssertionError`, `RuntimeError`, `_BiomartException`, `ConnectionError`.

## Running the script

```
uv run analyze_babel_logs.py [LOG_DIR] [--output-dir DIR] [--log-level LEVEL]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `LOG_DIR` | `data/babel-1.15-2025dec12` | Directory containing `sbatch-babel-*.err` files and `rule_*` subdirectories |
| `--output-dir` / `-o` | `data/` | Where to write `report.md` and `jobs.csv` |
| `--log-level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

### Recommended output layout

Store results under `results/` using the Babel run date or version as the subdirectory name so multiple runs can coexist:

```bash
# By date
uv run analyze_babel_logs.py /path/to/logs/babel-1.15-2025dec12 \
    --output-dir results/babel-1.15-2025dec12 \
    2>&1 | tee results/babel-1.15-2025dec12/last-run.log

# By version
uv run analyze_babel_logs.py /path/to/logs/babel-1.16 \
    --output-dir results/babel-1.16 \
    2>&1 | tee results/babel-1.16/last-run.log
```

This produces:

```
results/
└── babel-1.15-2025dec12/
    ├── report.md        # full analysis (see sections below)
    ├── jobs.csv         # one row per job execution
    └── last-run.log     # console output from the script run
```

## Output: `report.md`

Six sections:

1. **Run Summary** — start/end time, duration, and job counts (total / succeeded / failed) for each `sbatch` run
2. **Failed Rules** — every failed job with its SLURM job ID, error type, error message excerpt, and whether the rule eventually succeeded in a later run
3. **Job Timing** — actual wall-clock duration vs. allocated runtime for every completed job, sorted by % of allocation used; jobs using >90% are flagged ⚠ UNDER (may need more), jobs using <10% are flagged 💤 OVER (may be over-provisioned)
4. **CPU Efficiency** — all SLURM low-efficiency warnings, grouped by rule
5. **Rules Needing Retries** — rules that appeared in more than one sbatch run, with their final outcome
6. **Logging Improvement Suggestions** — actionable recommendations for making future runs easier to analyze (adding `onsuccess`/`onerror` hooks, per-rule resource declarations, `sacct` capture, output file size logging, etc.)

## Output: `jobs.csv`

One row per job execution with these columns:

| Column | Description |
|--------|-------------|
| `sbatch_run` | Which run this job belongs to (e.g. `run-1`) |
| `rule_name` | Snakemake rule name |
| `snakemake_jobid` | Internal Snakemake job ID |
| `slurm_jobid` | SLURM job ID |
| `submit_time` | When the job was submitted |
| `finish_time` | When the job finished (blank if failed before finishing) |
| `status` | `success`, `failed`, or `unknown` |
| `mem_mb` | Allocated memory in MB |
| `runtime_min` | Allocated runtime in minutes |
| `cpus` | Allocated CPU count |
| `wildcards` | Snakemake wildcard values (if any) |
| `actual_duration_min` | Wall-clock minutes from submit to finish |
| `pct_runtime_used` | `actual_duration_min / runtime_min × 100` |
| `cpu_efficiency` | CPU efficiency % from SLURM warning (if flagged) |
| `error_type` | Exception class from rule log (if failed) |
| `error_msg` | First line of error message (if failed) |
| `log_path` | Path to the rule's SLURM log file |

## Dependencies

`uv` handles dependencies automatically via inline script metadata. No separate install step needed. Requires Python ≥ 3.8 and [`uv`](https://docs.astral.sh/uv/).

External packages: `click`, `tqdm`. Everything else uses the Python standard library.
