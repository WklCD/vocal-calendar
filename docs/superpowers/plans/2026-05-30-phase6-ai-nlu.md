# Phase 6: AI 自然语言理解 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 LLM 抽象层（BaseLLM + 工厂 + 三个适配器），NLU 自然语言理解服务，多轮对话上下文（Redis），语音指令执行流程，语音指令历史记录和帮助面板。

**Architecture:** 后端 LLM 层采用 Adapter 模式，BaseLLM 定义统一接口，Qwen/OpenAI/GLM 各自实现适配器。NLU Service 调用 LLM 的 parse_calendar_command 方法解析意图和实体。多轮对话上下文存储在 Redis，5 分钟过期。语音指令通过 /api/voice/command 端点提交，NLU 解析后执行对应操作。

**Tech Stack:** FastAPI, Python, Redis, 通义千问 API, OpenAI API, 智谱 GLM API, Pydantic v2

---

## File Structure

| File | Responsibility |
|------|---------------|
| `backend/app/services/llm/__init__.py` | 包初始化 |
| `backend/app/services/llm/base.py` | BaseLLM 抽象接口 |
| `backend/app/services/llm/qwen.py` | 通义千问适配器 |
| `backend/app/services/llm/openai.py` | OpenAI 适配器 |
| `backend/app/services/llm/glm.py` | 智谱 GLM 适配器 |
| `backend/app/services/llm/factory.py` | LLM 工厂 |
| `backend/app/services/nlu_service.py` | NLU 自然语言理解 |
| `backend/app/services/voice_service.py` | 语音指令处理服务 |
| `backend/app/services/voice_context.py` | 多轮对话上下文管理 |
| `backend/app/schemas/voice.py` | 语音相关 Schema |
| `backend/app/api/voice.py` | 语音 API 路由 |
| `backend/app/api/ai.py` | AI API 路由 |
| `backend/tests/test_llm_base.py` | LLM 基础测试 |
| `backend/tests/test_nlu_service.py` | NLU 服务测试 |
| `backend/tests/test_voice_api.py` | 语音 API 测试 |

---

## Task 1: 创建 LLM 抽象层

**Files:**
- Create: `backend/app/services/llm/__init__.py`
- Create: `backend/app/services/llm/base.py`
- Create: `backend/tests/test_llm_base.py`

- [ ] **Step 1: 创建 LLM 包**

创建 `backend/app/services/llm/__init__.py`：

```python
```

- [ ] **Step 2: 编写 BaseLLM 测试 (RED)**

创建 `backend/tests/test_llm_base.py`：

```python
import pytest
from abc import ABC
from app.services.llm.base import BaseLLM


class TestBaseLLM:
    def test_is_abstract(self):
        assert issubclass(BaseLLM, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseLLM()

    def test_has_parse_calendar_command(self):
        assert hasattr(BaseLLM, 'parse_calendar_command')

    def test_has_chat(self):
        assert hasattr(BaseLLM, 'chat')
```

- [ ] **Step 3: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_llm_base.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: 实现 BaseLLM**

创建 `backend/app/services/llm/base.py`：

```python
from abc import ABC, abstractmethod
from typing import Any


class BaseLLM(ABC):
    """LLM 抽象基类，所有 LLM 适配器必须实现此接口。"""

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """通用对话接口。

        Args:
            messages: 对话消息列表，格式 [{"role": "user", "content": "..."}]

        Returns:
            LLM 回复文本
        """
        pass

    @abstractmethod
    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        """自然语言 → 结构化日历指令。

        Args:
            text: 用户输入的自然语言文本
            context: 多轮对话上下文（可选）

        Returns:
            结构化指令，格式:
            {
                "intent": "create" | "delete" | "modify" | "query",
                "entities": {
                    "title": str,
                    "date": str (YYYY-MM-DD),
                    "time": str (HH:MM),
                    "duration": int (minutes),
                    "location": str,
                    "priority": int (1-5)
                },
                "confidence": float (0-1),
                "need_clarify": bool,
                "clarify_question": str | None
            }
        """
        pass
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_llm_base.py -v
```

