import unittest

from autoclicker.input_backend import UnsupportedInputBackend, Win32InputBackend, create_input_backend


class InputBackendSelectionTests(unittest.TestCase):
    def test_selects_win32_backend_for_windows(self) -> None:
        backend = create_input_backend("win32")

        self.assertIsInstance(backend, Win32InputBackend)
        self.assertTrue(backend.supports_global_hotkeys)

    def test_selects_unsupported_backend_for_other_platforms(self) -> None:
        backend = create_input_backend("linux")

        self.assertIsInstance(backend, UnsupportedInputBackend)
        self.assertFalse(backend.supports_global_hotkeys)
        with self.assertRaisesRegex(OSError, "linux"):
            backend.click_mouse("left", 1, 2)


if __name__ == "__main__":
    unittest.main()
