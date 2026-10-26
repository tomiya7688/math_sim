"""Pin secure Python packaging tools and reject the compromised emSign root."""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import ssl
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

MINIMUM_PIP = (26, 2, 2)
MINIMUM_CERTIFI = (2026, 10, 19)
PIP_WHEEL = (
    "https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/"
    "pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"
)
EM_SIGN_ECC_ROOT_SHA256 = (
    "86A1ECBA089C4A8D3BBE2734C612BA341D813E043CF9E8A862CD5C57A36BBE6B"
)


def is_version_at_least(value: str, minimum: tuple[int, ...]) -> bool:
    from pip._vendor.packaging.version import InvalidVersion, Version

    try:
        return Version(value) >= Version(".".join(str(part) for part in minimum))
    except InvalidVersion as error:
        raise RuntimeError(f"unrecognized package version: {value}") from error


def certificate_fingerprints(pem: bytes) -> set[str]:
    fingerprints = set()
    for match in re.finditer(
        rb"-----BEGIN CERTIFICATE-----\s*(.*?)\s*-----END CERTIFICATE-----",
        pem,
        flags=re.DOTALL,
    ):
        der = base64.b64decode(re.sub(rb"\s+", b"", match.group(1)))
        fingerprints.add(hashlib.sha256(der).hexdigest().upper())
    return fingerprints


def is_der_certificate(data: bytes) -> bool:
    def read_element(offset: int) -> tuple[int, int] | None:
        if offset + 2 > len(data):
            return None
        tag, length = data[offset : offset + 2]
        header = 2
        if length & 0x80:
            length_size = length & 0x7F
            if (
                not length_size
                or length_size > 4
                or offset + header + length_size > len(data)
            ):
                return None
            length = int.from_bytes(
                data[offset + header : offset + header + length_size], "big"
            )
            header += length_size
        end = offset + header + length
        if end > len(data):
            return None
        return tag, end

    outer = read_element(0)
    if not outer or outer[0] != 0x30 or outer[1] != len(data):
        return False
    offset = 2
    outer_length = data[1]
    if outer_length & 0x80:
        offset += outer_length & 0x7F
    for expected_tag in (0x30, 0x30, 0x03):
        element = read_element(offset)
        if not element or element[0] != expected_tag:
            return False
        offset = element[1]
    return offset == len(data)


def package_certificate_fingerprints(data: bytes) -> set[str]:
    fingerprints = certificate_fingerprints(data)
    if fingerprints:
        return fingerprints
    if is_der_certificate(data):
        return {hashlib.sha256(data).hexdigest().upper()}
    return set()


def assert_root_absent(label: str, fingerprints: set[str]) -> None:
    if not fingerprints:
        raise RuntimeError(f"could not read certificates from {label}")
    if EM_SIGN_ECC_ROOT_SHA256 in fingerprints:
        raise RuntimeError(f"affected emSign ECC Root CA-G3 remains trusted in {label}")
    print(
        f"{label}: affected emSign root absent ({len(fingerprints)} certificates checked)"
    )


def pip_config_items():
    from pip._internal.configuration import Configuration

    configuration = Configuration(isolated=False)
    configuration.load()
    for key, value in configuration.items():
        if isinstance(value, dict):
            yield from value.items()
        else:
            yield key, value


def verify_bootstrap_trust(
    certifi_required: bool = False, require_versions: bool = False
) -> None:
    import pip
    import pip._vendor.certifi as pip_certifi

    if require_versions and not is_version_at_least(pip.__version__, MINIMUM_PIP):
        raise RuntimeError(f"pip {pip.__version__} is below required 26.2.2")
    print(f"pip: {pip.__version__}")
    assert_root_absent(
        f"pip bundled CA ({pip_certifi.where()})",
        certificate_fingerprints(Path(pip_certifi.where()).read_bytes()),
    )

    for key, value in pip_config_items():
        normalized_key = key.lower()
        if normalized_key.endswith("trusted-host") and value:
            raise RuntimeError(f"pip TLS verification is disabled in {key}")
        if not normalized_key.endswith("cert") or "client-cert" in normalized_key:
            continue
        if value:
            ca_path = Path(os.path.expandvars(value)).expanduser()
            assert_root_absent(
                f"pip configured CA ({key}: {ca_path})",
                certificate_fingerprints(ca_path.read_bytes()),
            )

    try:
        import certifi
    except ImportError:
        if certifi_required:
            raise RuntimeError(
                "certifi is required after the security bootstrap"
            ) from None
        print("certifi: not installed")
    else:
        if require_versions and not is_version_at_least(
            certifi.__version__, MINIMUM_CERTIFI
        ):
            raise RuntimeError(
                f"certifi {certifi.__version__} is below required 2026.10.19"
            )
        print(f"certifi: {certifi.__version__} ({certifi.where()})")
        assert_root_absent(
            f"certifi CA ({certifi.where()})",
            certificate_fingerprints(Path(certifi.where()).read_bytes()),
        )

    if sys.platform == "win32" and hasattr(ssl, "enum_certificates"):
        system_fingerprints = {
            hashlib.sha256(certificate).hexdigest().upper()
            for certificate, encoding, _trust in ssl.enum_certificates("ROOT")
            if encoding == "x509_asn"
        }
        assert_root_absent("Windows ROOT certificate store", system_fingerprints)
    else:
        ca_environment = {
            name: os.environ.pop(name, None)
            for name in ("SSL_CERT_FILE", "SSL_CERT_DIR")
        }
        try:
            system_context = ssl.create_default_context()
        finally:
            os.environ.update(
                {
                    name: value
                    for name, value in ca_environment.items()
                    if value is not None
                }
            )
        system_fingerprints = {
            hashlib.sha256(certificate).hexdigest().upper()
            for certificate in system_context.get_ca_certs(binary_form=True)
        }
        assert_root_absent("Python default system trust store", system_fingerprints)

    effective_context = ssl.create_default_context()
    effective_fingerprints = {
        hashlib.sha256(certificate).hexdigest().upper()
        for certificate in effective_context.get_ca_certs(binary_form=True)
    }
    assert_root_absent("Python effective TLS trust store", effective_fingerprints)


