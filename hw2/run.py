from core.http_client import HttpClient
from hw2.main.data.external_api.dependencies_collector import DependenciesCollector


def main() -> None:
    http_client = HttpClient()
    deps_collector = DependenciesCollector(http_client)

    resp = deps_collector.get_pypi_dependencies_for_package("pypi.org/simple", "aiogram")

    print(
       *[(key, value) for key, value in resp[0].items()], sep="\n"
    )

if __name__ == "__main__":
    main()