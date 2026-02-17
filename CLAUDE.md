# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python 3.12+ CLI tool to filter and extract error-related entries from Project Zomboid server log files. The tool parses verbose log files (typically 1.5MB-2MB) and distills them into a concise report containing only ERROR/WARN entries and LOG entries containing error-related keywords.

## Development Commands

### Running the Tool

```bash
# Using Python directly
python main.py <log_file_path> [options]

# Examples
python main.py log_example1.txt
python main.py log_example1.txt -o filtered_errors.txt
python main.py console.txt --keywords "custom,keyword"
```

### Environment Setup

```bash
# The project uses a virtual environment located at .venv/
# Python 3.12+ is required (specified in pyproject.toml)

# To activate the virtual environment (Windows)
.venv\Scripts\activate
```

## Architecture

### Core Components

**main.py** - Single-file application containing:

- `parse_log_file()` - Streaming parser that reads log files line-by-line and extracts entries. Entries are detected by pattern `^(LOG|WARN|ERROR):` and accumulated until the next entry start.

- `should_include_entry()` - Filter logic that:
  - Always includes ERROR and WARN type entries
  - Includes LOG entries containing keywords: "error", "warning", "err", "warn" (case-insensitive)
  - Supports additional user-provided keywords via `--keywords`

- `extract_timestamp_and_body()` - Normalizes entries by extracting timestamps (pattern `t:<timestamp>>`) and generating a clean body for deduplication.

- `deduplicate_entries()` - Removes duplicates based on message body (excluding timestamp), preserving original order and aggregating timestamps to show occurrence ranges.

- `generate_report()` - Outputs formatted report with header, entry count, and timestamp ranges (e.g., `1771295104050 ~ 1771295105000 (x5)`)

### Log Entry Format

Entries begin with type keywords:
```
LOG  : General      f:0, t:1771295104050> message
WARN : Category     f:0, t:1771295104050> message
ERROR: General      f:0, t:1771295219628> Exception thrown
        stack trace lines...
```

Multi-line entries continue until the next type keyword line.

### Deduplication Strategy

The tool uses the message body (excluding the timestamp) as a deduplication key. When duplicates are found, timestamps are aggregated to show occurrence ranges in the output report.

## Output Format

Default output filename: `{input_filename}_errors.txt`

Report structure:
```
=== Project Zomboid Server Log Filter Report ===
Source: {filename}
Generated: {timestamp}
Unique entries found: {count}

--- Entry 1 ---
Timestamp: 1771295219628 ~ 1771295231387 (x2)
ERROR : General> Exception thrown
    ...
```
