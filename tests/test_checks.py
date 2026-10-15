import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.checks import run_checks, scope_of  
from backend.store import load_packet  
from backend.trace import proof_tree  

PACKET = load_packet()
CHECKS_V3 = run_checks(PACKET, "v3")


def _ids(prefix):
    return [c["id"] for c in CHECKS_V3 if c["id"].startswith(prefix)]


def test_zero_basis_rsu_lots_are_blockers():
   
    blockers = [c for c in CHECKS_V3 if c["id"].startswith("zero-basis:") and c["severity"] == "blocker"]
    assert len(blockers) >= 3


def test_partially_read_document_is_a_blocker():
    assert any(c["id"] == "partial-extraction:D31" and c["severity"] == "blocker" for c in CHECKS_V3)


def test_low_confidence_donation_is_flagged():
   
    assert any("low-confidence:" in c["id"] for c in CHECKS_V3)


def test_every_line_traces_or_computes():
   
    for line in PACKET.lines("v3"):
        assert line.get("sources") or line.get("inputs") or line.get("rule"), line["key"]


def test_proof_tree_reaches_source_documents():
    tree = proof_tree(PACKET, "v3", "F1040.1a")
    assert tree is not None and tree["sources"], "wages must trace to W-2 values"
    assert all(s["document_id"].startswith("D") for s in tree["sources"])


def test_scope_mapping():
    assert scope_of({"form": "F8949"}) == "Capital gains"
    assert scope_of({"form": "SchC"}) == "Business (Sch C)"
    assert scope_of({"form": "SchCA540NR"}) == "California"
