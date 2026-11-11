from hw2.core.exceptions import HttpError
from hw2.core.http_client import HttpClient
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.exceptions import PackageNotFoundError

SIMPLE_API_HEADER = {
    "Accept": "application/vnd.pypi.simple.v1+json",
}

class DependenciesCollector:
    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_pypi_dependencies_for_package(self, host: str, name: str) -> list[str] | ExceptionCause:
        url = self.create_simple_api_supported_pypi_url(host, name)
        try:
            response = self.http_client.get(url, headers=SIMPLE_API_HEADER, follow_redirects=True)
        except HttpError as err:
            return ExceptionCause(
                status_code=err.status,
                cause=str(err)
            )

        index = response.json()
        files = index["files"]

        for file in files:
            filename = file.get("filename", None)

            if not filename:
                raise PackageNotFoundError()

            package_version = filename.split("-")[1]

    @staticmethod
    def create_simple_api_supported_pypi_url(
        repo_url: str,
        package_name: str,
    ) -> str:
        return f"https://{repo_url}/{package_name}"