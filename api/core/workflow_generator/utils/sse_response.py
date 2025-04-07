"""
SSE response utilities for workflow generator agents.
"""

import json
from collections.abc import Callable, Generator
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class SSEEventType(str, Enum):
    """SSE event types for workflow generator."""

    # 流式内容事件
    CONTENT = "content"
    # 工具调用事件
    TOOL_CALL = "tool_call"
    # 完成事件
    DONE = "done"
    # 错误事件
    ERROR = "error"


class SSEResponse(BaseModel):
    """Base SSE response model."""

    event: SSEEventType
    data: dict[str, Any]


def format_sse_data(data: dict[str, Any]) -> str:
    """Format data as SSE message."""
    return f"data: {json.dumps(data)}\n\n"


def generate_sse_response(
    event_type: SSEEventType,
    data: dict[str, Any]
) -> str:
    response = SSEResponse(event=event_type, data=data)
    return format_sse_data(response.model_dump())


def stream_generator(
    content_stream: Generator[Any, None, None],
    post_process_func: Optional[Callable[[str], dict[str, Any]]] = None
) -> Generator[str, None, None]:
    accumulated_content = ""

    try:
        for chunk in content_stream:
            if hasattr(chunk, 'delta') and chunk.delta and chunk.delta.message:
                if isinstance(chunk.delta.message.content, str):
                    content = chunk.delta.message.content
                    accumulated_content += content

                    yield generate_sse_response(
                        SSEEventType.CONTENT,
                        {"content": content}
                    )

                if chunk.delta.message.tool_calls:
                    for tool_call in chunk.delta.message.tool_calls:
                        yield generate_sse_response(
                            SSEEventType.TOOL_CALL,
                            {"tool_call": tool_call.model_dump()}
                        )
    except Exception as e:
        yield generate_sse_response(
            SSEEventType.ERROR,
            {"error": str(e)}
        )
        return

    # 收集完流式内容后，调用后处理函数
    if post_process_func and accumulated_content:
        try:
            result = post_process_func(accumulated_content)
            yield generate_sse_response(
                SSEEventType.DONE,
                {"result": result}
            )
        except Exception as e:
            yield generate_sse_response(
                SSEEventType.ERROR,
                {"error": str(e)}
            )
    else:
        yield generate_sse_response(
            SSEEventType.DONE,
            {"content": accumulated_content}
        )
