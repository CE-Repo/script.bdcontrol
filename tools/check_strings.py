#!/usr/bin/env python3
"""Verify that every string id used by the addon exists in the .po files.

    python3 tools/check_strings.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LOCALIZE = re.compile(r'localize\(\s*(\d{5})')
COMMAND = re.compile(r'Command\(\s*(\d{5})\s*,\s*(\d{5})')
SETTING_LABEL = re.compile(r'label="(\d{5})"')
SETTING_HELP = re.compile(r'help="(\d{5})"')
PO_ID = re.compile(r'msgctxt "#(\d{5})"')


def collect_used():
    used = set()
    for base, _dirs, files in os.walk(os.path.join(ROOT, 'resources', 'lib')):
        for name in files:
            if not name.endswith('.py'):
                continue
            with open(os.path.join(base, name), encoding='utf-8') as handle:
                text = handle.read()
            used.update(int(value) for value in LOCALIZE.findall(text))
            for label, hint in COMMAND.findall(text):
                used.add(int(label))
                used.add(int(hint))
    settings = os.path.join(ROOT, 'resources', 'settings.xml')
    if os.path.exists(settings):
        with open(settings, encoding='utf-8') as handle:
            text = handle.read()
        used.update(int(value) for value in SETTING_LABEL.findall(text))
        used.update(int(value) for value in SETTING_HELP.findall(text))
    return used


def collect_defined(language):
    path = os.path.join(ROOT, 'resources', 'language', language, 'strings.po')
    with open(path, encoding='utf-8') as handle:
        return {int(value) for value in PO_ID.findall(handle.read())}


def main():
    used = collect_used()
    failures = 0
    for language in ('resource.language.en_gb', 'resource.language.de_de'):
        defined = collect_defined(language)
        missing = sorted(used - defined)
        if missing:
            print('%s: missing %s' % (language, missing))
            failures += 1
        unused = sorted(defined - used)
        if unused:
            print('%s: defined but never used: %s' % (language, unused))
    if failures:
        return 1
    print('all %d used string ids are defined' % len(used))
    return 0


if __name__ == '__main__':
    sys.exit(main())
