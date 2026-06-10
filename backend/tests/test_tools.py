"""Each tool against the test DB: happy path, not-found, malformed input."""

from __future__ import annotations

import pydantic
import pytest

from backend.app import tools


def test_search_parts_happy() -> None:
    out = tools.run_tool("search_parts", {"query": "lower spray arm", "appliance_type": "dishwasher"})
    assert out["data"]["results"]
    assert out["ui_block"]["type"] == "product_list"


def test_get_part_details_found_and_missing() -> None:
    ok = tools.run_tool("get_part_details", {"part_identifier": "PS11752778"})
    assert ok["data"]["found"] and ok["ui_block"]["type"] == "product_card"
    missing = tools.run_tool("get_part_details", {"part_identifier": "PS99999999"})
    assert missing["data"]["found"] is False and missing["ui_block"] is None


def test_check_compatibility_verdicts() -> None:
    fit = tools.run_tool(
        "check_compatibility", {"part_identifier": "PS3406971", "model_number": "WDT780SAEM1"}
    )
    assert fit["data"]["status"] == "verified_fit"
    miss = tools.run_tool(
        "check_compatibility", {"part_identifier": "PS11752778", "model_number": "WDT780SAEM1"}
    )
    assert miss["data"]["status"] == "no_match_found"
    assert miss["data"]["parts_verified_for_model_sample"]


def test_diagnose_issue_ranked() -> None:
    out = tools.run_tool(
        "diagnose_issue",
        {
            "symptom_description": "ice maker not making ice",
            "appliance_type": "refrigerator",
            "brand": "Whirlpool",
        },
    )
    ranks = [c["rank"] for c in out["data"]["causes"]]
    assert ranks == sorted(ranks) and len(ranks) >= 3
    assert out["ui_block"]["type"] == "diagnosis"


def test_install_guide() -> None:
    out = tools.run_tool("get_installation_guide", {"part_identifier": "PS11752778"})
    assert out["data"]["difficulty"]
    assert out["ui_block"]["type"] == "install_guide"


def test_order_support_deterministic_mock() -> None:
    a = tools.run_tool("order_support", {"action": "order_status", "order_id": "123456"})
    b = tools.run_tool("order_support", {"action": "order_status", "order_id": "123456"})
    assert a["data"] == b["data"]
    ask = tools.run_tool("order_support", {"action": "order_status"})
    assert ask["data"]["needs"] == "order_id"


def test_malformed_input_raises_validation_error() -> None:
    with pytest.raises(pydantic.ValidationError):
        tools.run_tool("diagnose_issue", {"symptom_description": "x", "appliance_type": "spaceship"})
