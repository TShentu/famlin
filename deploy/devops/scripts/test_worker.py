import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import worker


class WorkerTests(unittest.TestCase):
    def test_failed_health_restores_source_and_download_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, public = base/'source', base/'public'
            (source/'web').mkdir(parents=True)
            public.mkdir()
            (base/'dependencies.sha256').write_text('old completed install')
            (source/'web/test.ts').write_text('old source')
            for name in ['latest.json', 'index.html']:
                (public/name).write_text('old page')
            content = b'new source'
            manifest = {'sourceCommit': 'abc', 'files': {'web/test.ts': hashlib.sha256(content).hexdigest()}}
            archive = io.BytesIO()
            with tarfile.open(fileobj=archive, mode='w:gz') as tar:
                for name, value in {'manifest.json': json.dumps(manifest).encode(), 'source/web/test.ts': content}.items():
                    item = tarfile.TarInfo(name)
                    item.size = len(value)
                    tar.addfile(item, io.BytesIO(value))
            data = {'famlin-family-unsigned.apk': b'unsigned', 'server-source.tgz': archive.getvalue(), 'source-commit.txt': b'abc',
                    'package-info.txt': b"package: name='cn.olares.hzfystt.famlin' versionCode='9' versionName='0.7.0'"}
            data['checksums.txt'] = '\n'.join(f'{hashlib.sha256(v).hexdigest()}  {k}' for k, v in data.items()).encode()
            prefix = f'https://github.com/{worker.REPO}/releases/download/dev-build-9/'
            release = {'assets': [{'name': k, 'data': v, 'size': len(v)} for k, v in data.items()]}
            def request(url):
                if url == worker.PUBLIC+'/latest.json':
                    return b'{"versionCode":2}'
                if url == worker.PUBLIC+'/new.apk':
                    return b'signed'
                return data[url.rsplit('/', 1)[1]]
            def command(args, **_kwargs):
                if 'sign' in args:
                    Path(args[args.index('--out')+1]).write_bytes(b'signed')
                else:
                    site = Path(args[args.index('--output')+1])
                    site.mkdir()
                    (site/'latest.json').write_text(json.dumps({'apkUrl': worker.PUBLIC+'/new.apk', 'sha256': hashlib.sha256(b'signed').hexdigest()}))
                    (site/'new.apk').write_bytes(b'signed')
            args = SimpleNamespace(state=str(base/'state'), downloads=str(public), source=str(source), branch='main',
                                   keystore=str(base/'private.p12'), password_file=str(base/'password'), java='java', apksigner='signer.jar', health_url='http://server')
            with patch.object(worker, 'candidate', return_value=({'run_number': 9, 'head_sha': 'abc'}, release)), \
                 patch.object(worker, 'request', side_effect=request), \
                 patch.object(worker.subprocess, 'run', side_effect=command), \
                 patch.object(worker.subprocess, 'check_output', return_value=worker.CERT), \
                 patch.object(worker, 'health', side_effect=RuntimeError('unhealthy')):
                with self.assertRaisesRegex(RuntimeError, 'unhealthy'):
                    worker.execute(args)
            self.assertEqual((source/'web/test.ts').read_text(), 'old source')
            self.assertEqual((public/'latest.json').read_text(), 'old page')
            self.assertEqual((public/'index.html').read_text(), 'old page')
            self.assertTrue((base/'state/failed.json').exists())
            self.assertFalse((base/'state/pending.json').exists())
            self.assertFalse((base/'dependencies.sha256').exists())

class CandidateTests(unittest.TestCase):
    def test_rejects_archive_paths_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state/'inbox').mkdir()
            with tarfile.open(state/'inbox/bad.tgz', 'w:gz') as tar:
                entry = tarfile.TarInfo('../escape')
                entry.size = 1
                tar.addfile(entry, io.BytesIO(b'x'))
            self.assertIsNone(worker.candidate('main', state))
            self.assertFalse((state/'escape').exists())
            self.assertTrue((state/'rejected/bad.tgz').exists())

    def test_ingests_only_allowed_repository_and_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state/'inbox').mkdir()
            metadata = {'repository': worker.REPO, 'branch': 'untrusted', 'runNumber': 9,
                        'sourceCommit': 'a'*40, 'runUrl': 'https://github.com/TShentu/famlin/actions/runs/123'}
            for branch in ['untrusted', 'main']:
                metadata['branch'] = branch
                entries = {name: b'x' for name in ['checksums.txt','famlin-family-unsigned.apk','server-source.tgz','package-info.txt','source-commit.txt']}
                entries['candidate.json'] = json.dumps(metadata).encode()
                with tarfile.open(state/f'inbox/{branch}.tgz', 'w:gz') as tar:
                    for name, data in entries.items():
                        entry = tarfile.TarInfo(name)
                        entry.size = len(data)
                        tar.addfile(entry, io.BytesIO(data))
                result = worker.candidate('codex/devops-zh', state)
                if branch == 'untrusted':
                    self.assertIsNone(result)
                else:
                    self.assertEqual(result[0]['head_sha'], 'a'*40)


if __name__ == '__main__':
    unittest.main()
