import unittest
import numpy as np
from PIL import Image
from engine import demo_pair,inspect_pair,png_bytes,batch_inspect
from io import BytesIO
from zipfile import ZipFile

class VisionDeltaEngineTests(unittest.TestCase):
    def test_fixture_is_deterministic(self):
        a,b,c=demo_pair()
        a2,b2,c2=demo_pair()
        np.testing.assert_array_equal(np.asarray(b),np.asarray(b2))

    def test_demo_has_visible_regions(self):
        a,b,truth=demo_pair()
        report=inspect_pair(a,b,sensitivity=.25,min_area=70,truth=truth)
        s=report["summary"]
        self.assertGreater(s["region_count"],0)
        self.assertGreater(s["flagged_area_pct"],0)
        self.assertIn("precision",s["evaluation"])
        self.assertEqual(len(report["images"]),7)

    def test_equal_images_are_clean(self):
        a,_,_=demo_pair()
        report=inspect_pair(a,a,alignment="off")
        self.assertEqual(report["summary"]["region_count"],0)
        self.assertEqual(report["summary"]["flagged_area_pct"],0)

    def test_errors_are_handled(self):
        with self.assertRaises(ValueError):
            inspect_pair(Image.new("RGB",(8,8)),Image.new("RGB",(8,8)))
        with self.assertRaises(ValueError):
            inspect_pair(*demo_pair()[:2], sensitivity=2.0)

    def test_png_signature(self):
        a,_,_=demo_pair()
        self.assertTrue(png_bytes(a).startswith(b"\x89PNG"))

    def test_batch_review(self):
        a,b,_=demo_pair()
        data=BytesIO()
        with ZipFile(data,"w") as archive:
            archive.writestr("before/panel.png",png_bytes(a))
            archive.writestr("after/panel.png",png_bytes(b))
        table=batch_inspect(data.getvalue())
        self.assertEqual(len(table),1)
        self.assertEqual(table.iloc[0]["image"],"panel.png")

if __name__=="__main__":
    unittest.main()
