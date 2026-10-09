from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass

class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True) 
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    
    exercises: Mapped[list["Exercise"]] = relationship("Exercise", back_populates="chapter")

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    number: Mapped[int] = mapped_column(nullable=False)
    page: Mapped[int] = mapped_column(nullable=False)
    sub_topic: Mapped[str] = mapped_column(Text, nullable=True)
    embedded_sub_topic: Mapped[list[float]] = mapped_column(Vector(768), nullable=True)
    task_type: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rule: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedded_summary: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    needs_review: Mapped[bool] = mapped_column(nullable=False)
    review_reason: Mapped[str] = mapped_column(Text, nullable=True)
    
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="exercises")
