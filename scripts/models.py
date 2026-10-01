from pydantic import BaseModel, Field

class Exercise(BaseModel):
    number: int = Field(description="Exercise number as printed in the book")
    page: int = Field(
        description="Page number where the exercise begins. "
        "Always read the literal page number printed on the page, never count sequentially"
    )
    sub_topic: str | None = Field(
        None, description="Specific grammar rule this exercise practices, if narrower than the chapter's overall topic"
    )
    task_type: str = Field(
        description="Kind of task, e.g. translation, fill-in-the-blank, open the brackets, matching"
    )
    text: str = Field(
        description="Full text of the exercise, transcribed verbatim exactly as printed on the page. "
        "Never paraphrase, summarize, or describe the content in place of the actual text — if part of it "
        "is unreadable, transcribe what you can and set needs_review=True instead of substituting a description."
    )

    rule: str | None = Field(
        None, description="Grammar rule or reference table immediately preceding this exercise, if present"
    )
    summary: str = Field(
        description="Specific, distinguishing description of what this exercise practices — not just the topic, "
        "but what makes it different from other exercises on the same topic"
    )
    needs_review: bool = Field(
        description="True only if there is a specific word or phrase you are not confident you read correctly. "
        "Do not set this to True simply because the exercise is long or repetitive."
    )
    review_reason: str | None = Field(None, description="If needs_review is True, briefly explain what specifically was uncertain")


class ChapterIndex(BaseModel):
    source_file: str
    topic: str = Field(description="Overall chapter topic, inferred from the page contents")
    exercises: list[Exercise]