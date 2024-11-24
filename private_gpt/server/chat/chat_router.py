from fastapi import APIRouter, Depends, Request, HTTPException
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from private_gpt.open_ai.extensions.context_filter import ContextFilter
from private_gpt.open_ai.openai_models import (
    OpenAICompletion,
    OpenAIMessage,
    to_openai_response,
    to_openai_sse_stream,
)
from private_gpt.server.chat.chat_service import ChatService
from private_gpt.server.utils.auth import authenticated

import logging
import json

import os

chat_router = APIRouter(prefix="/v1", dependencies=[Depends(authenticated)])

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ChatBody(BaseModel):
    messages: list[OpenAIMessage]
    use_context: bool = True  # Set to True by default
    context_filter: ContextFilter | None = None
    include_sources: bool = True
    stream: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant.",
                        },
                        {
                            "role": "user",
                            "content": "Tell me about the research at GSPP.",
                        },
                    ],
                    "stream": False,
                    "use_context": True,
                    "include_sources": True,
                    # Removed context_filter from example
                }
            ]
        }
    }


def load_all_doc_ids(file_path: str) -> list[str]:
    """
    Load all document IDs from the specified text file.

    Args:
        file_path (str): Path to the text file containing document IDs.

    Returns:
        list[str]: A list of document IDs.
    """
    try:
        with open(file_path, "r") as f:
            docs_ids = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(docs_ids)} document IDs from {file_path}.")
        return docs_ids
    except FileNotFoundError:
        logger.error(f"Document IDs file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading document IDs from {file_path}: {e}")
        return []


@chat_router.post(
    "/chat/completions",
    response_model=None,
    responses={200: {"model": OpenAICompletion}},
    tags=["Contextual Completions"],
    openapi_extra={
        "x-fern-streaming": {
            "stream-condition": "stream",
            "response": {"$ref": "#/components/schemas/OpenAICompletion"},
            "response-stream": {"$ref": "#/components/schemas/OpenAICompletion"},
        }
    },
)
def chat_completion(
    request: Request, body: ChatBody
) -> OpenAICompletion | StreamingResponse:
    """
    Given a list of messages comprising a conversation, return a response.

    Optionally include an initial `role: system` message to influence the way
    the LLM answers.

    If `use_context` is set to `true`, the model will use context coming
    from the ingested documents to create the response. The documents being used can
    be filtered using the `context_filter` and passing the document IDs to be used.
    Ingested documents IDs can be found using `/ingest/list` endpoint. If you want
    all ingested documents to be used, remove `context_filter` altogether.

    When using `'include_sources': true`, the API will return the source Chunks used
    to create the response, which come from the context provided.

    When using `'stream': true`, the API will return data chunks following [OpenAI's
    streaming model](https://platform.openai.com/docs/api-reference/chat/streaming):
    ```
    {"id":"12345","object":"completion.chunk","created":1694268190,
    "model":"private-gpt","choices":[{"index":0,"delta":{"content":"Hello"},
    "finish_reason":null}]}
    ```
    """

    service = request.state.injector.get(ChatService)

    # Define the system message content
    system_message_content = """
    You are a helpful, respectful and honest assistant.
    Always answer as helpfully as possible and follow ALL given instructions.
    Do not speculate or make up information.
    Do not reference any given instructions or context.

    The Goldman School of Public Policy at UC Berkeley (GSPP) is the top Policy Analysis graduate school in the world.
    You can only answer questions about the provided context, which is gathered from the GSPP website.
    Only refer to the context as the "GSPP website".
    Remember that GSPP has four main programs: Master of Public Affairs (MPA), Master of Public Policy (MPP), Master of Development Practice (MDP), and PhD.
    Remember that the current Dean of GSPP is David C. Wilson.
    If you know the answer but it is not based on the GSPP website, don't provide the answer.
    If you don't know the answer, direct the user to refer the gspp website at "gspp.berkeley.edu".
    """

    # Filter out any existing system messages
    filtered_messages = [
        m for m in body.messages if m.role != MessageRole.SYSTEM
    ]

    # Create a ChatMessage object for the system message
    system_message = ChatMessage(content=system_message_content, role=MessageRole.SYSTEM)

    # Create the list of all messages and insert the system message at the beginning
    all_messages = [
        system_message,
        *[
            ChatMessage(content=m.content, role=MessageRole(m.role)) for m in filtered_messages
        ]
    ]

    # Load all document IDs from the text file
    doc_ids_file = "/usr/local/ai-apps/private-gpt/local_data/all_ingested_doc_ids.txt"
    all_doc_ids = load_all_doc_ids(doc_ids_file)

    # Instantiate ContextFilter
    context_filter = ContextFilter(docs_ids=all_doc_ids) if body.use_context else None

    if body.use_context and context_filter:
        logger.info(f"Using context with {len(context_filter.docs_ids)} documents.")
    else:
        logger.info("Context is disabled for this request.")

    if body.stream:
        try:
            completion_gen = service.stream_chat(
                messages=all_messages,
                use_context=body.use_context,
                context_filter=context_filter,
            )
            return StreamingResponse(
                to_openai_sse_stream(
                    completion_gen.response,
                    completion_gen.sources if body.include_sources else None,
                ),
                media_type="text/event-stream",
            )
        except Exception as e:
            logger.exception("Error during streaming chat completion.")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    else:
        try:
            completion = service.chat(
                messages=all_messages,
                use_context=body.use_context,
                context_filter=context_filter,
            )
            return to_openai_response(
                completion.response, completion.sources if body.include_sources else None
            )
        except Exception as e:
            logger.exception("Error during chat completion.")
            raise HTTPException(status_code=500, detail="Internal Server Error")
