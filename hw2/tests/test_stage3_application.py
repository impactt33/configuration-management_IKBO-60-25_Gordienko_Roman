"""Проверки выбора репозитория и ограничений в приложении."""

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import httpx

from hw2.core.http_client import HttpClient
from hw2.main.domain.entities.parameters import PackageManagerParameters
from hw2.run import build_tree


class TestStage3Application(unittest.IsolatedAsyncioTestCase):
    """Оба режима используют настоящий BFS, сеть подменяется на границе."""

    async def test_file_mode_never_creates_http_client(self):
        """Локальный репозиторий работает при запрете создания HTTP-клиента."""
        params = PackageManagerParameters(
            name="A", version="1.0", test_mode=True, max_depth=1,
            repo_url=str(Path(__file__).parents[1]
                         / "examples" / "branching.json"),
        )
        with patch("hw2.run.HttpClient", side_effect=AssertionError("HTTP")):
            result = await build_tree(params)
        self.assertEqual(result.as_adjacency_list(), {
            "A==1.0": ["B==1.5", "C==1.0"],
            "B==1.5": [], "C==1.0": [],
        })

    async def test_network_mode_uses_custom_url_version_depth_and_filter(self):
        """Настройки доходят до сетевого сборщика и ограничивают запросы."""
        repo = "https://example.invalid/custom/simple/"
        wheel = {
            "filename": "root-2.0-py3-none-any.whl",
            "url": "https://example.invalid/files/root.whl",
            "core-metadata": True,
        }
        responses = {
            repo + "root/": httpx.Response(200, json={"files": [wheel]}),
            wheel["url"] + ".metadata": httpx.Response(200, content=(
                b"Requires-Dist: Filtered\nRequires-Dist: Child>=1\n\n"
            )),
            repo + "child/": httpx.Response(
                200, json={"versions": ["1.0", "1.5"]},
            ),
        }
        http = Mock(spec=HttpClient)
        http.get.side_effect = lambda url, **kwargs: responses[url]
        params = PackageManagerParameters(
            name="Root", version="2.0", repo_url=repo,
            max_depth=1, filter="FILTERED",
        )
        with patch("hw2.run.HttpClient", return_value=http):
            result = await build_tree(params)
        self.assertEqual(result.as_adjacency_list(), {
            "Root==2.0": ["Child==1.5"], "Child==1.5": [],
        })
        self.assertEqual(http.get.call_count, 3)
        http.close.assert_called_once_with()

    async def test_network_client_is_closed_after_failure(self):
        """Сбой запроса не оставляет открытый HTTP-клиент."""
        http = Mock(spec=HttpClient)
        http.get.side_effect = httpx.ConnectError("Repository unavailable")
        params = PackageManagerParameters(name="Root", version="1.0")
        with patch("hw2.run.HttpClient", return_value=http):
            with self.assertRaises(httpx.ConnectError):
                await build_tree(params)
        http.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
