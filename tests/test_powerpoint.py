"""Adapter contract tests; COM objects are fakes, not evidence of Office compatibility."""

from types import SimpleNamespace as NS
import unittest

from app.powerpoint import PowerPointAdapter, PowerPointError, PowerPointCommandError


class Collection:
    def __init__(self, items):
        self.items = items

    @property
    def Count(self):
        return len(self.items)

    def Item(self, index):
        return self.items[index - 1]


class FakeView:
    def __init__(self):
        self.index = 1
        self.calls = []
        self.refuse = False

    @property
    def Slide(self):
        return NS(SlideIndex=self.index)

    def GotoSlide(self, index, reset):
        self.calls.append((index, reset))
        if not self.refuse:
            self.index = index


def fake_application():
    presentation = NS(Name="Test.pptx", FullName="C:/test/Test.pptx",
                      Slides=Collection([NS(SlideShowTransition=NS(Hidden=False)) for _ in range(5)]),
                      SlideShowSettings=NS(RangeType=1))
    window = NS(Presentation=presentation, View=FakeView())
    return NS(SlideShowWindows=Collection([window])), window


class PowerPointTests(unittest.TestCase):
    def setUp(self):
        self.app, self.window = fake_application()
        self.adapter = PowerPointAdapter(lambda: self.app)

    def test_not_connected_cannot_dispatch(self):
        with self.assertRaises(PowerPointError):
            self.adapter.apply("next")

    def test_connection_and_verified_navigation(self):
        self.assertEqual(self.adapter.connect().slide, 1)
        result = self.adapter.apply("next")
        self.assertEqual(result.state.slide, 2)
        self.assertTrue(result.moved)
        self.assertGreaterEqual(result.elapsed_ms, 0)
        self.assertEqual(self.window.View.calls, [(2, 0)])
        self.assertEqual(self.adapter.apply("previous").state.slide, 1)

    def test_window_handle_is_not_required(self):
        self.assertFalse(hasattr(self.window, "HWND"))
        self.adapter.connect()
        self.assertEqual(self.adapter.apply("next").state.slide, 2)

    def test_current_slide_is_read_before_each_action(self):
        self.adapter.connect()
        self.window.View.index = 3  # manual navigation outside Hey Slides
        self.assertEqual(self.adapter.apply("next").state.slide, 4)

    def test_boundaries_do_not_end_show_or_wrap(self):
        self.adapter.connect()
        self.assertFalse(self.adapter.apply("previous").moved)
        self.window.View.index = 5
        self.assertFalse(self.adapter.apply("next").moved)
        self.assertEqual(self.window.View.calls, [])

    def test_hidden_slides_are_skipped_by_next_previous(self):
        self.window.Presentation.Slides.Item(2).SlideShowTransition.Hidden = True
        self.adapter.connect()
        self.assertEqual(self.adapter.apply("next").state.slide, 3)
        self.assertEqual(self.adapter.apply("previous").state.slide, 1)

    def test_goto_and_invalid_numbers(self):
        self.adapter.connect()
        self.assertEqual(self.adapter.apply("goto", 4).state.slide, 4)
        for target in (0, 6, None, True):
            with self.assertRaises(PowerPointCommandError):
                self.adapter.apply("goto", target)
        self.assertEqual(self.adapter.snapshot().slide, 4)

    def test_missing_or_ambiguous_show_rejected(self):
        for windows in ([], [self.window, self.window]):
            self.app.SlideShowWindows.items = windows
            with self.assertRaises(PowerPointError):
                self.adapter.connect()

    def test_custom_or_range_show_rejected(self):
        for range_type in (2, 3):
            self.window.Presentation.SlideShowSettings.RangeType = range_type
            with self.assertRaises(PowerPointError):
                self.adapter.connect()

    def test_ended_show_does_not_retarget_another_window(self):
        self.adapter.connect()
        _, replacement = fake_application()
        self.app.SlideShowWindows.items = [replacement]
        with self.assertRaises(PowerPointError):
            self.adapter.apply("next")
        self.assertEqual(self.window.View.calls, [])
        with self.assertRaises(PowerPointError):
            self.adapter.snapshot()

    def test_renamed_presentation_requires_reconnect(self):
        self.adapter.connect()
        self.window.Presentation.FullName = "C:/test/Other.pptx"
        with self.assertRaises(PowerPointError):
            self.adapter.apply("next")
        self.assertEqual(self.window.View.calls, [])

    def test_failed_readback_invalidates_connection(self):
        self.adapter.connect()
        self.window.View.refuse = True
        with self.assertRaises(PowerPointError):
            self.adapter.apply("next")
        with self.assertRaises(PowerPointError):
            self.adapter.snapshot()

    def test_disconnected_com_error_becomes_actionable_error(self):
        self.adapter.connect()
        self.app.SlideShowWindows = None
        with self.assertRaisesRegex(PowerPointError, "reconnect"):
            self.adapter.apply("next")


if __name__ == "__main__":
    unittest.main()
