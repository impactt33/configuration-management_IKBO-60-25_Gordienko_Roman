"""Связь GUI с состоянием шелла без открытия настоящего окна."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from gui import ShellWindow
from shell import Shell
from vfs_reader import get_vfs


class TestPrompt(unittest.TestCase):
    """Приглашение обновляется при ручном и скриптовом вводе."""

    def create_window(self):
        """Создаёт окно с подменными виджетами без запуска GUI."""
        path = Path(__file__).resolve().parent.parent / "vfs" / "deep.xml"
        self.window = ShellWindow.__new__(ShellWindow)
        self.window.shell = Shell(get_vfs(str(path)))
        self.window.prompt_label = Mock()
        self.window.write = Mock()
        self.window.update_prompt()

    def test_interactive_cd_updates_label(self):
        """Введённая команда cd обновляет путь в приглашении."""
        self.create_window()
        old_prompt = self.window.prompt
        self.window.run_line("cd /home")
        self.assertTrue(self.window.prompt.endswith(":/home$ "))
        self.window.prompt_label.config.assert_called_with(
            text=self.window.prompt
        )
        self.window.write.assert_called_once_with(old_prompt + "cd /home")

    def test_script_uses_updated_prompt(self):
        """Команды скрипта выводятся с актуальным путём в приглашении."""
        self.create_window()
        with patch("gui.Path.read_text", return_value="cd /home\ncd student"):
            self.window.run_script("startup.txt")
        self.assertTrue(self.window.prompt.endswith(":/home/student$ "))
        second_line = self.window.write.call_args_list[1].args[0]
        self.assertTrue(second_line.endswith(":/home$ cd student"))
        self.window.prompt_label.config.assert_called_with(
            text=self.window.prompt
        )

    def test_failed_cd_keeps_prompt(self):
        """Ошибка перехода сохраняет текущий каталог и приглашение."""
        self.create_window()
        self.window.run_line("cd /home")
        old_prompt = self.window.prompt
        self.window.run_line("cd student/missing")
        self.assertEqual(self.window.prompt, old_prompt)
        self.assertEqual(self.window.shell.current_path, "/home")
        self.assertIn(
            "no such file or directory", self.window.write.call_args.args[0]
        )

    def test_cd_demo_stops_at_file(self):
        """Скрипт останавливается при попытке перейти в файл."""
        self.create_window()
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        self.window.run_script(str(scripts / "cd_demo.txt"))
        self.assertEqual(
            self.window.shell.current_path, "/home/student/project/docs"
        )
        self.window.write.assert_any_call(
            "cd: /home/student/notes.txt: not a directory."
        )
        self.assertIn("execution stopped", self.window.write.call_args.args[0])

    def test_script_without_vfs_stops_on_first_command(self):
        """Команда, требующая VFS, останавливает стартовый скрипт."""
        self.create_window()
        scripts = Path(__file__).resolve().parent.parent / "scripts"
        self.window.shell = Shell(None)
        self.window.run_script(str(scripts / "no_errors.txt"))
        output = [call.args[0] for call in self.window.write.call_args_list]
        self.assertEqual(output[-3:], [
            self.window.prompt + "ls 123 123",
            "ls: VFS is not loaded.",
            "Script error at line 4, execution stopped.",
        ])

    def test_exit_script_closes_window(self):
        """Команда exit в стартовом скрипте закрывает окно."""
        self.create_window()
        self.window.root = Mock()
        with patch("gui.Path.read_text", return_value="ls\nexit\nls"):
            self.window.run_script("startup.txt")
        self.window.root.destroy.assert_called_once_with()
        self.assertEqual(
            self.window.write.call_args_list[-1].args[0],
            self.window.prompt + "exit",
        )
        self.assertEqual(self.window.write.call_count, 3)

    def test_stage3_demo_with_minimal_vfs(self):
        """Скрипт с минимальной VFS доходит до ошибки exit с аргументами."""
        self.create_window()
        base = Path(__file__).resolve().parent.parent
        self.window.shell = Shell(get_vfs(str(base / "vfs" / "minimal.xml")))
        self.window.run_script(str(base / "scripts" / "stage3_demo.txt"))
        self.window.write.assert_any_call("exit: too many arguments.")
        self.assertIn("execution stopped", self.window.write.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
