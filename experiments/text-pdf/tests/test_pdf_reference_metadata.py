"""Independent physical-page expectations and manifest work budgets."""

import pytest

from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.evaluation_manifest import parse_evaluation_manifest
from soulkiller_text.pdf_fact_annotation import PdfFactAnnotation

from .corpus_helpers import encode_manifest
from .pdf_corpus_fixtures import evaluation_document, pdf_document


@pytest.mark.parametrize("count", [True, False, 1.0, "1", None, 0, -1, 21])
def test_pdf_page_count_is_a_positive_bounded_nonboolean_integer(count: object) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["page_count"] = count
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("count,page", [(1, 1), (20, 20)])
def test_pdf_page_count_and_fact_page_accept_exact_boundaries(count: int, page: int) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["page_count"] = count
    fixture["annotations"] = [{"page_number": page, "quote": "An independent fact."}]
    # Act
    result = parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert result[0].annotations == (PdfFactAnnotation(page, "An independent fact."),)


@pytest.mark.parametrize("page", [True, False, 1.0, "1", None, 0, -1, 3])
def test_pdf_fact_page_requires_nonboolean_integer_within_declared_count(page: object) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["annotations"] = [{"page_number": page, "quote": "A literal fact."}]
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("quote", ["", None, 3, "\ud800", "valid\udfff"])
def test_pdf_reference_quote_requires_nonempty_nonsurrogate_text(quote: object) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["annotations"] = [{"page_number": 1, "quote": quote}]
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "annotation",
    [
        None,
        {"page_number": 1},
        {"quote": "A fact."},
        {"page_number": 1, "quote": "A fact.", "start": 0},
        {"start": 0, "end": 3, "quote": "abc"},
    ],
)
def test_pdf_fact_fields_are_exact_and_do_not_accept_txt_offsets(annotation: object) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["annotations"] = [annotation]
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


def test_pdf_reference_annotations_preserve_given_order_and_literal_whitespace() -> None:
    # Arrange
    fixture = pdf_document()
    fixture["annotations"] = [
        {"page_number": 2, "quote": "  A second-page fact.\r\n"},
        {"page_number": 1, "quote": "Une étoile e\u0301🌟."},
    ]
    # Act
    result = parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert result[0].annotations == (
        PdfFactAnnotation(2, "  A second-page fact.\r\n"),
        PdfFactAnnotation(1, "Une étoile e\u0301🌟."),
    )


def test_pdf_fixture_accepts_exactly_thirty_two_annotations() -> None:
    # Arrange
    fixture = pdf_document()
    fixture["annotations"] = [{"page_number": 1, "quote": "Literal fact."} for _ in range(32)]
    # Act
    result = parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert len(result[0].annotations) == 32


@pytest.mark.parametrize(
    "annotations",
    [None, {}, [], [0] * 33],
    ids=[
        "null",
        "nonlist",
        "empty-valid",
        "over-count",
    ],
)
def test_pdf_annotation_shape_and_bound(annotations: object) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["annotations"] = annotations
    # Act
    if annotations == []:
        result = parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    else:
        with pytest.raises(CorpusError) as failure:
            parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    if annotations == []:
        assert result[0].annotations == ()
    else:
        assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("outcome", ["no_text", "encrypted_pdf", "malformed_input"])
def test_pdf_nonsuccess_reference_outcomes_accept_empty_annotations(outcome: str) -> None:
    # Arrange
    fixture = pdf_document()
    fixture.update({"outcome": outcome, "annotations": []})
    # Act
    result = parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert result[0].outcome == outcome
    assert result[0].annotations == ()


@pytest.mark.parametrize("outcome", ["no_text", "encrypted_pdf", "malformed_input"])
def test_pdf_nonsuccess_reference_outcomes_reject_facts(outcome: str) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["outcome"] = outcome
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "outcome",
    [
        "invalid_encoding",
        "partial",
        "unsupported_dependency",
        "candidate_failure",
        "timeout",
        "page_limit",
        None,
    ],
)
def test_pdf_reference_outcomes_exclude_infrastructure_and_txt_only_results(
    outcome: object,
) -> None:
    # Arrange
    fixture = pdf_document()
    fixture.update({"outcome": outcome, "annotations": []})
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


def test_aggregate_pdf_budget_accepts_exactly_twenty_declared_pages() -> None:
    # Arrange
    first = pdf_document()
    first["page_count"] = 12
    second = pdf_document("second", "pdfs/second.pdf")
    second["page_count"] = 8
    # Act
    result = parse_evaluation_manifest(encode_manifest(evaluation_document([first, second])))
    # Assert
    assert len(result) == 2


def test_aggregate_pdf_budget_rejects_twenty_one_declared_pages() -> None:
    # Arrange
    first = pdf_document()
    first["page_count"] = 12
    second = pdf_document("second", "pdfs/second.pdf")
    second["page_count"] = 9
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([first, second])))
    # Assert
    assert failure.value.category == "invalid_manifest"
