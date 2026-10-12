"""Small atlas download and optional official FSL template; no private data."""
from pathlib import Path
import urllib.request
import shutil
import tarfile
import subprocess
import hashlib
from .common import sha256, write_json
from .atlas import ATLAS_NAME, LUT_NAME
ATLAS_COMMIT = "27826640aa5d1644e135d8be99ae25194352428c"
BASE = f"https://raw.githubusercontent.com/compneurobilbao/nextbrain-mni-atlas/{ATLAS_COMMIT}/"
EXPECTED_SHA256 = {
    ATLAS_NAME: "0fd00a035070d26cf848c6bb4b36d409ab1bb355c9186f0e1faba6793d54bdab",
    LUT_NAME: "607b55566ec38c9af2a6b6fa29f014265a5a80025cb89c301ccd59ccc9f4f78c",
}
FSL_URL = "https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/noarch/fsl-data_standard-2208.0-0.tar.bz2"
FSL_SHA = "2faefb4d366b6427cbf4e5c3e54c63c040ec9bcfe11b1f10848f89a1571b828a"

def source_checksum(path):
    path = Path(path)
    if path.suffix in [".txt", ".md"]:
        # Git autocrlf changes checkout bytes, not source text. Record actual
        # bytes separately, and validate text against the pinned LF Git blob.
        return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return sha256(path)

def retrieve(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    request = urllib.request.Request(url, headers={"User-Agent": "NextBrain-research/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    temporary.replace(destination)

def download(root, reference=False):
    root = Path(root)
    source = root / "data/source_atlas"
    provenance_path = root / "data/provenance.json"
    import json
    provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else {"assets": []}
    assets = {a["path"]: a for a in provenance["assets"]}
    for name in (ATLAS_NAME, LUT_NAME, "README.md"):
        path = source / name
        if path.exists() and (source / ".git").exists():
            actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
            if actual != ATLAS_COMMIT:
                raise ValueError("Source checkout differs from pinned atlas commit; do not overwrite")
        if not path.exists():
            retrieve(BASE + name, path)
        if name in EXPECTED_SHA256 and source_checksum(path) != EXPECTED_SHA256[name]:
            raise ValueError(f"Pinned atlas checksum mismatch: {name}")
        key = path.relative_to(root).as_posix()
        if key in assets and assets[key]["sha256"] != sha256(path):
            raise ValueError(f"Source changed: {key}")
        assets[key] = dict(path=key, url=BASE + name, commit=ATLAS_COMMIT, sha256=sha256(path), canonical_sha256=source_checksum(path),
                           bytes=path.stat().st_size, license="No explicit LICENSE in pinned MNI atlas repository; raw files excluded from publication")
    if reference:
        target = root / "data/reference/MNI152_T1_1mm.nii.gz"
        archive = root / "data/download_cache/fsl-data_standard-2208.0-0.tar.bz2"
        if not target.exists():
            if not archive.exists():
                print("Downloading official FSL standard template package (187 MB)", flush=True)
                retrieve(FSL_URL, archive)
            if sha256(archive) != FSL_SHA:
                raise ValueError("Official FSL archive checksum mismatch")
            target.parent.mkdir(parents=True, exist_ok=True)
            # Extract only regular-file members to explicitly chosen destinations.
            with tarfile.open(archive, "r:bz2") as tar:
                matches = [m for m in tar.getmembers() if m.isfile() and m.name.endswith("/MNI152_T1_1mm.nii.gz")]
                if len(matches) != 1:
                    raise ValueError(f"Expected one FSL reference member, found {len(matches)}")
                with tar.extractfile(matches[0]) as input_file, target.open("wb") as output:
                    shutil.copyfileobj(input_file, output)
                for member in tar.getmembers():
                    if member.isfile() and "license" in member.name.lower():
                        dest = target.parent / ("FSL_" + Path(member.name).name)
                        with tar.extractfile(member) as src, dest.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
        key = target.relative_to(root).as_posix()
        assets[key] = dict(path=key, url=FSL_URL, archive_sha256=FSL_SHA,
                           sha256=sha256(target), bytes=target.stat().st_size,
                           license="FSL noncommercial research terms; see https://fsl.fmrib.ox.ac.uk/fsl/docs/license.html",
                           role="MNI152 population-average T1 reference; not a patient")
    provenance["assets"] = list(assets.values())
    provenance["retrieval_date"] = "2026-10-12"
    write_json(provenance_path, provenance)
    return provenance
