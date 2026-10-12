from nextbrain_research.download import source_checksum
from nextbrain_research.common import sha256
import json
import pytest

def test_text_checksum_accepts_git_crlf_but_detects_content_changes(tmp_path):
    lf, crlf = tmp_path / "lf.txt", tmp_path / "crlf.txt"
    lf.write_bytes(b"48 Left-head_of_caudate 145 160 110 0\n")
    crlf.write_bytes(b"48 Left-head_of_caudate 145 160 110 0\r\n")
    assert sha256(lf) != sha256(crlf)
    assert source_checksum(lf) == source_checksum(crlf)
    crlf.write_bytes(b"49 Left-head_of_caudate 145 160 110 0\r\n")
    assert source_checksum(lf) != source_checksum(crlf)

def test_binary_checksum_does_not_normalize(tmp_path):
    p = tmp_path / "labels.nii.gz"
    p.write_bytes(b"binary\r\nnot-text")
    assert source_checksum(p) == sha256(p)

def test_published_provenance_accepts_new_checkout_line_endings(tmp_path, monkeypatch):
    import nextbrain_research.download as module
    source = tmp_path / "data/source_atlas"
    source.mkdir(parents=True)
    payloads = {module.ATLAS_NAME:b"binary atlas fixture", module.LUT_NAME:b"0 Unknown 0 0 0 0\r\n", "README.md":b"# Fixture\r\n"}
    entries = []
    for name, data in payloads.items():
        path = source / name
        path.write_bytes(data)
        entries.append(dict(path=path.relative_to(tmp_path).as_posix(), sha256=sha256(path), canonical_sha256=source_checksum(path)))
    monkeypatch.setattr(module,"EXPECTED_SHA256",{name:source_checksum(source/name) for name in [module.ATLAS_NAME,module.LUT_NAME]})
    (tmp_path / "data/provenance.json").write_text(json.dumps(dict(assets=entries)))
    for name in [module.LUT_NAME,"README.md"]:
        (source/name).write_bytes(payloads[name].replace(b"\r\n",b"\n"))
    result = module.download(tmp_path)
    assert len(result["assets"]) == 3
    (source/module.LUT_NAME).write_bytes(b"1 Changed label 0 0 0 0\n")
    with pytest.raises(ValueError,match="checksum"):
        module.download(tmp_path)
