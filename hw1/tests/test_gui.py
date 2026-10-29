"""Связь GUI с состоянием шелла без открытия настоящего окна."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from gui import ShellWindow
from shell import Shell
from vfs_reader import get_vfs


class TestPrompt(unittest.TestCase):
    """Приглашение обновляется при ручном и скриптовом вводе."""

    def setUp(self):
        """Создаёт окно с подменными виджетами без запуска GUI."""
        path = Path(__file__).resolve().parent.parent / "vfs" / "deep.xml"
        self.window = ShellWindow.__new__(ShellWindow)
        self.window.shell = Shell(get_vfs(str(path)))
        self.window.prompt_label = Mock()
        self.window.write = Mock()
        self.window.update_prompt()

    def test_interactive_cd_updates_label(self):
        """Введённая команда cd обновляет путь в приглашении."""
        old_prompt = self.window.prompt
        self.window.run_line("cd /home")
        self.assertTrue(self.window.prompt.endswith(":/home$ "))
        self.window.prompt_label.config.assert_called_with(text=self.window.prompt)
        self.window.write.assert_called_once_with(old_prompt + "cd /home")

    def test_script_uses_updated_prompt(self):
        """Команды скрипта выводятся с актуальным путём в приглашении."""
        with patch("gui.Path.read_text", return_value="cd /home\ncd student"):
            self.window.run_script("startup.txt")
        self.assertTrue(self.window.prompt.endswith(":/home/student$ "))
        second_line = self.window.write.call_args_list[1].args[0]
        self.assertTrue(second_line.endswith(":/home$ cd student"))
        self.window.prompt_label.config.assert_called_with(text=self.window.prompt)

    def test_failed_cd_keeps_prompt(self):
        """Ошибка перехода сохраняет текущий каталог и приглашение."""
        self.window.run_line("cd /home")
        old_prompt = self.window.prompt
        self.window.run_line("cd student/missing")
        self.assertEqual(self.window.prompt, old_prompt)
        self.assertEqual(self.window.shell.current_path, "/home")
        self.assertIn("no such file or directory", self.window.write.call_args.args[0])

    def test_cd_demo_stops_at_file(self):
        """Демонстрационный скрипт останавливается при попытке перейти в файл."""
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        self.window.run_script(str(scripts / "cd_demo.txt"))
        self.assertEqual(self.window.shell.current_path, "/home/student/project/docs")
        self.window.write.assert_any_call(
            "cd: /home/student/notes.txt: not a directory."
        )
        self.assertIn("execution stopped", self.window.write.call_args.args[0])

    def test_no_errors_script_without_vfs(self):
        """Скрипт без ошибок выполняется до конца без загруженной VFS."""
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        self.window.shell = Shell(None)
        self.window.run_script(str(scripts / "no_errors.txt"))
        output = [call.args[0] for call in self.window.write.call_args_list]
        self.assertFalse(any("Script error" in line for line in output))
        self.assertEqual(output[-1], "ls: []")

    def test_exit_script_closes_window(self):
        """Команда exit в стартовом скрипте закрывает окно."""
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        self.window.root = Mock()
        self.window.run_script(str(scripts / "with_exit.txt"))
        self.window.root.destroy.assert_called_once_with()

    def test_stage3_demo_with_minimal_vfs(self):
        """Скрипт с минимальной VFS доходит до ошибки exit с аргументами."""
        base = Path(__file__).resolve().parent.parent
        self.window.shell = Shell(get_vfs(str(base / "vfs" / "minimal.xml")))
        self.window.run_script(str(base / "scripts" / "stage3_demo.txt"))
        self.window.write.assert_any_call("exit: too many arguments.")
        self.assertIn("execution stopped", self.window.write.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
