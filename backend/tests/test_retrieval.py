"""Phase 2 acceptance checks as pytest (playbook/02_data_layer.md)."""
from __future__ import annotations


def test_get_part_ps11752778_reality() -> None:
    """NOTE: playbook said 'door balance link kit'; live site says refrigerator
    door shelf bin (see playbook/DEVIATIONS.md #10). Reality wins."""
    from backend.app.retrieval import get_part
    part = get_part("PS11752778")
    assert part is not None
    assert part["mpn"] == "WPW10321304"
    assert "Door Shelf Bin" in part["title"]
    assert part["appliance_type"] == "refrigerator"
    assert part["price"] and part["price"] > 0
    assert part["availability"] == "In Stock"


def test_get_part_by_mpn_and_replaced_mpn() -> None:
    from backend.app.retrieval import get_part
    assert get_part("WPW10321304")["ps_number"] == "PS11752778"
    via_old = get_part("W10321303")             # superseded number from replaces list
    assert via_old is not None and via_old["ps_number"] == "PS11752778"


def test_check_compat_honest_no_match() -> None:
    """Fridge bin vs dishwasher model: data must answer no_match_found (with
    evidence), never a hallucinated yes. (DEVIATIONS.md #10 - playbook's
    expected verified_fit contradicted the live site.)"""
    from backend.app.retrieval import check_compat
    res = check_compat("PS11752778", "WDT780SAEM1")
    assert res.status == "no_match_found"
    assert res.evidence["model_seen_in_data"] is True
    assert res.evidence["parts_verified_for_model"] >= 5


def test_check_compat_verified_fit() -> None:
    from backend.app.retrieval import check_compat
    res = check_compat("PS3406971", "WDT780SAEM1")   # lower dishrack wheel, model page
    assert res.status == "verified_fit"
    res2 = check_compat("PS11752778", "10640262010")  # Kenmore fridge, cross-ref table
    assert res2.status == "verified_fit"
    assert res2.evidence["source"] in ("crossref", "cross_ref")


def test_check_compat_unknown_model_and_part() -> None:
    from backend.app.retrieval import check_compat
    assert check_compat("PS11752778", "FAKE123").status == "unknown_model"
    assert check_compat("PS99999999", "WDT780SAEM1").status == "unknown_part"


def test_parts_for_model() -> None:
    from backend.app.retrieval import parts_for_model
    parts = parts_for_model("WDT780SAEM1")
    assert len(parts) >= 5
    assert all(p["appliance_type"] == "dishwasher" for p in parts)


def test_search_repairs_ice_maker_rank_order() -> None:
    from backend.app.retrieval import guide_causes, search_repairs
    chunks = search_repairs("ice maker not making ice", "refrigerator")
    assert chunks, "no repair chunks returned"
    top = chunks[0]
    assert "ice" in top["symptom"].lower()
    causes = guide_causes(top["guide_id"])
    assert [c["rank"] for c in causes] == sorted(c["rank"] for c in causes)
    assert len(causes) >= 4


def test_hybrid_search_spray_arm() -> None:
    from backend.app.retrieval import hybrid_search
    results = hybrid_search("thing that sprays water bottom of dishwasher", "dishwasher")
    top3 = " ".join(p["title"].lower() for p in results[:3])
    assert "spray arm" in top3, f"expected a spray arm in top 3, got: {top3}"


def test_keyword_search_scoped_by_appliance() -> None:
    from backend.app.retrieval import keyword_search
    results = keyword_search("water filter", "refrigerator")
    assert results and all(p["appliance_type"] == "refrigerator" for p in results)


def test_support_snippets() -> None:
    from backend.app.retrieval import search_support
    hits = search_support("does this fit my fridge door", "PS11752778")
    assert hits and all(h["ps_number"] == "PS11752778" for h in hits)
