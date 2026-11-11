import asyncio

from core.http_client import HttpClient
from hw2.main.data.dependencies_tree_builder import DependenciesTreeBuilder
from hw2.main.data.external_api.dependencies_collector import DependenciesCollector


async def main() -> None:
    http_client = HttpClient()
    deps_collector = DependenciesCollector(http_client)
    deps_tree_builder = DependenciesTreeBuilder(deps_collector)
    try:
        resp = await deps_tree_builder("pypi.org/simple", "aiogram", "3.31.0")
        print(resp)
    finally:
        http_client.close()

if __name__ == "__main__":
    asyncio.run(main())