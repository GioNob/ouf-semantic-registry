"""Load CI archives and extract the migration inventory from the actual image."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def prepare(directory, destination, predecessor):
    manifest = json.loads((directory / "manifest.json").read_text())
    archive = directory / "image.tar.gz"
    image = manifest["imageId"]
    revision = manifest["testedCommit"]
    require(re.fullmatch(r"sha256:[a-f0-9]{64}", image) and re.fullmatch(r"[a-f0-9]{40}", revision),
            "Invalid candidate or predecessor identity")
    require(manifest["schema"] == "ouf.semantic-tested-image.v1" and
            manifest["repository"] == os.environ["GITHUB_REPOSITORY"], "Wrong image producer")
    if predecessor:
        commit = output("git", "rev-parse", "--verify", os.environ["PREDECESSOR_COMMIT"] + "^{commit}")
        require(manifest["reviewedSourceCommit"] == commit and
                manifest["testedTree"] == output("git", "rev-parse", commit + "^{tree}") and
                manifest["workflowRunId"] == os.environ["PREDECESSOR_RUN"] and
                image == os.environ["PREDECESSOR_IMAGE_ID"], "Installed predecessor identity mismatch")
    else:
        require(revision == output("git", "rev-parse", "HEAD") == os.environ["GITHUB_SHA"] and
                manifest["workflowRunId"] == os.environ["GITHUB_RUN_ID"], "Candidate is not this checkout")
    with archive.open("rb") as stream:
        require(hashlib.file_digest(stream, "sha256").hexdigest() == manifest["archiveSha256"],
                "Image archive checksum mismatch")
    subprocess.run(["docker", "load", "-i", archive], check=True, stdout=sys.stderr)
    label = output("docker", "image", "inspect", image, "--format",
                   '{{index .Config.Labels "org.opencontainers.image.revision"}}')
    require(label == revision == manifest["imageRevisionLabel"], "Image revision mismatch")
    container = output("docker", "create", "--network", "none", image)
    jar = destination / "application.jar"
    try:
        subprocess.run(["docker", "cp", container + ":/app/application.jar", jar], check=True)
    finally:
        subprocess.run(["docker", "rm", container], check=True, stdout=sys.stderr)
    entries = []
    sql = destination / "sql"
    lib = destination / "lib"
    sql.mkdir()
    lib.mkdir()
    with ZipFile(jar) as package:
        for entry in package.infolist():
            if re.fullmatch(r"BOOT-INF/lib/[\w.+-]+\.jar", entry.filename):
                # Run the Flyway engine and JDBC driver shipped with this image.
                (lib / Path(entry.filename).name).write_bytes(package.read(entry))
                continue
            if not entry.filename.startswith("BOOT-INF/classes/db/migration/") or entry.is_dir():
                continue
            name = entry.filename.rsplit("/", 1)[1]
            require(entry.filename == "BOOT-INF/classes/db/migration/" + name and
                    re.fullmatch(r"V[1-9][0-9]*__[A-Za-z0-9_]+\.sql", name),
                    "Unexpected migration resource")
            raw = package.read(entry)
            (sql / name).write_bytes(raw)
            entries.append({"name": name, "sha256": hashlib.sha256(raw).hexdigest()})
    jar.unlink()
    require(entries and sorted(entries, key=lambda e: e["name"]) ==
            sorted(manifest["flywayMigrations"], key=lambda e: e["name"]), "Migration inventory mismatch")
    print(image)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] == "predecessor")
