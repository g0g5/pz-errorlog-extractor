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


def extract_timestamp_and_body(content: str) -> tuple[str | None, str]:
    """
    Extract timestamp and message body from entry content.

    Pattern: f:<number>, t:<timestamp>> or just t:<timestamp>>
    Returns (timestamp, body_without_timestamp)
    """
    # Pattern to match timestamp like "f:0, t:1771295104050>" or just "t:1771295104050>"
    timestamp_pattern = re.compile(r'^(LOG|WARN|ERROR)\s*:\s*\S+\s+(f:\d+,\s*)?t:(\d+)>(.*)$', re.MULTILINE)

    # Check first line for timestamp
    lines = content.split('\n', 1)
    first_line = lines[0] if lines else ''
    rest = lines[1] if len(lines) > 1 else ''

    match = timestamp_pattern.match(first_line)
    if match:
        timestamp = match.group(3)
        # Reconstruct the body: type + category + rest of message (without timestamp)
        entry_type = match.group(1)
        # Extract category (the word after type, before f: or t:)
        category_match = re.match(r'^(LOG|WARN|ERROR)\s*:\s*(\S+)\s+', first_line)
        category = category_match.group(2) if category_match else ''
        message_rest = match.group(4)

        # Build body without timestamp
        body_first_line = f"{entry_type} : {category}{message_rest}"
        body = body_first_line + ('\n' + rest if rest else '')
        return timestamp, body.strip()

    return None, content.strip()


def deduplicate_entries(entries: list[dict]) -> list[dict]:
    """
    Remove duplicate entries based on message body (excluding timestamp).
    Returns a list of unique entries preserving original order.
    Each entry has 'timestamps' list containing all timestamps for duplicates.
    """
    body_to_entry: dict[str, dict] = {}

    for entry in entries:
        timestamp, body = extract_timestamp_and_body(entry['content'])

        if body not in body_to_entry:
            # First occurrence - create new entry
            body_to_entry[body] = {
                'type': entry['type'],
                'content': entry['content'],
                'body': body,
                'timestamps': [timestamp] if timestamp else [],
                'first_index': len(body_to_entry)  # Preserve order
            }
        else:
            # Duplicate - add timestamp to existing entry
            if timestamp:
                body_to_entry[body]['timestamps'].append(timestamp)

    # Convert dict back to list, preserving original order
    unique_entries = sorted(body_to_entry.values(), key=lambda x: x['first_index'])
    return unique_entries


def format_timestamp_range(timestamps: list[str]) -> str:
    """Format timestamp list as range or single timestamp."""
    if not timestamps:
        return "N/A"
    if len(timestamps) == 1:
        return timestamps[0]
    # Sort timestamps numerically
    sorted_ts = sorted(timestamps, key=int)
    return f"{sorted_ts[0]} ~ {sorted_ts[-1]} (x{len(timestamps)})"


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
        f.write(f'Unique entries found: {len(entries)}\n')
        f.write('\n')

        # Write each entry
        for i, entry in enumerate(entries, 1):
            f.write(f'--- Entry {i} ---\n')
            # Write timestamp range
            ts_range = format_timestamp_range(entry.get('timestamps', []))
            f.write(f'Timestamp: {ts_range}\n')
            # Write the body (message without timestamp)
            f.write(entry['body'])
            # Ensure entry ends with a newline
            if not entry['body'].endswith('\n'):
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
