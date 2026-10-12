from nextbrain_research.download import source_checksum
from nextbrain_research.common import sha256

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
