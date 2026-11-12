"""Linear audit log with a separately retained checkpoint, not a signature.

The checkpoint must be inaccessible to the actor that can rewrite the log.
A crash between append and checkpoint fails closed and needs host recovery.
"""
import json
import os
from pathlib import Path
import tempfile
import argparse
import sys
from .ledger import _seal, verify_chain


class AuditError(ValueError):
    pass


class AuditStore:
    def __init__(self, log, checkpoint):
        self.log, self.checkpoint = Path(log), Path(checkpoint)
        if self.log.resolve() == self.checkpoint.resolve():
            raise AuditError('checkpoint must be separate from log')
        if self.log.exists() != self.checkpoint.exists():
            raise AuditError('missing log or checkpoint; host recovery required')
        self.records = []
        if self.log.exists():
            self.records = [json.loads(line) for line in self.log.read_text(encoding='utf-8').splitlines()]
            anchor = json.loads(self.checkpoint.read_text(encoding='utf-8'))
            expected = {'length': len(self.records), 'head': self.records[-1]['hash'] if self.records else None}
            if verify_chain(self.records) or anchor != expected:
                raise AuditError('log does not match independent checkpoint')
        else:
            self.log.parent.mkdir(parents=True, exist_ok=True)
            self.checkpoint.parent.mkdir(parents=True, exist_ok=True)
            self.log.touch(exist_ok=False)
            self._checkpoint({'length': 0, 'head': None})

    def _checkpoint(self, value):
        fd, path = tempfile.mkstemp(dir=self.checkpoint.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(value, stream, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(path, self.checkpoint)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def append(self, event):
        # Single writer owned by the host. Revalidate before every append.
        current = AuditStore(self.log, self.checkpoint)
        if current.records != self.records:
            raise AuditError('another writer changed the audit store')
        record = _seal(dict(event, seq=len(self.records)), self.records[-1]['hash'] if self.records else None)
        with self.log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        self._checkpoint({'length': len(self.records) + 1, 'head': record['hash']})
        self.records.append(record)


def main(argv):
    parser = argparse.ArgumentParser(prog='skillwren audit')
    parser.add_argument('log')
    parser.add_argument('checkpoint')
    args = parser.parse_args(argv)
    try:
        if not Path(args.log).is_file() or not Path(args.checkpoint).is_file():
            raise AuditError('existing log and independent checkpoint required')
        store = AuditStore(args.log, args.checkpoint)
        active = False
        interruptions = 0
        for record in store.records:
            if record.get('type') == 'start':
                interruptions += int(active)
                active = True
            elif record.get('type') == 'stop':
                active = False
        interruptions += int(active)
        report = {'integrity_valid': True, 'records': len(store.records),
                  'interrupted_sessions': interruptions,
                  'recorder_closed': bool(store.records) and store.records[-1].get('type') == 'stop',
                  'coverage': 'controller requests only'}
        print(json.dumps(report, indent=2))
        return 0 if report['recorder_closed'] and not interruptions else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2
