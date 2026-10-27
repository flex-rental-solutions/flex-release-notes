#!/usr/bin/env python3
"""Read-only validation and full-content preview of plan changes against a Git ref."""

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "release-notes.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
ENTRY_VALIDATOR = Draft202012Validator(
    {"$ref": "#/$defs/proposedEntry", "$defs": SCHEMA["$defs"]},
    format_checker=FormatChecker(),
)


class JsonObject(dict):
    def __init__(self, pairs):
        super().__init__(pairs)
        self.pairs = pairs
        self.duplicates = [key for key, count in Counter(k for k, _ in pairs).items() for _ in range(count - 1)]


def duplicate_keys(value, path='$'):
    if isinstance(value, JsonObject):
        for key in value.duplicates:
            yield f'{path}.{key}'
        for key, child in value.pairs:
            yield from duplicate_keys(child, f'{path}.{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from duplicate_keys(child, f'{path}[{index}]')


def content_identity(value):
    if isinstance(value, JsonObject):
        occurrences = {}
        for key, child in value.pairs:
            occurrences.setdefault(key, []).append(content_identity(child))
        return occurrences
    if isinstance(value, list):
        return [content_identity(child) for child in value]
    return (type(value), value)


def parse(source):
    def invalid_constant(value):
        raise ValueError(f'Non-JSON numeric constant: {value}')
    result = json.loads(source, object_pairs_hook=JsonObject, parse_constant=invalid_constant)
    if not isinstance(result, list) or not result or not all(isinstance(item, dict) for item in result):
        raise ValueError('Expected a nonempty array of entry objects')
    return result


def schema_errors(validator, value):
    return [f'{error.json_path}: {error.message}' for error in validator.iter_errors(value)]


def validate_entry(entry):
    return ([f'duplicate key {key}' for key in duplicate_keys(entry)]
            + schema_errors(ENTRY_VALIDATOR, entry))


def preview(label, entry):
    print(f'\n{label}\nExact JSON:')
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    print('Decoded text (HTML source preserved):')
    for key in ('title', 'announcement'):
        if key in entry:
            print(f'{key}:\n{entry[key]}')
    notes = entry.get('notes', [])
    if isinstance(notes, list):
        for index, note in enumerate(notes, 1):
            print(f'note {index}:\n{note}')
    pins = entry.get('pinned', [])
    for pin in pins if isinstance(pins, list) else [pins]:
        if isinstance(pin, dict):
            print(f'pin flag: {pin.get("flag")}\nmessage:\n{pin.get("message")}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='origin/main', help='Already-fetched Git base ref')
    args = parser.parse_args()
    errors = []
    for filename in ('flex-enterprise.json', 'flex-assets.json'):
        try:
            base_text = subprocess.run(
                ['git', 'show', f'{args.base}:{filename}'], check=True,
                capture_output=True, text=True, encoding='utf-8'
            ).stdout
            before = parse(base_text)
            after = parse(Path(filename).read_text(encoding='utf-8'))
            before_identities = [content_identity(entry) for entry in before]
            after_identities = [content_identity(entry) for entry in after]
            print(f'\n=== {filename} ===')
            errors.extend(f'{filename}: {error}' for error in schema_errors(VALIDATOR, after))
            baseline_duplicates = list(duplicate_keys(before))
            if baseline_duplicates:
                print('Baseline duplicate-key warnings: ' + ', '.join(baseline_duplicates))
            # Ignore ordinary object-key order but retain every duplicate occurrence.
            changed = [entry for entry, identity in zip(after, after_identities)
                       if identity not in before_identities]
            for entry in changed:
                version = entry.get('version')
                errors.extend(f'{filename} {version}: {error}' for error in validate_entry(entry))
                if sum(item.get('version') == version for item in after) > 1:
                    errors.append(f'{filename}: duplicate changed version {version}')
                preview(f'Proposed {version} ({entry.get("date")})', entry)
            for entry, identity in zip(before, before_identities):
                if identity not in after_identities:
                    preview('Previous content removed or replaced', entry)
            # Reject extra copies even when they compare equal to an old entry.
            for entry, identity in zip(after, after_identities):
                if after_identities.count(identity) > max(1, before_identities.count(identity)):
                    errors.append(f'{filename}: added duplicate entry {entry.get("version")}')
                    break
            if not changed and before_identities == after_identities:
                print('No content changes.')
            elif not changed:
                print('No new/edited entries; inspect removals or ordering in git diff.')
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            errors.append(f'{filename}: {exc}')
    # Match the release-notes CI gate before any remote publication.
    for filename in ('flex-enterprise.json', 'flex-assets.json'):
        try:
            subprocess.run(['jq', '-e', '. | length > 0', filename],
                           check=True, stdout=subprocess.DEVNULL)
            print(f'CI jq validation passed: {filename}')
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f'CI jq validation failed for {filename}: {exc}')
    for error in errors:
        print(f'ERROR: {error}', file=sys.stderr)
    print('\nValidation failed.' if errors else '\nValidation passed. Review copy, HTML, scope, and diff separately.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
