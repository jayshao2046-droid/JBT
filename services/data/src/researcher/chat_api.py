"""对话 API - FastAPI 路由

职责：
1. 提供对话接口
2. 处理自然语言指令
"""
from fastapi import APIRouter
from pydantic import BaseModel
from .chat_interface import ChatInterface

router = APIRouter(prefix="/api/v1/researcher/chat", tags=["chat"])

chat_interface = ChatInterface()


class ChatRequest(BaseModel):
    message: str


@router.post("/")
async def chat(request: ChatRequest):
    """对话接口"""
    result = chat_interface.process_command(request.message)
    return result