Expected: `4 passed`

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: add BaseLLM abstract interface"
```

---

## Task 2: 实现 LLM 适配器

**Files:**
- Create: `backend/app/services/llm/qwen.py`
- Create: `backend/app/services/llm/openai.py`
- Create: `backend/app/services/llm/glm.py`
- Create: `backend/app/services/llm/factory.py`

- [ ] **Step 1: 安装依赖**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pip install httpx
echo "httpx==0.27.2" >> requirements.txt
```

- [ ] **Step 2: 实现 Qwen 适配器**

创建 `backend/app/services/llm/qwen.py`：

```python
import json
import httpx
from typing import Any
from app.services.llm.base import BaseLLM
from app.core.config import get_settings


PARSE_PROMPT = """你是一个日历助手，负责将用户的自然语言指令解析为结构化的日历操作。

请分析以下用户输入，返回 JSON 格式的解析结果：

用户输入: "{text}"

{context_section}

请返回以下 JSON 格式（不要返回其他内容）:
{{
    "intent": "create" | "delete" | "modify" | "query",
    "entities": {{
        "title": "事件标题",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration": 分钟数,
        "location": "地点",
        "priority": 1-5
    }},
    "confidence": 0.0-1.0,
    "need_clarify": true/false,
    "clarify_question": "需要追问的问题"
}}

注意:
- 如果用户没有明确指定日期，根据"今天"、"明天"、"后天"、"下周X"等推算
- 如果信息不完整，设置 need_clarify=true 并给出追问问题
- confidence 根据信息完整度和明确程度判断
"""


class QwenLLM(BaseLLM):
    """通义千问 LLM 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "qwen-turbo"):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "QWEN_API_KEY", "")
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        context_section = ""
        if context:
            context_section = f"之前的对话上下文:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        prompt = PARSE_PROMPT.format(text=text, context_section=context_section)

        messages = [{"role": "user", "content": prompt}]
        response_text = await self.chat(messages)

        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        # Fallback: return low-confidence result
        return {
            "intent": "create",
            "entities": {"title": text},
            "confidence": 0.3,
            "need_clarify": True,
            "clarify_question": "抱歉，我没有完全理解你的意思，请再说一次。",
        }
```

- [ ] **Step 3: 实现 OpenAI 适配器**

创建 `backend/app/services/llm/openai.py`：

```python
import json
import httpx
from typing import Any
from app.services.llm.base import BaseLLM
from app.core.config import get_settings


PARSE_PROMPT = """你是一个日历助手，负责将用户的自然语言指令解析为结构化的日历操作。

请分析以下用户输入，返回 JSON 格式的解析结果：

用户输入: "{text}"

{context_section}

请返回以下 JSON 格式（不要返回其他内容）:
{{
    "intent": "create" | "delete" | "modify" | "query",
    "entities": {{
        "title": "事件标题",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration": 分钟数,
        "location": "地点",
        "priority": 1-5
    }},
    "confidence": 0.0-1.0,
    "need_clarify": true/false,
    "clarify_question": "需要追问的问题"
}}
"""


class OpenAILLM(BaseLLM):
    """OpenAI LLM 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        context_section = ""
        if context:
            context_section = f"之前的对话上下文:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        prompt = PARSE_PROMPT.format(text=text, context_section=context_section)
        messages = [{"role": "user", "content": prompt}]
        response_text = await self.chat(messages)

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {
            "intent": "create",
            "entities": {"title": text},
            "confidence": 0.3,
            "need_clarify": True,
            "clarify_question": "抱歉，我没有完全理解你的意思，请再说一次。",
        }
```

- [ ] **Step 4: 实现 GLM 适配器**

创建 `backend/app/services/llm/glm.py`：

