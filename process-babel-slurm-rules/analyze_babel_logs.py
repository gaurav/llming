#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["click", "tqdm"]
# ///
"""
Analyze Babel 1.15 SLURM/Snakemake log files to generate resource tuning reports.
"""

import csv
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from tqdm import tqdm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class JobEvent:
    rule_name: str
    snakemake_jobid: int
    slurm_jobid: Optional[int] = None
    sbatch_run: str = ""
    submit_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    status: str = "unknown"  # "success" | "failed" | "unknown"
    mem_mb: Optional[int] = None
    runtime_min: Optional[int] = None   # allocated
    cpus: Optional[int] = None
    log_path: Optional[str] = None
    error_type: Optional[str] = None
    error_msg: Optional[str] = None
    cpu_efficiency: Optional[float] = None
    wildcards: Optional[str] = None

    @property
    def actual_duration_min(self) -> Optional[float]:
        if self.submit_time and self.finish_time:
            return (self.finish_time - self.submit_time).total_seconds() / 60.0
        return None

    @property
    def pct_runtime_used(self) -> Optional[float]:
        dur = self.actual_duration_min
        if dur is not None and self.runtime_min:
            return 100.0 * dur / self.runtime_min
        return None


@dataclass
class SbatchRun:
    run_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_jobs: int = 0
    status: str = "unknown"  # "completed" | "failed"


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

RE_TIMESTAMP = re.compile(
    r"INFO snakemake\.logging \[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})\]:"
)
RE_RULE_SUBMIT = re.compile(
    r"INFO snakemake\.logging \[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})\]:\s+Rule:\s+(\S+),\s+Jobid:\s+(\d+)"
)
RE_SLURM_SUBMIT = re.compile(
    r"^Job (\d+) has been submitted with SLURM jobid (\d+) \(log:\s*(.+?)\)\."
)
RE_FINISHED = re.compile(
    r"INFO snakemake\.logging \[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})\]: Finished jobid:\s+(\d+)"
)
RE_ERROR = re.compile(
    r"ERROR snakemake\.logging \[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})\]: Error in rule (\S+), jobid:\s+(\d+)"
)
RE_RESOURCES = re.compile(
    r"^\s+resources:.*?mem_mb=(\d+).*?runtime=(\d+).*?cpus_per_task=(\d+)"
)
RE_WILDCARDS = re.compile(r"^\s+wildcards:\s*(.+)$")
RE_CPU_EFF = re.compile(
    r"WARNING snakemake\.logging \[.*?\]: Job (\d+)\.0 for rule '(\S+)' \(\S+\) has low CPU efficiency:\s+([\d.]+)%"
)
RE_RULE_EXCEPTION = re.compile(r"^RuleException:")
RE_EXCEPTION_CLASS = re.compile(r"^(\w+Error|\w+Exception|EOFError|JSONDecodeError|AssertionError|AttributeError|KeyError|ValueError|TypeError) in file ")
RE_EXCEPTION_MSG = re.compile(r"^(.{10,200})$")


