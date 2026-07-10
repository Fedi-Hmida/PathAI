from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.critic import CriticReviewDTO


def test_critic_review_document_round_trip_with_embedded_dimension_scores() -> None:
    critic_review = demo.CRITIC_REVIEW
    document = to_document(critic_review, critic_review.critic_review_id)

    assert document["_id"] == critic_review.critic_review_id
    assert document["pass_status"] == critic_review.pass_status.value
    assert isinstance(document["dimension_scores"], dict)
    assert document["dimension_scores"]["coverage"] == critic_review.dimension_scores.coverage

    restored = from_document(document, CriticReviewDTO)
    assert restored == critic_review