```python
import json
import httpx
from typing import Any
from app.services.llm.base import BaseLLM
from app.core.config import get_settings


PARSE_PROMPT = """你是一个日历助手，负责将用户的自然语言指令解析为结构化的日历操作。

请分析以下用户输入，返回 JSON 格式的解析结果：

用户输入: "{text}"

{context_section}

请返回以下 JSON 格式（不要返回其他内容）:
{{
    "intent": "create" | "delete" | "modify" | "query",
    "entities": {{
        "title": "事件标题",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration": 分钟数,
        "location": "地点",
        "priority": 1-5
    }},
    "confidence": 0.0-1.0,
    "need_clarify": true/false,
    "clarify_question": "需要追问的问题"
}}
"""


class GLMLLM(BaseLLM):
    """智谱 GLM 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "glm-4-flash"):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "GLM_API_KEY", "")
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def parse_calendar_command(self, text: str, context: dict[str, Any] | None = None) -> dict:
        context_section = ""
        if context:
            context_section = f"之前的对话上下文:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        prompt = PARSE_PROMPT.format(text=text, context_section=context_section)
        messages = [{"role": "user", "content": prompt}]
        response_text = await self.chat(messages)

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {
            "intent": "create",
            "entities": {"title": text},
            "confidence": 0.3,
            "need_clarify": True,
            "clarify_question": "抱歉，我没有完全理解你的意思，请再说一次。",
        }
```

- [ ] **Step 5: 实现 LLM 工厂**

创建 `backend/app/services/llm/factory.py`：

```python
from app.services.llm.base import BaseLLM
from app.services.llm.qwen import QwenLLM
from app.services.llm.openai import OpenAILLM
from app.services.llm.glm import GLMLLM
from app.core.config import get_settings


def create_llm(provider: str | None = None) -> BaseLLM:
    """根据配置创建 LLM 实例。

    Args:
        provider: "qwen" | "openai" | "glm"，默认从配置读取

    Returns:
        BaseLLM 实例
    """
    settings = get_settings()
    provider = provider or getattr(settings, "LLM_PROVIDER", "qwen")

    providers = {
        "qwen": lambda: QwenLLM(),
        "openai": lambda: OpenAILLM(),
        "glm": lambda: GLMLLM(),
    }

    factory = providers.get(provider)
    if not factory:
        raise ValueError(f"不支持的 LLM 提供商: {provider}. 可选: {list(providers.keys())}")

    return factory()
```

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: add LLM adapters (Qwen, OpenAI, GLM) with factory pattern"
```

---

## Task 3: 实现 NLU 服务和语音上下文管理

**Files:**
- Create: `backend/app/services/nlu_service.py`
- Create: `backend/app/services/voice_context.py`
- Create: `backend/tests/test_nlu_service.py`

- [ ] **Step 1: 编写 NLU 服务测试 (RED)**

创建 `backend/tests/test_nlu_service.py`：

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.nlu_service import NLUService


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.parse_calendar_command = AsyncMock(return_value={
        "intent": "create",
        "entities": {
            "title": "开会",
            "date": "2026-06-01",
            "time": "15:00",
            "duration": 60,
            "location": "会议室A",
            "priority": 3,
        },
        "confidence": 0.95,
        "need_clarify": False,
        "clarify_question": None,
    })
    return llm


@pytest.fixture
def service(mock_llm):
    return NLUService(llm=mock_llm)


class TestNLUService:
    @pytest.mark.asyncio
    async def test_parse_command_high_confidence(self, service):
        result = await service.parse_command("明天下午3点开会")
        assert result["intent"] == "create"
        assert result["confidence"] >= 0.7
        assert result["need_clarify"] is False

    @pytest.mark.asyncio
    async def test_parse_command_returns_response_text(self, service):
        result = await service.parse_command("明天下午3点开会")
        assert "response_text" in result

    @pytest.mark.asyncio
    async def test_parse_command_low_confidence_needs_clarify(self, mock_llm, service):
        mock_llm.parse_calendar_command = AsyncMock(return_value={
            "intent": "create",
            "entities": {"title": "开会"},
            "confidence": 0.4,
            "need_clarify": True,
            "clarify_question": "你想安排在什么时间？",
        })
        result = await service.parse_command("开会")
        assert result["need_clarify"] is True
        assert "clarify_question" in result
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_nlu_service.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现语音上下文管理**

创建 `backend/app/services/voice_context.py`：

```python
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from app.core.config import get_settings


