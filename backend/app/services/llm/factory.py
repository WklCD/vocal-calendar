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
