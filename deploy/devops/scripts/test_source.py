import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from source import read_bundle, apply, accept, rollback


class SourceTests(unittest.TestCase):
    def bundle(self, entries):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:gz') as tar:
            for name, content in entries.items():
                item = tarfile.TarInfo(name)
                item.size = len(content)
                tar.addfile(item, io.BytesIO(content))
        return data.getvalue()

    def test_rejects_traversal_and_checksum_mismatch(self):
        with self.assertRaises(ValueError):
            read_bundle(self.bundle({'source/backend/../../secret': b'x'}), 'abc')
        with self.assertRaises(ValueError):
            read_bundle(self.bundle({'manifest.json': json.dumps({'sourceCommit': 'abc', 'files': {}}).encode(), 'source/web/a': b'x'}), 'abc')

    def test_update_delete_and_rollback_preserve_unmanaged_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state = Path(tmp)/'source', Path(tmp)/'state'
            (root/'web').mkdir(parents=True)
            (root/'web/old.ts').write_text('old')
            (root/'web/old.ts').chmod(0o755)
            (root/'web/user-file').write_text('keep')
            files = {'web/old.ts': b'new', 'web/new.ts': b'new'}
            manifest = {'sourceCommit': 'abc', 'files': {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}}
            apply(root, state, manifest, files)
            rollback(root, state)
            self.assertEqual((root/'web/old.ts').read_text(), 'old')
            self.assertEqual((root/'web/old.ts').stat().st_mode & 0o777, 0o755)
            self.assertFalse((root/'web/new.ts').exists())
            apply(root, state, manifest, files)
            accept(state, manifest)
            apply(root, state, {'sourceCommit': 'next', 'files': {}}, {})
            self.assertFalse((root/'web/old.ts').exists())
            self.assertEqual((root/'web/user-file').read_text(), 'keep')
            rollback(root, state)
            self.assertEqual((root/'web/old.ts').read_text(), 'new')

    def test_no_writes_through_symlinks_or_migrations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'root'
            root.mkdir()
            (root/'web').symlink_to(Path(tmp), target_is_directory=True)
            with self.assertRaises(ValueError):
                apply(root, Path(tmp)/'state', {'files': {}}, {'web/secret': b'x'})
            with self.assertRaises(ValueError):
                apply(root, Path(tmp)/'state', {'files': {}}, {'backend/prisma/migrations/new.sql': b'x'})


if __name__ == '__main__':
    unittest.main()
