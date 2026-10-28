"""Strict boundaries between untrusted LLM output and our renderers."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Language = Literal['en', 'hi', 'ta']
Level = Literal['beginner', 'intermediate']
SceneType = Literal['title_card', 'diagram', 'code_walkthrough']


class LessonRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    topic: str = Field(min_length=3, max_length=280)
    level: Level = 'beginner'
    language: Language = 'en'
    target_seconds: int = Field(default=60, ge=30, le=90)

    @field_validator('topic')
    @classmethod
    def normalize_topic(cls, text: str) -> str:
        text = ' '.join(text.split())
        if len(text) < 3:
            raise ValueError('Please enter a topic of at least three characters.')
        return text


class RevoiceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    language: Language


class ScenePlan(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: SceneType
    heading: str = Field(min_length=1, max_length=140)
    narration: str = Field(min_length=1, max_length=650)
    items: list[str] = Field(default_factory=list, max_length=5)
    code: str = Field(default='', max_length=700)
    highlight_lines: list[int] = Field(default_factory=list, max_length=12)

    @field_validator('heading', 'narration', 'code')
    @classmethod
    def strip_text(cls, text: str) -> str:
        return text.replace('\x00', '').strip()

    @field_validator('items')
    @classmethod
    def validate_items(cls, items: list[str]) -> list[str]:
        result = [str(item).replace('\x00', '').strip() for item in items]
        if any(not item or len(item) > 80 for item in result):
            raise ValueError('Diagram labels must be 1–80 characters each.')
        return result

    @field_validator('highlight_lines')
    @classmethod
    def valid_line_numbers(cls, values: list[int]) -> list[int]:
        if any(value < 1 or value > 40 for value in values):
            raise ValueError('Highlight lines must be between 1 and 40.')
        return values

    @model_validator(mode='after')
    def check_scene_content(self):
        if not self.heading or not self.narration:
            raise ValueError('Every scene needs a heading and narration.')
        if self.type == 'diagram' and len(self.items) < 2:
            raise ValueError('Diagram scenes need at least two labels.')
        if self.type == 'code_walkthrough' and not self.code:
            raise ValueError('Code walkthrough scenes need code.')
        if self.code:
            lines = self.code.splitlines()
            max_lines, max_width = (3, 31) if self.type == 'title_card' else (5, 38)
            if len(lines) > max_lines or any(len(line) > max_width for line in lines):
                raise ValueError('Code must fit the built-in visual component.')
            if any(line > len(lines) for line in self.highlight_lines):
                raise ValueError('A highlighted line is outside the code example.')
        return self


class LessonPlan(BaseModel):
    model_config = ConfigDict(extra='ignore')
    title: str = Field(min_length=1, max_length=160)
    scenes: list[ScenePlan] = Field(min_length=3, max_length=6)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, title: str) -> str:
        title = title.replace('\x00', '').strip()
        if not title:
            raise ValueError('The lesson needs a title.')
        return title


class TranslatedScene(BaseModel):
    model_config = ConfigDict(extra='ignore')
    heading: str = Field(min_length=1, max_length=140)
    narration: str = Field(min_length=1, max_length=650)
    items: list[str] = Field(default_factory=list, max_length=5)


class TranslationPlan(BaseModel):
    model_config = ConfigDict(extra='ignore')
    title: str = Field(min_length=1, max_length=160)
    scenes: list[TranslatedScene] = Field(min_length=3, max_length=6)


class Caption(BaseModel):
    text: str
    start: float
    end: float


class SceneOutput(ScenePlan):
    audio_url: str
    captions: list[Caption] = Field(default_factory=list)
    audio_duration: float = Field(gt=0)
    pause_seconds: float = Field(default=0.6, ge=0, le=2)


class LessonOutput(BaseModel):
    id: str
    title: str
    level: Level
    language: Language
    source: Literal['sample', 'ollama']
    original_id: str | None = None
    scenes: list[SceneOutput]
    notice: str | None = None
    timings: dict[str, float] = Field(default_factory=dict)
