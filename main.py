#!/usr/bin/env python3
"""
Project Zomboid Server Log Filter

A tool to filter and extract error-related entries from verbose Project Zomboid
server log files.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_log_file(file_path: Path) -> list[dict]:
    """
    Parse the log file and return a list of entries.
    Each entry is a dict with 'type', 'content', and 'clean_content'.
    """
    # Entry start pattern: LOG:, WARN:, or ERROR: at line beginning
    entry_start_pattern = re.compile(r'^(LOG|WARN|ERROR)\s*:')

    entries = []
    current_entry = None

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            # Check if this line starts a new entry
            match = entry_start_pattern.match(line)

            if match:
                # Save the previous entry if exists
                if current_entry is not None:
                    entries.append(current_entry)

                # Start a new entry
                entry_type = match.group(1)  # LOG, WARN, or ERROR
                current_entry = {
                    'type': entry_type,
                    'content': line,
                    # For deduplication, we'll compute this later
                    'clean_content': None
                }
            elif current_entry is not None:
                # Continue the current multi-line entry
                current_entry['content'] += line
            else:
                # Lines before the first entry - skip them
                pass

        # Don't forget the last entry
        if current_entry is not None:
            entries.append(current_entry)

    return entries


def should_include_entry(entry: dict, additional_keywords: list[str] | None = None) -> bool:
    """
    Determine if an entry should be included based on filtering rules.

    Include criteria:
    1. All ERROR and WARN entries
    2. LOG entries containing error/warning keywords (case-insensitive)
    """
    entry_type = entry['type']
    content = entry['content']

    # Always include ERROR and WARN entries
    if entry_type in ('ERROR', 'WARN'):
        return True

    # For LOG entries, check for error/warning keywords
    if entry_type == 'LOG':
        content_lower = content.lower()

        # Default keywords to check
        default_keywords = ['error', 'warning', 'err', 'warn']

        # Check default keywords
        for keyword in default_keywords:
            if keyword in content_lower:
                return True

        # Check additional keywords if provided
        if additional_keywords:
            for keyword in additional_keywords:
                if keyword.lower() in content_lower:
                    return True

    return False


def deduplicate_entries(entries: list[dict]) -> list[dict]:
    """
    Remove duplicate entries based on content (after stripping whitespace).
    Returns a list of unique entries preserving original order.
    """
    seen = set()
    unique_entries = []

    for entry in entries:
        # Normalize content for deduplication
        clean_content = entry['content'].strip()

        if clean_content not in seen:
            seen.add(clean_content)
            entry['clean_content'] = clean_content
            unique_entries.append(entry)

    return unique_entries


def generate_report(
    entries: list[dict],
    source_filename: str,
    output_path: Path
) -> None:
    """Generate the filtered log report file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write('=== Project Zomboid Server Log Filter Report ===\n')
        f.write(f'Source: {source_filename}\n')
        f.write(f'Generated: {timestamp}\n')
        f.write(f'Total entries found: {len(entries)}\n')
        f.write('\n')

        # Write each entry
        for i, entry in enumerate(entries, 1):
            f.write(f'--- Entry {i} ---\n')
            f.write(entry['content'])
            # Ensure entry ends with a newline
            if not entry['content'].endswith('\n'):
                f.write('\n')
            f.write('\n')


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Filter and extract error-related entries from Project Zomboid server logs.'
    )
    parser.add_argument(
        'log_file_path',
        help='Path to the Project Zomboid server log file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: {input}_errors.txt)'
    )
    parser.add_argument(
        '--keywords',
        help='Additional keywords to filter (comma-separated)'
    )

    args = parser.parse_args()

    # Resolve input file path
    log_file_path = Path(args.log_file_path).resolve()
    if not log_file_path.exists():
        print(f'Error: Log file not found: {log_file_path}', file=sys.stderr)
        return 1

    # Determine output file path
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = log_file_path.parent / f'{log_file_path.stem}_errors.txt'

    # Parse additional keywords
    additional_keywords = None
    if args.keywords:
        additional_keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]

    # Parse the log file
    print(f'Parsing log file: {log_file_path}')
    entries = parse_log_file(log_file_path)
    print(f'Total entries parsed: {len(entries)}')

    # Filter entries
    filtered_entries = [
        entry for entry in entries
        if should_include_entry(entry, additional_keywords)
    ]
    print(f'Entries matching filter criteria: {len(filtered_entries)}')

    # Deduplicate
    unique_entries = deduplicate_entries(filtered_entries)
    print(f'Unique entries after deduplication: {len(unique_entries)}')

    # Generate report
    generate_report(unique_entries, log_file_path.name, output_path)
    print(f'Report written to: {output_path}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
