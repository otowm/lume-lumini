import unittest
from app.capture import hotkeyd


class HotkeyChordTests(unittest.TestCase):
    def test_bracket_and_physical_layout(self):
        self.assertEqual(hotkeyd.parse_key('Ctrl+['), 26)
        self.assertEqual(hotkeyd.parse_key('Ctrl+[', 'BracketRight'), 27)

    def test_bracket_alone_does_not_trigger_control_shortcut(self):
        chord = hotkeyd.ShortcutDetector('Ctrl+[', hold_seconds=.6)
        self.assertIsNone(chord.feed_key(26, 1, 0))
        self.assertIsNone(chord.feed_key(26, 0, .1))
        chord.feed_key(29, 1, 1)
        chord.feed_key(26, 1, 1.1)
        self.assertEqual(chord.feed_key(26, 0, 1.2), 'tap')

    def test_right_control_and_hold(self):
        chord = hotkeyd.ShortcutDetector('Ctrl+[', hold_seconds=.6)
        chord.feed_key(97, 1, 0)
        chord.feed_key(26, 1, .1)
        self.assertEqual(chord.tick(.8), 'hold')
        self.assertIsNone(chord.feed_key(26, 0, .9))

    def test_releasing_modifier_cancels_hold(self):
        chord = hotkeyd.ShortcutDetector('Ctrl+[')
        chord.feed_key(29, 1, 0)
        chord.feed_key(26, 1, .1)
        chord.feed_key(29, 0, .2)
        self.assertIsNone(chord.tick(1))
        self.assertIsNone(chord.feed_key(26, 0, 1.1))

    def test_hud_chord_does_not_trigger_plain_f8(self):
        chord = hotkeyd.ShortcutDetector('F8')
        chord.feed_key(29, 1, 0)
        chord.feed_key(42, 1, 0)
        chord.feed_key(66, 1, .1)
        self.assertIsNone(chord.feed_key(66, 0, .2))


class WindowsBracketTests(unittest.TestCase):
    def test_bracket_uses_current_keyboard_layout(self):
        import ctypes
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from app.capture.winhotkey import MarkerHotkey

        lookup = Mock(return_value=0xDB)
        with patch.object(ctypes, "windll", SimpleNamespace(user32=SimpleNamespace(VkKeyScanW=lookup)), create=True):
            self.assertEqual(MarkerHotkey._parse("Ctrl+["), (2, 0xDB))
            lookup.assert_called_with(ord("["))
            lookup.return_value = 0x1DD  # layout que exige Shift
            self.assertEqual(MarkerHotkey._parse("Ctrl+]"), (6, 0xDD))
            lookup.return_value = 0xffff
            self.assertIsNone(MarkerHotkey._parse("Ctrl+["))
