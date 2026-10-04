import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('transfer', Path(__file__).resolve().parents[1]/'famlindevops/files/transfer.py')
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class TransferTests(unittest.TestCase):
    def test_out_of_order_and_retry_produce_one_verified_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            data = b'x'*transfer.CHUNK+b'end'
            sha = hashlib.sha256(data).hexdigest()
            self.assertFalse(transfer.receive(d,sha,1,2,len(data),b'end'))
            self.assertTrue(transfer.receive(d,sha,0,2,len(data),data[:transfer.CHUNK]))
            self.assertTrue(transfer.receive(d,sha,1,2,len(data),b'end'))
            archives=list((Path(d)/'inbox').glob('*.tgz'))
            self.assertEqual(len(archives),1)
            self.assertEqual(archives[0].read_bytes(),data)

    def test_bad_hash_and_bounds_never_enqueue(self):
        with tempfile.TemporaryDirectory() as d:
            for sha,index,count,total in [('0'*64,0,1,3),('../bad',0,1,3),('0'*64,3,1,3)]:
                with self.assertRaises(ValueError):
                    transfer.receive(d,sha,index,count,total,b'bad')
            self.assertEqual(list((Path(d)/'inbox').glob('*.tgz')),[])
