import unittest
from py315ready import wheel_verdict, spec_allows, check, read_requirements

class Tags(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(wheel_verdict("numpy-2.3.0-cp315-cp315-manylinux_2_28_x86_64.whl"), "cp315")
        self.assertEqual(wheel_verdict("numpy-2.3.0-cp315-cp315t-win_amd64.whl"), "cp315t")
        self.assertEqual(wheel_verdict("cryptography-46.0.0-cp311-abi3-manylinux_2_34_x86_64.whl"), "abi3")
        self.assertIsNone(wheel_verdict("x-1.0-cp316-abi3-linux_x86_64.whl"))
        self.assertEqual(wheel_verdict("requests-2.32.5-py3-none-any.whl"), "pure")
        self.assertEqual(wheel_verdict("six-1.17.0-py2.py3-none-any.whl"), "pure")
        self.assertIsNone(wheel_verdict("old-1.0-py2-none-any.whl"))
        self.assertIsNone(wheel_verdict("lxml-6.0.0-cp314-cp314-manylinux_2_28_x86_64.whl"))

class Spec(unittest.TestCase):
    def test_spec(self):
        for s in [None, "", ">=3.9", ">=3.10,<4", "!=3.0.*,!=3.1.*,>=2.7", "~=3.9", "<=3.15", ">3.14.9"]:
            self.assertTrue(spec_allows(s), s)
        for s in ["<3.15", ">=3.9,<3.15", "==3.14.*", "<=3.14", "~=3.12.0", "!=3.15.*"]:
            self.assertFalse(spec_allows(s), s)

def fake(files, rp=">=3.9", cls=()):
    return lambda name: {"info": {"version": "1.0", "requires_python": rp, "classifiers": list(cls)},
                         "urls": [{"filename": f, "upload_time_iso_8601": "2026-09-01T00:00:00Z"} for f in files]}

class Check(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(check("a", fake(["a-1.0-py3-none-any.whl"]))["status"], "READY")
        self.assertEqual(check("a", fake(["a-1.0-cp314-cp314-win_amd64.whl", "a-1.0.tar.gz"]))["status"], "NO-WHEEL")
        self.assertEqual(check("a", fake(["a-1.0.tar.gz"]))["status"], "SDIST-ONLY")
        self.assertEqual(check("a", fake(["a-1.0-py3-none-any.whl"], rp="<3.15"))["status"], "BLOCKED")
        self.assertTrue(check("a", fake([], cls=["Programming Language :: Python :: 3.15"]))["declares_315"])

class Req(unittest.TestCase):
    def test_parse(self):
        import tempfile, os
        p = tempfile.mktemp()
        open(p, "w").write("# c\nNumPy>=2\nrequests[socks]==2.32 ; python_version>'3'\n-e .\ngit+https://x\nnumpy\n")
        self.assertEqual(read_requirements(p), ["NumPy", "requests"]); os.remove(p)

if __name__ == "__main__":
    unittest.main()
