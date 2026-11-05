import unittest
from PIL import Image
from logic import demo_images, inspect, png_bytes

class TestVisionDelta(unittest.TestCase):
    def test_demo_changes(self):
        result=inspect(*demo_images(), threshold=30, minimum_area=15)
        self.assertGreater(result['summary']['changed_pixel_percent'],0)
        self.assertGreater(len(result['summary']['regions']),0)
    def test_same_image(self):
        img=Image.new('RGB',(100,100),'blue')
        result=inspect(img,img)
        self.assertEqual(result['summary']['changed_pixel_percent'],0)
        self.assertEqual(len(result['summary']['regions']),0)
    def test_png(self):
        self.assertTrue(png_bytes(demo_images()[0]).startswith(b'\x89PNG'))

if __name__=='__main__':unittest.main()