class VoiceContextManager:
    """管理多轮对话上下文，存储在 Redis 中。"""

    def __init__(self, redis_client: redis.Redis | None = None):
        self.redis = redis_client
        self.ttl = 300  # 5 分钟过期

    async def _get_redis(self) -> redis.Redis:
        if not self.redis:
            settings = get_settings()
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis

    async def get_context(self, user_id: str) -> dict:
        """获取用户的对话上下文。"""
        r = await self._get_redis()
        data = await r.get(f"voice_session:{user_id}")
        if data:
            return json.loads(data)
        return {
            "last_intent": None,
            "last_entities": None,
            "turn_count": 0,
        }

    async def update_context(
        self, user_id: str, intent: str, entities: dict
    ) -> dict:
        """更新用户的对话上下文。"""
        context = await self.get_context(user_id)
        context["last_intent"] = intent
        context["last_entities"] = entities
        context["turn_count"] += 1
        context["updated_at"] = datetime.now(timezone.utc).isoformat()

        r = await self._get_redis()
        await r.setex(
            f"voice_session:{user_id}",
            self.ttl,
            json.dumps(context, ensure_ascii=False),
        )
        return context

    async def clear_context(self, user_id: str) -> None:
        """清除用户的对话上下文。"""
        r = await self._get_redis()
        await r.delete(f"voice_session:{user_id}")
```

- [ ] **Step 4: 实现 NLU 服务**

创建 `backend/app/services/nlu_service.py`：

```python
from typing import Any
from app.services.llm.base import BaseLLM
from app.services.voice_context import VoiceContextManager
from datetime import datetime, timedelta, timezone


