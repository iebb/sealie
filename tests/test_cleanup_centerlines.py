"""Sub-pen centerline faults are removed by deleting vertices only."""
from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import cleanup_centerlines as cleanup


class CleanupCenterlines(unittest.TestCase):
    def kept(self,points,closed=False):
        result,found=cleanup.clean(points,closed)
        self.assertTrue(set(result)<=set(points))
        self.assertEqual((result[0],result[-1]),(points[0],points[-1]))
        return result,found

    def test_tiny_segment_back_step_and_notch(self):
        result,found=self.kept([(0,0),(50,0),(50.1,0),(100,0)])
        self.assertEqual(result,[(0,0),(50,0),(100,0)]);self.assertEqual(found,{'tiny':1})
        result,found=self.kept([(0,0),(60,0),(50,0.1),(120,0)])
        self.assertEqual(result,[(0,0),(60,0),(120,0)]);self.assertEqual(found,{'back_step':1})
        result,found=self.kept([(0,0),(40,0),(48,0),(50,3),(52,0),(60,0),(100,0)])
        self.assertNotIn((50,3),result);self.assertIn('notch',found)

    def test_jitter_is_thinned_within_tolerance(self):
        points=[(float(x),0.2*(-1)**x) for x in range(40)]
        result,found=self.kept(points)
        self.assertIn('jitter',found);self.assertLess(len(result),10)
        for point in points:
            self.assertLessEqual(min(cleanup._deviation(point,a,b) for a,b in zip(result,result[1:])),cleanup.JITTER_EPSILON)

    def test_shapes_are_kept(self):
        hook=[(0,0),(100,0),(104,3),(106,8),(105,14)]
        corner=[(0,0),(50,0),(50,50)]
        ring=[(0,0),(2,0),(2,2),(0,2)]
        for points,closed in ((hook,False),(corner,False),(ring,True),([(5,5)],False)):
            self.assertEqual(cleanup.clean(points,closed),(points,{}))

    def test_repository_sources_are_clean_and_text_is_preserved(self):
        text=(ROOT/'tests/sample-svg/U3D000.svg').read_text()
        self.assertEqual(cleanup.clean_text(text),(text,[]))
        dirty=text.replace('L ','L 300.0 320.0 L 300.1 320.0 L ',1)
        cleaned,report=cleanup.clean_text(dirty)
        self.assertEqual(report[0]['tiny'],1);self.assertIn('L 300.0 320.0 L',cleaned);self.assertNotIn('300.1',cleaned)


if __name__=='__main__':unittest.main()
