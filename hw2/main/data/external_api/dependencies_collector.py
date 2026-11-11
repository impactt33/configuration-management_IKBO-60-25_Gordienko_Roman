from email.parser import BytesParser
from email.policy import compat32

from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import Version

from hw2.core.exceptions import HttpError
from hw2.core.http_client import HttpClient
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.exceptions import VersionNotFoundError

SIMPLE_API_HEADER = {
    "Accept": "application/vnd.pypi.simple.v1+json",
}


class DependenciesCollector:
    """Получает прямые зависимости из метаданных файлов репозитория."""

    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_pypi_dependencies_for_package(
        self, host: str, name: str, version: str,
    ) -> list[str] | ExceptionCause:
        package_file = self._request_for_package_files(host, name, version)

        if isinstance(package_file, ExceptionCause):
            return package_file

        package_metadata = self._request_for_package_metadata(package_file)

        if isinstance(package_metadata, ExceptionCause):
            return package_metadata

        return self._parse_dependencies_from_metadata(package_metadata)

    def get_available_versions_of_package(
        self, host: str, package_name: str,
    ) -> list[str] | ExceptionCause:
        index = self._request_for_package(host, package_name)

        if isinstance(index, ExceptionCause):
            return index

        return index["versions"]

    def _request_for_package(
        self, host: str, package_name: str,
    ) -> dict | ExceptionCause:
        url = self._create_simple_api_supported_pypi_url(host, package_name)
        try:
            response = self.http_client.get(
                url, headers=SIMPLE_API_HEADER, follow_redirects=True,
            )
        except HttpError as err:
            return ExceptionCause(
                status_code=err.status,
                cause=str(err)
            )

        return response.json()

    def _request_for_package_files(
        self, host: str, package_name: str, version: str,
    ) -> dict | ExceptionCause:
        """Выбирает файл релиза по нормализованным имени и версии."""
        index = self._request_for_package(host, package_name)
        if isinstance(index, ExceptionCause):
            return index

        expected = canonicalize_name(package_name), Version(version)
        matches = []
        for file in index["files"]:
            filename = file.get("filename")
            if not isinstance(filename, str):
                continue
            if self._parse_distribution_filename(filename) == expected:
                matches.append(file)

        if not matches:
            raise VersionNotFoundError(
                f"No distribution file found for {package_name}=={version}"
            )

        return max(matches, key=lambda file: (
            bool(file.get("core-metadata", file.get("dist-info-metadata"))),
            file["filename"].endswith(".whl"),
        ))

    @staticmethod
    def _parse_distribution_filename(
        filename: str,
    ) -> tuple[str, Version] | None:
        """Разбирает wheel или sdist, пропуская некорректные имена."""
        try:
            if filename.endswith(".whl"):
                name, version, *_ = parse_wheel_filename(filename)
            elif filename.endswith((".tar.gz", ".zip")):
                name, version = parse_sdist_filename(filename)
            else:
                return None
        except (InvalidWheelFilename, InvalidSdistFilename):
            return None
        return name, version

    def _request_for_package_metadata(
        self, package_file: dict,
    ) -> bytes | ExceptionCause:
        metadata_url = self._create_simple_api_supported_pypi_metadata_url(
            package_file["url"],
        )

        try:
            response = self.http_client.get(
                metadata_url, follow_redirects=True,
            )
        except HttpError as err:
            return ExceptionCause(
                status_code=err.status,
                cause=str(err)
            )

        return response.content

    @staticmethod
    def _parse_dependencies_from_metadata(package_metadata: bytes) -> list[str]:
        parser = BytesParser(policy=compat32)
        parsed_metadata = parser.parsebytes(package_metadata)

        return parsed_metadata.get_all("Requires-Dist", [])

    @staticmethod
    def _create_simple_api_supported_pypi_url(
        repo_url: str,
        package_name: str,
    ) -> str:
        base_url = repo_url.rstrip("/")
        if "://" not in base_url:
            base_url = f"https://{base_url}"
        return f"{base_url}/{canonicalize_name(package_name)}/"

    @staticmethod
    def _create_simple_api_supported_pypi_metadata_url(
        package_full_url: str,
    ) -> str:
        return package_full_url + ".metadata"