def parse_ts(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp with timezone offset."""
    # Python 3.6 doesn't support %z with colon, handle both
    ts_str = ts_str.strip()
    try:
        return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        # Try with colon in tz offset
        ts_str2 = ts_str[:-3] + ts_str[-2:]
        return datetime.strptime(ts_str2, "%Y-%m-%dT%H:%M:%S%z")


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_sbatch_file(filepath: Path, run_name: str) -> Tuple[SbatchRun, List[JobEvent]]:
    """Parse a single sbatch .err log file."""
    run = SbatchRun(run_name=run_name)
    jobs: Dict[int, JobEvent] = {}           # snakemake_jobid -> JobEvent
    slurm_to_snake: Dict[int, int] = {}      # slurm_jobid -> snakemake_jobid

    pending_resources: Optional[dict] = None
    pending_wildcards: Optional[str] = None
    last_ts: Optional[datetime] = None

    lines = filepath.read_text(errors="replace").splitlines()

    for line in lines:
        # Track any timestamp for run start/end
        m = RE_TIMESTAMP.search(line)
        if m:
            ts = parse_ts(m.group(1))
            if run.start_time is None:
                run.start_time = ts
            last_ts = ts

        # Resources line (raw, before INFO prefix)
        m = RE_RESOURCES.match(line)
        if m:
            pending_resources = {
                "mem_mb": int(m.group(1)),
                "runtime_min": int(m.group(2)),
                "cpus": int(m.group(3)),
            }
            continue

        # Wildcards line
        m = RE_WILDCARDS.match(line)
        if m:
            pending_wildcards = m.group(1).strip()
            continue

        # Rule submit (INFO prefix version with timestamp)
        m = RE_RULE_SUBMIT.search(line)
        if m:
            ts = parse_ts(m.group(1))
            rule = m.group(2)
            jid = int(m.group(3))
            job = JobEvent(
                rule_name=rule,
                snakemake_jobid=jid,
                sbatch_run=run_name,
                submit_time=ts,
            )
            if pending_resources:
                job.mem_mb = pending_resources["mem_mb"]
                job.runtime_min = pending_resources["runtime_min"]
                job.cpus = pending_resources["cpus"]
                pending_resources = None
            if pending_wildcards:
                job.wildcards = pending_wildcards
                pending_wildcards = None
            jobs[jid] = job
            run.total_jobs += 1
            continue

        # SLURM submission
        m = RE_SLURM_SUBMIT.match(line)
        if m:
            snake_jid = int(m.group(1))
            slurm_jid = int(m.group(2))
            log_path = m.group(3).strip()
            if snake_jid in jobs:
                jobs[snake_jid].slurm_jobid = slurm_jid
                jobs[snake_jid].log_path = log_path
                slurm_to_snake[slurm_jid] = snake_jid
            continue

        # Finished jobid
        m = RE_FINISHED.search(line)
        if m:
            ts = parse_ts(m.group(1))
            jid = int(m.group(2))
            if jid in jobs:
                jobs[jid].finish_time = ts
                jobs[jid].status = "success"
            continue

        # Error in rule
        m = RE_ERROR.search(line)
        if m:
            jid = int(m.group(3))
            if jid in jobs:
                jobs[jid].status = "failed"
            continue

        # CPU efficiency warning
        m = RE_CPU_EFF.search(line)
        if m:
            slurm_jid = int(m.group(1))
            eff = float(m.group(3))
            snake_jid = slurm_to_snake.get(slurm_jid)
            if snake_jid and snake_jid in jobs:
                jobs[snake_jid].cpu_efficiency = eff
            continue

    run.end_time = last_ts

    # Determine run status: failed if any job failed
    job_list = list(jobs.values())
    if any(j.status == "failed" for j in job_list):
        run.status = "failed"
    elif job_list:
        run.status = "completed"

    return run, job_list


def parse_rule_log_file(filepath: Path) -> dict:
    """Extract error type and message from a rule-level SLURM log file."""
    try:
        lines = filepath.read_text(errors="replace").splitlines()
    except Exception:
        return {}

    result = {}
    i = 0
    while i < len(lines):
        if RE_RULE_EXCEPTION.match(lines[i]):
            # Next non-empty line should be "ExceptionClass in file ..."
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                m = RE_EXCEPTION_CLASS.match(lines[i].strip())
                if m:
                    result["error_type"] = m.group(1)
                    # Message is on the following line
                    i += 1
                    if i < len(lines) and lines[i].strip():
                        result["error_msg"] = lines[i].strip()[:300]
                    break
        i += 1
    return result


# ---------------------------------------------------------------------------
# Log directory walker
# ---------------------------------------------------------------------------

def parse_log_directory(log_dir: Path) -> Tuple[List[SbatchRun], List[JobEvent]]:
    """Parse all sbatch .err files in log_dir and enrich with rule log data."""
    sbatch_files = sorted(log_dir.glob("sbatch-babel-*.err"))
    if not sbatch_files:
        logger.warning("No sbatch .err files found in %s", log_dir)

    all_runs: List[SbatchRun] = []
    all_jobs: List[JobEvent] = []

    for sbatch_path in tqdm(sbatch_files, desc="Parsing sbatch logs", unit="file"):
        run_name = sbatch_path.stem  # e.g. "sbatch-babel-1.15-run-1"
        # Simplify to "run-N"
        m = re.search(r"(run-\d+)$", run_name)
        run_label = m.group(1) if m else run_name
        logger.info("Parsing %s as %s", sbatch_path.name, run_label)
        run, jobs = parse_sbatch_file(sbatch_path, run_label)
        all_runs.append(run)
        all_jobs.extend(jobs)

    # Enrich failed jobs with error details from rule log files
    failed_jobs = [j for j in all_jobs if j.status == "failed" and j.log_path]
    logger.info("Enriching %d failed jobs with rule log details", len(failed_jobs))

    for job in tqdm(failed_jobs, desc="Reading rule logs", unit="job"):
        if not job.log_path:
            continue
        # log_path is relative; look for it under log_dir
        # e.g. "babel_outputs/logs/rule_get_HMDB/74071.log"
        # In the data dir, it's stored as rule_get_HMDB/74071.log
        rule_dir_name = "rule_" + job.rule_name
        slurm_id = job.slurm_jobid
        if slurm_id is None:
            continue

        # Try to find the log in rule_RULENAME directory
        candidate = log_dir / rule_dir_name / f"{slurm_id}.log"
        if not candidate.exists():
            # Wildcard sub-dir: search for slurm_id.log anywhere under rule_dir
            matches = list((log_dir / rule_dir_name).glob(f"**/{slurm_id}.log")) if (log_dir / rule_dir_name).exists() else []
            candidate = matches[0] if matches else None

        if candidate and candidate.exists():
            error_info = parse_rule_log_file(candidate)
            job.error_type = error_info.get("error_type")
            job.error_msg = error_info.get("error_msg")

    return all_runs, all_jobs


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def format_duration(minutes: Optional[float]) -> str:
    if minutes is None:
        return "—"
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def format_ts(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def generate_report(
    runs: List[SbatchRun],
    jobs: List[JobEvent],
    output_dir: Path,
) -> None:
    report_path = output_dir / "report.md"
    csv_path = output_dir / "jobs.csv"

    # Index jobs by (rule_name, sbatch_run)
    jobs_by_rule: Dict[str, List[JobEvent]] = defaultdict(list)
    for j in jobs:
        jobs_by_rule[j.rule_name].append(j)

    # Build set of rules that eventually succeeded (used in failed report)
    successful_rules = {j.rule_name for j in jobs if j.status == "success"}

    # ---------------------------------------------------------------------------
    # Write jobs.csv
    # ---------------------------------------------------------------------------
    csv_field_names = [
        "sbatch_run", "rule_name", "snakemake_jobid", "slurm_jobid",
        "submit_time", "finish_time", "status",
        "mem_mb", "runtime_min", "cpus", "wildcards",
        "actual_duration_min", "pct_runtime_used",
        "cpu_efficiency", "error_type", "error_msg", "log_path",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_field_names)
        writer.writeheader()
        for j in sorted(jobs, key=lambda x: (x.sbatch_run, x.snakemake_jobid)):
            writer.writerow({
                "sbatch_run": j.sbatch_run,
                "rule_name": j.rule_name,
                "snakemake_jobid": j.snakemake_jobid,
                "slurm_jobid": j.slurm_jobid or "",
                "submit_time": format_ts(j.submit_time),
                "finish_time": format_ts(j.finish_time),
                "status": j.status,
                "mem_mb": j.mem_mb or "",
                "runtime_min": j.runtime_min or "",
                "cpus": j.cpus or "",
                "wildcards": j.wildcards or "",
                "actual_duration_min": f"{j.actual_duration_min:.1f}" if j.actual_duration_min is not None else "",
                "pct_runtime_used": f"{j.pct_runtime_used:.1f}" if j.pct_runtime_used is not None else "",
                "cpu_efficiency": f"{j.cpu_efficiency:.1f}" if j.cpu_efficiency is not None else "",
                "error_type": j.error_type or "",
                "error_msg": j.error_msg or "",
                "log_path": j.log_path or "",
            })
    logger.info("Wrote %s", csv_path)

    # ---------------------------------------------------------------------------
    # Write report.md
    # ---------------------------------------------------------------------------
    lines: List[str] = []
    lines.append("# Babel 1.15 SLURM Run Analysis Report\n")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    lines.append("")

    # --- Section 1: Run Summary ---
    lines.append("## 1. Run Summary\n")
    lines.append("| Run | Start | End | Duration | Total Jobs | Succeeded | Failed | Status |")
    lines.append("|-----|-------|-----|----------|------------|-----------|--------|--------|")

    for run in sorted(runs, key=lambda r: r.run_name):
        run_jobs = [j for j in jobs if j.sbatch_run == run.run_name]
        n_success = sum(1 for j in run_jobs if j.status == "success")
        n_failed = sum(1 for j in run_jobs if j.status == "failed")
        dur = None
        if run.start_time and run.end_time:
            dur = (run.end_time - run.start_time).total_seconds() / 60.0
        status_icon = "✓" if run.status == "completed" else "✗"
        lines.append(
            f"| {run.run_name} | {format_ts(run.start_time)} | {format_ts(run.end_time)} "
            f"| {format_duration(dur)} | {run.total_jobs} | {n_success} | {n_failed} | {status_icon} {run.status} |"
        )
    lines.append("")

    # --- Section 2: Failed Rules Report ---
    lines.append("## 2. Failed Rules Report\n")
    failed_jobs = [j for j in jobs if j.status == "failed"]

    if not failed_jobs:
        lines.append("No failed jobs found.\n")
    else:
        lines.append("| Rule | Run | SLURM Job ID | Error Type | Error Message | Eventually Succeeded? |")
        lines.append("|------|-----|--------------|------------|---------------|----------------------|")
        for j in sorted(failed_jobs, key=lambda x: (x.rule_name, x.sbatch_run)):
            later_success = "Yes" if j.rule_name in successful_rules else "No"
            err_type = j.error_type or "—"
            err_msg = (j.error_msg or "—")[:80].replace("|", "\\|")
            slurm_id = str(j.slurm_jobid) if j.slurm_jobid else "—"
            lines.append(
                f"| {j.rule_name} | {j.sbatch_run} | {slurm_id} "
                f"| {err_type} | {err_msg} | {later_success} |"
            )
    lines.append("")

    # --- Section 3: Job Timing Report ---
    lines.append("## 3. Job Timing Report\n")
    lines.append(
        "*Jobs where actual duration was >90% of allocated runtime are marked **⚠ UNDER** "
        "(may need more); <10% are marked **💤 OVER** (may be over-provisioned).*\n"
    )
    lines.append("| Rule | Run | Wildcards | Allocated (min) | Actual (min) | % Used | Status |")
    lines.append("|------|-----|-----------|-----------------|--------------|--------|--------|")

    timed_jobs = [j for j in jobs if j.actual_duration_min is not None and j.runtime_min]
    for j in sorted(timed_jobs, key=lambda x: -(x.pct_runtime_used or 0)):
        pct = j.pct_runtime_used
        flag = ""
        if pct is not None:
            if pct > 90:
                flag = " ⚠ UNDER"
            elif pct < 10:
                flag = " 💤 OVER"
        wc = j.wildcards or ""
        lines.append(
            f"| {j.rule_name} | {j.sbatch_run} | {wc} "
            f"| {j.runtime_min} | {j.actual_duration_min:.1f} "
            f"| {pct:.1f}%{flag} | {j.status} |"
        )
    lines.append("")

    # --- Section 4: CPU Efficiency Report ---
    lines.append("## 4. CPU Efficiency Report\n")
    lines.append("*Jobs where SLURM reported low CPU efficiency.*\n")

    low_eff_jobs = [j for j in jobs if j.cpu_efficiency is not None]
    if not low_eff_jobs:
        lines.append("No CPU efficiency warnings found.\n")
    else:
        # Group by rule
        by_rule: Dict[str, List[JobEvent]] = defaultdict(list)
        for j in low_eff_jobs:
            by_rule[j.rule_name].append(j)

        lines.append("| Rule | Run | SLURM Job ID | CPU Efficiency | Allocated CPUs |")
        lines.append("|------|-----|--------------|----------------|----------------|")
        for rule in sorted(by_rule):
            for j in sorted(by_rule[rule], key=lambda x: x.sbatch_run):
                slurm_id = str(j.slurm_jobid) if j.slurm_jobid else "—"
                lines.append(
                    f"| {rule} | {j.sbatch_run} | {slurm_id} "
                    f"| {j.cpu_efficiency:.1f}% | {j.cpus or '—'} |"
                )
    lines.append("")

    # --- Section 5: Rules Needing Retries ---
    lines.append("## 5. Rules Needing Retries\n")
    lines.append("*Rules that ran in multiple sbatch runs (indicating earlier failures).*\n")

    multi_run_rules = {
        rule: rule_jobs
        for rule, rule_jobs in jobs_by_rule.items()
        if len({j.sbatch_run for j in rule_jobs}) > 1
    }

    if not multi_run_rules:
        lines.append("No rules required retries across runs.\n")
    else:
        lines.append("| Rule | Runs | Final Status |")
        lines.append("|------|------|--------------|")
        for rule in sorted(multi_run_rules):
            rule_jobs = multi_run_rules[rule]
            runs_seen = sorted({j.sbatch_run for j in rule_jobs})
            final_status = "success" if any(j.status == "success" for j in rule_jobs) else "failed"
            lines.append(f"| {rule} | {', '.join(runs_seen)} | {final_status} |")
    lines.append("")

    # --- Section 6: Logging Improvement Suggestions ---
    lines.append("## 6. Logging Improvement Suggestions\n")
    lines.append(
        "The following improvements to the Babel pipeline would make future log analysis "
        "significantly easier:\n"
    )
    suggestions = [
        (
            "Add `onsuccess`/`onerror` Snakemake hooks",
            "Add `onsuccess` and `onerror` hooks to the main Snakefile that write a structured "
            "`run_summary.json` file listing failed rules, total job counts, and run duration. "
            "This eliminates the need to parse unstructured logs for basic run statistics.",
        ),
        (
            "Explicit resource declarations in snakefiles",
            "Currently, resources come from a SLURM profile rather than individual rule "
            "declarations. Adding `resources: mem_mb=..., runtime=...` directly to each rule "
            "in `data/src/snakefiles/*.snakefile` makes resource tuning visible in code review "
            "and auditable. It also enables per-rule tuning based on observed actual usage.",
        ),
        (
            "Post-job `sacct` capture for actual memory/CPU usage",
            "Wrap SLURM job scripts to run "
            "`sacct -j $SLURM_JOB_ID --format=MaxRSS,Elapsed,CPUTimeRAW -n` on completion "
            "and append actual resource usage to the rule's log file. This enables true memory "
            "utilization analysis (currently impossible from these logs alone).",
        ),
        (
            "Log output file sizes at rule completion",
            "Add a `shell` snippet or Python statement at the end of each rule to log the sizes "
            "of key output files. This catches silent failures (0-byte or truncated outputs) "
            "before downstream rules consume bad data.",
        ),
        (
            "Timestamp rule log completion explicitly",
            "Rule log files currently only contain failure timestamps; success is only recorded "
            "in the sbatch controller log. Adding an explicit completion line to each rule "
            "(e.g., via a Snakemake wrapper script) would make rule logs self-contained and "
            "simplify per-rule duration analysis.",
        ),
    ]
    for i, (title, body) in enumerate(suggestions, 1):
        lines.append(f"### 6.{i} {title}\n")
        lines.append(body + "\n")

    report_path.write_text("\n".join(lines))
    logger.info("Wrote %s", report_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.argument(
    "log_dir",
    default="data/babel-1.15-2025dec12",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output-dir", "-o",
    default="data",
    type=click.Path(file_okay=False, path_type=Path),
    show_default=True,
    help="Directory to write report.md and jobs.csv.",
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    show_default=True,
    help="Logging verbosity.",
)
def main(log_dir: Path, output_dir: Path, log_level: str) -> None:
    """Analyze Babel 1.15 SLURM log files and generate resource-tuning reports.

    LOG_DIR: Directory containing sbatch-babel-*.err files and rule_* subdirectories.
    Defaults to data/babel-1.15-2025dec12.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    log_dir = log_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Log directory: %s", log_dir)
    logger.info("Output directory: %s", output_dir)

    runs, jobs = parse_log_directory(log_dir)

    logger.info(
        "Parsed %d runs, %d total job events (%d success, %d failed, %d unknown)",
        len(runs),
        len(jobs),
        sum(1 for j in jobs if j.status == "success"),
        sum(1 for j in jobs if j.status == "failed"),
        sum(1 for j in jobs if j.status == "unknown"),
    )

    generate_report(runs, jobs, output_dir)

    print(f"\nReports written to: {output_dir}")
    print(f"  - {output_dir / 'report.md'}")
    print(f"  - {output_dir / 'jobs.csv'}")


if __name__ == "__main__":
    main()
