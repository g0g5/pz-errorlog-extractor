# Project Zomboid Server Log Filter - Specification

## Overview
A Python tool to filter and extract error-related entries from verbose Project Zomboid server log files (typically 1.5MB-2MB). The tool distills the log into a concise report containing only relevant error/warning entries.

## Log Entry Format

### Entry Types
Entries begin with one of three type keywords:
- `LOG` - General log messages
- `WARN` - Warning messages
- `ERROR` - Error messages

### Entry Structure

**Single-line entry:**
```
LOG  : General      f:0, t:1771295104050> ERROR: mods isn't a valid workshop item ID
```

**Multi-line entry:**
```
ERROR: General      f:0, t:1771295219628> ExceptionLogger.logException> Exception thrown
	java.lang.Exception: Fluid not found: Alcohol. line: fluid 0.1 [Alcohol] at InputScript.OnPostWorldDictionaryInit(InputScript.java:965).
	Stack trace:
		zombie.scripting.entity.components.crafting.InputScript.OnPostWorldDictionaryInit(InputScript.java:965)
```

An entry begins with a type keyword and ends before the next type keyword line.

## Filtering Rules

### Include Criteria
Extract entries matching ANY of the following:

1. **Type-based inclusion:**
   - Entries with type `ERROR`
   - Entries with type `WARN`

2. **Content-based inclusion (for LOG type only):**
   - LOG entries containing any of these keywords (case-insensitive):
     - `error`
     - `warning`
     - `err`
     - `warn`

### Deduplication
- Identical entries (exact match after stripping whitespace) should be deduplicated
- Only unique entries should appear in the output

## Output Format

### Output File
- Format: Plain text file
- Naming: `{input_filename}_errors.txt` (or user-specified)
- Encoding: UTF-8

### Output Structure
```
=== Project Zomboid Server Log Filter Report ===
Source: {filename}
Generated: {timestamp}
Total entries found: {count}

--- Entry 1 ---
[Entry content]

--- Entry 2 ---
[Entry content]
...
```

## CLI Interface

### Command Line Arguments
```
python main.py <log_file_path> [options]
```

### Options
- `log_file_path` (required): Path to the Project Zomboid server log file
- `-o, --output` (optional): Output file path (default: `{input}_errors.txt`)
- `--keywords` (optional): Additional keywords to filter (comma-separated)

### Example Usage
```bash
python main.py server_logs.txt
python main.py server_logs.txt -o filtered_errors.txt
```

## Implementation Notes

### Parsing Strategy
1. Read log file line by line
2. Detect entry start by matching type keywords at line beginning: `^(LOG|WARN|ERROR):`
3. Accumulate lines until next entry start or EOF
4. Apply filtering criteria to complete entry
5. Store unique entries (using content hash for deduplication)
6. Write filtered results to output file

### Performance Considerations
- Process large files (2MB+) efficiently using streaming
- Use set for O(1) deduplication lookups
- Minimize memory footprint by processing entries as streams
