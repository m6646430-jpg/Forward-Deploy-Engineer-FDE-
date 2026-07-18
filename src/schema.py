"""The extraction contract.

This is the single most important file in the project. Everything downstream —
aggregation, risk scoring, the report — depends on the LLM emitting exactly this
shape. In a real FDE engagement you'd iterate on this schema WITH the customer:
"is 'sizing' the same as 'fit'? do you care about shipping complaints?" etc.

We use Pydantic so we get validation for free: if the model returns garbage, we
find out immediately instead of three stages downstream.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class IssueCategory(str, Enum):
    """The buckets the merch team cares about. Kept deliberately small — a huge
    taxonomy makes the model inconsistent. Start narrow, expand with the customer."""
    defect = "defect"              # something physically broke / failed
    sizing_fit = "sizing_fit"      # runs small/large, doesn't fit as expected
    quality = "quality"            # cheap-feeling, wore out, not as described
    usability = "usability"        # hard to use / confusing
    shipping = "shipping"          # arrived damaged / late / wrong item
    other = "other"


class ReviewInsight(BaseModel):
    """What the LLM extracts from ONE review."""
    sentiment: Sentiment
    # Short, human-readable phrases. E.g. "main zipper split after 2 weeks".
    # These are what cluster into "14 reviews mention the zipper" later.
    issues: list[str] = Field(
        default_factory=list,
        description="Specific problems mentioned, each a short phrase. Empty if none.",
    )
    issue_categories: list[IssueCategory] = Field(
        default_factory=list,
        description="Which buckets the issues fall into.",
    )
    praise: list[str] = Field(
        default_factory=list,
        description="Specific things the customer liked. Empty if none.",
    )
    # The one-line signal a merchandiser could scan in a table.
    summary: str = Field(description="One sentence capturing the review's key point.")
    # A short quoted phrase we can show as evidence in the report.
    evidence_quote: Optional[str] = Field(
        default=None,
        description="A short verbatim quote (<=15 words) supporting the main issue, if any.",
    )


# The JSON Schema we hand to the Anthropic API tool/structured-output. Generated from the model
# so it can never drift from the Pydantic definition above.
REVIEW_INSIGHT_SCHEMA = ReviewInsight.model_json_schema()
