import unittest

from command_utils import parse_command


class TestParseCommand(unittest.TestCase):
    def test_non_command(self):
        self.assertEqual(parse_command("hello"), ("", ""))

    def test_command_without_args(self):
        self.assertEqual(parse_command("/list_listen"), ("/list_listen", ""))

    def test_command_with_args(self):
        self.assertEqual(parse_command("/add_listen -100 @bot"), ("/add_listen", "-100 @bot"))


if __name__ == "__main__":
    unittest.main()