class NLUService:
    """自然语言理解服务，将用户语音文本解析为结构化指令。"""

    def __init__(self, llm: BaseLLM, context_manager: VoiceContextManager | None = None):
        self.llm = llm
        self.context_manager = context_manager or VoiceContextManager()

    async def parse_command(
        self, text: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """解析用户语音指令。

        Args:
            text: 语音转文字后的文本
            user_id: 用户 ID（用于获取对话上下文）

        Returns:
            解析结果 + 响应文本
        """
        # 获取对话上下文
        context = None
        if user_id:
            context = await self.context_manager.get_context(user_id)

        # 调用 LLM 解析
        result = await self.llm.parse_calendar_command(text, context)

        # 后处理：补充相对日期
        result = self._resolve_relative_dates(result)

        # 生成响应文本
        response_text = self._generate_response(result)
        result["response_text"] = response_text

        # 更新上下文
        if user_id and not result.get("need_clarify"):
            await self.context_manager.update_context(
                user_id, result["intent"], result.get("entities", {})
            )

        return result

    def _resolve_relative_dates(self, result: dict) -> dict:
        """解析相对日期（明天、后天、下周X等）。"""
        entities = result.get("entities", {})
        if not entities.get("date"):
            today = datetime.now(timezone.utc).date()
            title = entities.get("title", "")

            if "明天" in title:
                entities["date"] = (today + timedelta(days=1)).isoformat()
            elif "后天" in title:
                entities["date"] = (today + timedelta(days=2)).isoformat()
            elif "今天" in title:
                entities["date"] = today.isoformat()

            result["entities"] = entities
        return result

    def _generate_response(self, result: dict) -> str:
        """根据解析结果生成自然语言响应。"""
        intent = result.get("intent", "unknown")
        entities = result.get("entities", {})
        confidence = result.get("confidence", 0)

        if result.get("need_clarify"):
            return result.get("clarify_question", "请再说一次？")

        if confidence < 0.7:
            return "抱歉，我没有完全理解你的意思，请再说一次。"

        title = entities.get("title", "事件")
        date = entities.get("date", "")
        time = entities.get("time", "")

        if intent == "create":
            time_str = f" {time}" if time else ""
            date_str = f"{date}{time_str}" if date else ""
            return f"好的，已为你创建：{title}" + (f"，时间：{date_str}" if date_str else "")
        elif intent == "delete":
            return f"好的，已删除：{title}"
        elif intent == "modify":
            return f"好的，已修改：{title}"
        elif intent == "query":
            return f"正在查询：{title}"

        return "已处理你的请求。"
```

- [ ] **Step 5: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest tests/test_nlu_service.py -v
```

Expected: `3 passed`

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "feat: add NLU service and voice context manager with tests"
```

---

## Task 4: 创建语音 Schema 和 API 路由

**Files:**
- Create: `backend/app/schemas/voice.py`
- Create: `backend/app/services/voice_service.py`
- Create: `backend/app/api/voice.py`
- Create: `backend/app/api/ai.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_voice_api.py`

- [ ] **Step 1: 创建语音 Schema**

创建 `backend/app/schemas/voice.py`：

```python
from pydantic import BaseModel
from datetime import datetime


class VoiceCommandRequest(BaseModel):
    text: str


class VoiceCommandResponse(BaseModel):
    intent: str
    entities: dict
    confidence: float
    need_clarify: bool
    clarify_question: str | None = None
    response_text: str


class VoiceLogResponse(BaseModel):
    id: str
    raw_text: str
    parsed_intent: str | None
    parsed_entities: dict | None
    response_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class VoiceHelpItem(BaseModel):
    command: str
    example: str
    description: str
```

- [ ] **Step 2: 创建 VoiceLog 模型**

创建 `backend/app/models/voice_log.py`：

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class VoiceLog(Base):
    __tablename__ = "voice_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parsed_entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 3: 更新 models/__init__.py**

修改 `backend/app/models/__init__.py`：

```python
from app.models.user import User
from app.models.event import Event
from app.models.category import Category
from app.models.voice_log import VoiceLog

__all__ = ["User", "Event", "Category", "VoiceLog"]
```

- [ ] **Step 4: 实现 VoiceService**

创建 `backend/app/services/voice_service.py`：

```python
from sqlalchemy.orm import Session
from app.models.voice_log import VoiceLog
from app.services.nlu_service import NLUService
from app.services.voice_context import VoiceContextManager
from app.models.event import Event
from datetime import datetime, timedelta, timezone


class VoiceService:
    """处理语音指令的完整流程。"""

    def __init__(self, db: Session, nlu_service: NLUService):
        self.db = db
        self.nlu_service = nlu_service

    async def process_command(self, user_id: str, text: str) -> dict:
        """处理语音指令的完整流程。

        1. NLU 解析
        2. 执行动作
        3. 记录日志
        4. 返回结果
        """
        # 1. NLU 解析
        result = await self.nlu_service.parse_command(text, user_id)

        # 2. 执行动作（如果不需要追问且置信度够高）
        if not result.get("need_clarify") and result.get("confidence", 0) >= 0.7:
            action_result = await self._execute_action(user_id, result)
            result["action_result"] = action_result

        # 3. 记录日志
        log = VoiceLog(
            user_id=user_id,
            raw_text=text,
            parsed_intent=result.get("intent"),
            parsed_entities=result.get("entities"),
            response_text=result.get("response_text"),
        )
        self.db.add(log)
        self.db.commit()

        return result

    async def _execute_action(self, user_id: str, result: dict) -> dict:
        """根据解析结果执行对应动作。"""
        intent = result.get("intent")
        entities = result.get("entities", {})

        if intent == "create":
            return await self._create_event(user_id, entities)
        elif intent == "delete":
            return await self._delete_event(user_id, entities)
        elif intent == "query":
            return await self._query_events(user_id, entities)

        return {"status": "noop"}

    async def _create_event(self, user_id: str, entities: dict) -> dict:
        """创建事件。"""
        title = entities.get("title", "新事件")
        date_str = entities.get("date")
        time_str = entities.get("time")
        duration = entities.get("duration", 60)

        if date_str and time_str:
            start = datetime.fromisoformat(f"{date_str}T{time_str}:00")
        elif date_str:
            start = datetime.fromisoformat(f"{date_str}T09:00:00")
        else:
            start = datetime.now(timezone.utc).replace(second=0, microsecond=0)

        # Apply timezone
        start = start.replace(tzinfo=timezone.utc)
        end = start + timedelta(minutes=duration)

        event = Event(
            user_id=user_id,
            title=title,
            start_time=start,
            end_time=end,
            location=entities.get("location"),
            priority=entities.get("priority", 3),
        )
        self.db.add(event)
        self.db.commit()

        return {"status": "created", "event_id": event.id}

    async def _delete_event(self, user_id: str, entities: dict) -> dict:
        """删除事件（按标题模糊匹配）。"""
        title = entities.get("title", "")
        event = (
            self.db.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.title.ilike(f"%{title}%"),
            )
            .first()
        )
        if event:
            self.db.delete(event)
            self.db.commit()
            return {"status": "deleted", "event_id": event.id}
        return {"status": "not_found"}

    async def _query_events(self, user_id: str, entities: dict) -> dict:
        """查询事件。"""
        title = entities.get("title", "")
        date_str = entities.get("date")

        query = self.db.query(Event).filter(Event.user_id == user_id)

        if title:
            query = query.filter(Event.title.ilike(f"%{title}%"))
        if date_str:
            date = datetime.fromisoformat(date_str)
            query = query.filter(
                Event.start_time >= date,
                Event.start_time < date + timedelta(days=1),
            )

        events = query.order_by(Event.start_time).all()
        return {
            "status": "found",
            "count": len(events),
            "events": [
                {"id": e.id, "title": e.title, "start": e.start_time.isoformat()}
                for e in events
            ],
        }

    def get_logs(self, user_id: str, limit: int = 50) -> list[VoiceLog]:
        """获取语音指令历史。"""
        return (
            self.db.query(VoiceLog)
            .filter(VoiceLog.user_id == user_id)
            .order_by(VoiceLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_help(self) -> list[dict]:
        """获取语音指令帮助列表。"""
        return [
            {"command": "创建事件", "example": "帮我创建明天下午3点的会议", "description": "创建新的日历事件"},
            {"command": "删除事件", "example": "删除明天的会议", "description": "删除指定事件"},
            {"command": "查询事件", "example": "我明天有什么安排", "description": "查询指定时间的事件"},
            {"command": "修改事件", "example": "把明天的会议改到后天", "description": "修改已有事件"},
        ]
```

- [ ] **Step 5: 创建语音 API 路由**

创建 `backend/app/api/voice.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.voice import VoiceCommandRequest, VoiceCommandResponse, VoiceLogResponse, VoiceHelpItem
from app.services.voice_service import VoiceService
from app.services.nlu_service import NLUService
from app.services.llm.factory import create_llm
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/voice", tags=["voice"])


def get_voice_service(db: Session = Depends(get_db)) -> VoiceService:
    llm = create_llm()
    nlu_service = NLUService(llm=llm)
    return VoiceService(db=db, nlu_service=nlu_service)


@router.post("/command")
async def process_command(
    req: VoiceCommandRequest,
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service),
):
    try:
        result = await voice_service.process_command(current_user.id, req.text)
        return {
            "code": 0,
            "data": result,
            "message": result.get("response_text", "已处理"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/logs")
def get_voice_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    llm = create_llm()
    nlu_service = NLUService(llm=llm)
    voice_service = VoiceService(db=db, nlu_service=nlu_service)
    logs = voice_service.get_logs(current_user.id)
    return {
        "code": 0,
        "data": [VoiceLogResponse.from_orm(log) for log in logs],
        "message": "ok",
    }


@router.get("/help")
def get_voice_help():
    llm = create_llm()
    nlu_service = NLUService(llm=llm)
    db = next(get_db())
    voice_service = VoiceService(db=db, nlu_service=nlu_service)
    help_items = voice_service.get_help()
    return {"code": 0, "data": help_items, "message": "ok"}
```

- [ ] **Step 6: 创建 AI API 路由**

创建 `backend/app/api/ai.py`：

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/parse")
async def parse_command(
    text: str,
    current_user: User = Depends(get_current_user),
):
    # Placeholder for direct NLU parsing
    return {"code": 0, "data": {"text": text}, "message": "请使用 /api/voice/command"}


@router.post("/detect-conflicts")
async def detect_conflicts(
    current_user: User = Depends(get_current_user),
):
    # Placeholder — implemented in phase 8
    return {"code": 0, "data": {"conflicts": []}, "message": "冲突检测功能即将上线"}


@router.post("/recommend-slot")
async def recommend_slot(
    current_user: User = Depends(get_current_user),
):
    # Placeholder — implemented in phase 8
    return {"code": 0, "data": {"slots": []}, "message": "空闲推荐功能即将上线"}


@router.get("/daily-briefing")
async def daily_briefing(
    current_user: User = Depends(get_current_user),
):
    # Placeholder — implemented in phase 8
    return {"code": 0, "data": {"briefing": ""}, "message": "每日摘要功能即将上线"}
```

- [ ] **Step 7: 注册路由到 main.py**

修改 `backend/app/main.py`，添加：

```python
from app.api.voice import router as voice_router
from app.api.ai import router as ai_router

app.include_router(voice_router)
app.include_router(ai_router)
```

- [ ] **Step 8: 更新 alembic 迁移**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
alembic revision --autogenerate -m "create voice_logs table"
alembic upgrade head
```

- [ ] **Step 9: 安装 redis 依赖**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pip install redis
echo "redis==5.1.1" >> requirements.txt
```

- [ ] **Step 10: 提交**

```bash
git add backend/
git commit -m "feat: add voice API, NLU service, and voice service with LLM integration"
```

---

## Task 5: 前端集成语音指令到后端

**Files:**
- Modify: `frontend/src/features/voice/VoicePanel.tsx`
- Create: `frontend/src/services/voiceApi.ts`

- [ ] **Step 1: 创建 voiceApi**

创建 `frontend/src/services/voiceApi.ts`：

```typescript
import api from './api';

interface VoiceCommandResponse {
  intent: string;
  entities: Record<string, any>;
  confidence: number;
  need_clarify: boolean;
  clarify_question: string | null;
  response_text: string;
}

export const voiceApi = {
  sendCommand: (text: string) =>
    api.post<{ code: number; data: VoiceCommandResponse; message: string }>(
      '/voice/command',
      { text }
    ),

  getLogs: () =>
    api.get<{ code: number; data: any[]; message: string }>('/voice/logs'),

  getHelp: () =>
    api.get<{ code: number; data: any[]; message: string }>('/voice/help'),
};
```

- [ ] **Step 2: 更新 VoicePanel 对接后端**

修改 `frontend/src/features/voice/VoicePanel.tsx`，替换模拟处理部分：

在文件顶部添加导入：

```tsx
import { voiceApi } from '../../services/voiceApi';
```

替换 `handleToggle` 函数中的模拟处理部分（`// TODO: Send to backend` 那段），替换为：

```tsx
if (finalText.trim()) {
  setProcessing(true);
  try {
    const resp = await voiceApi.sendCommand(finalText);
    const data = resp.data.data;
    setResponse(data.response_text);
    speak(data.response_text);
  } catch (err) {
    setResponse('语音指令处理失败，请重试');
  } finally {
    setProcessing(false);
  }
}
```

- [ ] **Step 3: 运行全部前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add frontend/
git commit -m "feat: integrate voice commands with backend NLU API"
```

---

## Task 6: 创建语音历史页面和帮助面板

**Files:**
- Create: `frontend/src/features/voice/VoiceHistory.tsx`
- Create: `frontend/src/features/voice/VoiceHelpPanel.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 VoiceHistory**

创建 `frontend/src/features/voice/VoiceHistory.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { voiceApi } from '../../services/voiceApi';

interface VoiceLog {
  id: string;
  raw_text: string;
  parsed_intent: string | null;
  response_text: string | null;
  created_at: string;
}

export default function VoiceHistory() {
  const [logs, setLogs] = useState<VoiceLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const resp = await voiceApi.getLogs();
        setLogs(resp.data.data);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  if (loading) {
    return <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>加载中...</div>;
  }

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: 'var(--space-6)', color: 'var(--color-primary)' }}>
        🎙️ 语音指令历史
      </h1>

      {logs.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center' }}>
          暂无语音指令记录
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {logs.map((log) => (
            <div
              key={log.id}
              style={{
                padding: 'var(--space-4)',
                background: 'var(--color-surface)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                <span style={{ fontWeight: 600 }}>{log.raw_text}</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {new Date(log.created_at).toLocaleString('zh-CN')}
                </span>
              </div>
              {log.parsed_intent && (
                <span style={{
                  display: 'inline-block',
                  padding: 'var(--space-1) var(--space-2)',
                  background: 'rgba(66, 133, 244, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-primary)',
                  marginRight: 'var(--space-2)',
                }}>
                  {log.parsed_intent}
                </span>
              )}
              {log.response_text && (
                <p style={{ marginTop: 'var(--space-2)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                  💬 {log.response_text}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 创建 VoiceHelpPanel**

创建 `frontend/src/features/voice/VoiceHelpPanel.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { voiceApi } from '../../services/voiceApi';

interface HelpItem {
  command: string;
  example: string;
  description: string;
}

export default function VoiceHelpPanel() {
  const [items, setItems] = useState<HelpItem[]>([]);

  useEffect(() => {
    const fetchHelp = async () => {
      try {
        const resp = await voiceApi.getHelp();
        setItems(resp.data.data);
      } catch {
        // Handle error
      }
    };
    fetchHelp();
  }, []);

  return (
    <div style={{
      padding: 'var(--space-4)',
      background: 'var(--color-surface)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
    }}>
      <h3 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-lg)' }}>
        💡 语音指令帮助
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {items.map((item, index) => (
          <div key={index} style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <span style={{
              padding: 'var(--space-1) var(--space-2)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}>
              {item.command}
            </span>
            <div>
              <p style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-1)' }}>
                {item.description}
              </p>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                例: "{item.example}"
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 更新路由**

修改 `frontend/src/App.tsx`，添加语音历史路由：

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import AuthGuard from './features/auth/AuthGuard';
import CalendarPage from './features/calendar/CalendarPage';
import VoiceHistory from './features/voice/VoiceHistory';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/calendar"
          element={
            <AuthGuard>
              <CalendarPage />
            </AuthGuard>
          }
        />
        <Route
          path="/voice-history"
          element={
            <AuthGuard>
              <VoiceHistory />
            </AuthGuard>
          }
        />
        <Route path="/" element={<Navigate to="/calendar" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

- [ ] **Step 4: 提交**

```bash
git add frontend/
git commit -m "feat: add voice history page and help panel"
```

---

## Task 7: 完整验证

- [ ] **Step 1: 后端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest -v --tb=short
```

Expected: 所有测试通过

- [ ] **Step 2: 前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 手动验证**

1. 登录 → 日历页面 → 点击语音按钮
2. 说出"帮我创建明天下午3点的会议"
3. 系统调用后端 NLU → 解析意图 → 创建事件 → 语音确认
4. 访问 /voice-history 查看指令记录

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 6 complete — AI NLU with LLM adapters and voice commands"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| BaseLLM 抽象接口 | ☐ |
| Qwen 适配器 | ☐ |
| OpenAI 适配器 | ☐ |
| GLM 适配器 | ☐ |
| LLM 工厂 | ☐ |
| NLU 服务 | ☐ |
| VoiceContextManager | ☐ |
| VoiceService | ☐ |
| VoiceLog 模型 | ☐ |
| 语音 API 路由 | ☐ |
| AI API 路由（占位） | ☐ |
| 前端 voiceApi | ☐ |
| VoicePanel 对接后端 | ☐ |
| VoiceHistory 页面 | ☐ |
| VoiceHelpPanel | ☐ |
