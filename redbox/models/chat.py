from typing import Literal, Optional
from uuid import UUID

from pydantic import Field, BaseModel, AnyUrl


class ChatMessage(BaseModel):
    text: str = Field(description="The text of the message")
    role: Literal["user", "ai", "system"] = Field(description="The role of the message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "You are helpful AI Assistant", "role": "system"},
                {"text": "Hello", "role": "user"},
                {"text": "Hi there!", "role": "ai"},
            ]
        }
    }


class ChatRequest(BaseModel):
    message_history: list[ChatMessage] = Field(description="The history of messages in the chat")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message_history": [
                        {"text": "You are a helpful AI Assistant", "role": "system"},
                        {"text": "What is AI?", "role": "user"},
                    ]
                }
            ]
        }
    }


class Metadata(BaseModel):
    parent_doc_uuid: UUID = Field(description="uuid of original file")
    languages: Optional[list[str]] = Field(
        description="languages detected in this chunk", examples=[["eng"]], default=None
    )
    url: Optional[AnyUrl] = Field(description="url of original file", default=None)
    filetype: Optional[str] = Field(description="content-type", examples=["application/pdf"], default=None)
    page_numbers: Optional[list[int]] = Field(
        description="page number of the file that this chunk came from", default=None
    )


class InputDocuments(BaseModel):
    page_content: str = Field(description="chunk text")
    metadata: Metadata


class ChatResponse(BaseModel):
    question: str = Field(
        description="original question",
        examples=["Who is the prime minister?"],
    )
    input_documents: Optional[list[InputDocuments]] = Field(
        description="documents retrieved to form this response", default=None
    )
    output_text: str = Field(
        description="response text",
        examples=["The current Prime Minister of the UK is The Rt Hon. Rishi Sunak MP."],
    )
