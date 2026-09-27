# مدل‌های ورودی و خروجی پردازش زبانی.

from schemas.input import ExtractNlpInput
from schemas.output import (
    ExtractFactsOutput,
    ExtractFrameOutput,
    ExtractQuotesOutput,
    FactHit,
    IssueFrameHit,
    QuoteHit,
)

__all__ = [
    "ExtractFactsOutput",
    "ExtractFrameOutput",
    "ExtractNlpInput",
    "ExtractQuotesOutput",
    "FactHit",
    "IssueFrameHit",
    "QuoteHit",
]
