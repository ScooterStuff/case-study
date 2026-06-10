"""Hallucination validator edge cases."""

from __future__ import annotations

import pytest

from backend.app.tools import HallucinationError, validate_part_numbers


def test_known_ps_passes() -> None:
    validate_part_numbers("Use PS3406971 and PS11752778.", {"PS3406971", "PS11752778"})


def test_unknown_ps_raises_with_numbers() -> None:
    with pytest.raises(HallucinationError) as err:
        validate_part_numbers("Order PS12345678!", {"PS3406971"})
    assert err.value.numbers == {"PS12345678"}


def test_lowercase_ps_not_matched() -> None:
    # the agent normalizes tool data to uppercase; lowercase in prose is not a
    # PS-number claim (e.g. "ps. see above") - regex is case-sensitive on purpose
    validate_part_numbers("ps12345678 is not a part reference", set())


def test_ps_embedded_in_longer_word() -> None:
    with pytest.raises(HallucinationError):
        validate_part_numbers("CAPS123456 oh wait PS123456", set())


def test_punctuation_boundaries() -> None:
    validate_part_numbers("(PS3406971), PS3406971. PS3406971!", {"PS3406971"})


def test_empty_text() -> None:
    validate_part_numbers("", set())
