"""Устанавливает проверенный Linux-бинарник D2 только в hw2/.tools."""

import hashlib
from io import BytesIO
from pathlib import Path, PurePosixPath
import platform
import tarfile
from urllib.request import urlopen


VERSION = "0.9.0"
BUILDS = {
    "x86_64": (
        "amd64",
        "5669ddc46b99e942cc96078f4a4e36d5e62103348f4c05179ede27802fdd87a9",
    ),
    "aarch64": (
        "arm64",
        "ac2c028697199479acb321db1e3d68caee9f2ba492ed73caa3cd13f3829bf913",
    ),
}


def install() -> Path:
    """Проверяет SHA-256 архива и извлекает только исполняемый файл."""
    if platform.system() != "Linux" or platform.machine() not in BUILDS:
        raise RuntimeError("Для этой системы установите D2 по d2lang.com")
    architecture, expected_hash = BUILDS[platform.machine()]
    filename = f"d2-v{VERSION}-linux-{architecture}.tar.gz"
    base = f"https://github.com/d2lang/d2/releases/download/v{VERSION}"
    url = f"{base}/{filename}"
    with urlopen(url, timeout=60) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != expected_hash:
        raise RuntimeError("SHA-256 архива D2 не совпадает с GitHub Release")
    with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as package:
        member = next(
            item for item in package.getmembers()
            if item.isfile()
            and PurePosixPath(item.name).parts[-2:] == ("bin", "d2")
        )
        with package.extractfile(member) as binary:
            content = binary.read()
    output = Path(__file__).resolve().parents[1] / ".tools" / "d2"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    output.chmod(0o755)
    return output


if __name__ == "__main__":
    print(install())
