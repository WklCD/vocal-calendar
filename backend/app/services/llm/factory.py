from app.services.llm.base import BaseLLM
from app.services.llm.qwen import QwenLLM
from app.services.llm.openai import OpenAILLM
from app.services.llm.glm import GLMLLM
from app.services.llm.mock import MockLLM
from app.core.config import get_settings


def create_llm(provider: str | None = None) -> BaseLLM:
    """根据配置创建 LLM 实例。

    Args:
        provider: "qwen" | "openai" | "glm" | "mock"，默认从配置读取
                  如果配置的 provider 没有 API Key，自动降级为 mock

    Returns:
        BaseLLM 实例
    """
    settings = get_settings()
    provider = provider or getattr(settings, "LLM_PROVIDER", "mock")

    providers = {
        "qwen": lambda: QwenLLM(),
        "openai": lambda: OpenAILLM(),
        "glm": lambda: GLMLLM(),
        "mock": lambda: MockLLM(),
    }

    factory = providers.get(provider)
    if not factory:
        raise ValueError(f"不支持的 LLM 提供商: {provider}. 可选: {list(providers.keys())}")

    # 如果选择的 provider 没有配置 API Key，自动降级为 mock
    if provider != "mock":
        api_key = getattr(settings, f"{provider.upper()}_API_KEY", "")
        if not api_key:
            print(f"[LLM] {provider} 未配置 API_KEY，自动使用 Mock 模式")
            return MockLLM()

    return factory()