def verify_package_sources() -> None:
    for key, value in pip_config_items():
        normalized_key = key.lower()
        if not value:
            continue
        if normalized_key.endswith(("extra-index-url", "find-links")):
            raise RuntimeError(f"unapproved extra pip package source: {key}")
        if normalized_key.endswith("no-index") and str(value).lower() not in {
            "0",
            "false",
            "no",
            "off",
        }:
            raise RuntimeError("pip package index is disabled")
        if normalized_key.endswith("index-url"):
            for configured_url in str(value).split():
                parsed = urlsplit(configured_url)
                if (
                    parsed.scheme.lower() != "https"
                    or parsed.hostname != "pypi.org"
                    or parsed.path.rstrip("/") != "/simple"
                ):
                    raise RuntimeError(
                        f"pip index must be https://pypi.org/simple: {key}"
                    )


def ensure_secure_tools() -> None:
    import pip

    verify_bootstrap_trust()
    verify_package_sources()
    if not is_version_at_least(pip.__version__, MINIMUM_PIP):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                PIP_WHEEL,
            ],
            check=True,
        )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "certifi>=2026.10.19",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--verify-only",
            "--require-certifi",
            "--require-versions",
        ],
        check=True,
    )


def check_package(path: Path) -> None:
    root = path.resolve()
    if not root.is_dir():
        raise RuntimeError(f"package directory does not exist: {root}")
    app_executable = root / "math_sim.exe"
    if not app_executable.is_file():
        raise RuntimeError(f"packaged Windows app is missing: {app_executable}")
    bundles = []
    certificate_suffixes = {".pem", ".crt", ".cer", ".der"}
    for bundle in root.rglob("*"):
        if bundle.is_file() and bundle.suffix.lower() in certificate_suffixes:
            bundles.append(
                (
                    str(bundle.relative_to(root)),
                    package_certificate_fingerprints(bundle.read_bytes()),
                )
            )
    for archive in root.rglob("*.zip"):
        try:
            with zipfile.ZipFile(archive) as contents:
                for name in contents.namelist():
                    if Path(name).suffix.lower() in certificate_suffixes:
                        bundles.append(
                            (
                                f"{archive.relative_to(root)}!/{name}",
                                package_certificate_fingerprints(contents.read(name)),
                            )
                        )
        except zipfile.BadZipFile as error:
            raise RuntimeError(
                f"cannot inspect ZIP package {archive}: {error}"
            ) from error

    archives = [app_executable] if app_executable.is_file() else []
    archives.extend(root.rglob("*.pkg"))
    if archives:
        try:
            from PyInstaller.archive.readers import CArchiveReader
        except ImportError as error:
            raise RuntimeError(
                "PyInstaller is required to inspect packaged CArchive contents"
            ) from error
        for archive_path in archives:
            try:
                archive = CArchiveReader(str(archive_path))
            except Exception as error:
                raise RuntimeError(
                    f"cannot inspect PyInstaller archive {archive_path}: {error}"
                ) from error
            for name in archive.toc:
                if Path(name).suffix.lower() in certificate_suffixes:
                    bundles.append(
                        (
                            f"{archive_path.relative_to(root)}!/{name}",
                            package_certificate_fingerprints(archive.extract(name)),
                        )
                    )

    if not bundles:
        print(
            "package: no CA certificate bundles found in files, ZIP, or PyInstaller CArchive"
        )
        return
    for name, fingerprints in bundles:
        assert_root_absent(f"packaged CA certificate ({name})", fingerprints)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--require-certifi", action="store_true")
    parser.add_argument("--require-versions", action="store_true")
    parser.add_argument("--check-package", type=Path)
    args = parser.parse_args()
    try:
        if args.check_package:
            check_package(args.check_package)
        else:
            if not args.verify_only:
                ensure_secure_tools()
            else:
                verify_bootstrap_trust(
                    certifi_required=args.require_certifi,
                    require_versions=args.require_versions,
                )
    except (
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        ssl.SSLError,
    ) as error:
        print(f"Python CA security check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
