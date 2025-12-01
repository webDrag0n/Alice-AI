import os
import litellm
import warnings
from litellm import acompletion
from typing import List, Dict, Any, AsyncGenerator
from config.settings import settings

# Suppress Pydantic serializer warnings from litellm internals
warnings.filterwarnings("ignore", message=".*Pydantic serializer warnings.*")
# Suppress RuntimeWarning about unawaited coroutine in litellm on cancellation
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*BaseLLMHTTPHandler.async_completion.*")

# Configure litellm to drop unsupported parameters
litellm.drop_params = True

class LLMProvider:
    def __init__(self, model: str = None, api_base: str = None, api_key: str = None):
        self.model = model or settings.LLM_MODEL
        self.api_base = api_base or settings.LLM_API_BASE
        self.api_key = api_key or settings.LLM_API_KEY

    async def generate(self, messages: List[Dict[str, str]], model: str = None, api_base: str = None, api_key: str = None, **kwargs) -> str:

        # Merge default params if not provided? 
        # Actually, the caller should provide params. 
        # But for backward compatibility or ease of use, we might want defaults.
        # However, since we are moving to explicit params in settings, let's rely on caller passing them.
        
        current_model = model or self.model
        current_base = api_base or self.api_base
        current_key = api_key or self.api_key
        
        # Auto-fix model name for OpenAI Proxy (e.g. Yunwu, DeepSeek)
        # If using OpenAI provider but model name doesn't start with 'openai/', prepend it.
        # This forces litellm to use the OpenAI protocol for models like 'Doubao/...' or 'anthropic/...'
        if settings.LLM_PROVIDER == "openai" and not current_model.startswith("openai/"):
            current_model = f"openai/{current_model}"
        
        # Debug logging
        if settings.ENABLE_LLM_LOGS:
            print(f"\n========== [LLM Request] ==========")
            print(f"Model: {current_model}")
            print(f"Messages: {messages}")
            print(f"===================================\n")

        try:
            response = await acompletion(
                model=current_model,
                messages=messages,
                api_base=current_base,
                api_key=current_key,
                **kwargs
            )
            content = response.choices[0].message.content
            
            if settings.ENABLE_LLM_LOGS:
                print(f"\n========== [LLM Response] ==========")
                print(f"Model: {current_model}")
                print(f"Content: {content}")
                print(f"====================================\n")
                
            return content
        except Exception as e:
            error_msg = str(e)
            print(f"LLM Generation Error: {error_msg}")
            print(f"Params: model={current_model}, base={current_base}, key_configured={'Yes' if current_key else 'No'}")
            
            if "ServiceUnavailableError" in error_msg or "No available channels" in error_msg:
                print("提示: 您的模型代理服务似乎无法处理此模型请求。请检查 docker-compose.yml 中的 OPENAI_MODEL_MAIN 配置是否正确，或联系您的 API 提供商。")
            
            # traceback.print_exc()
            raise e

    async def generate_stream(self, messages: List[Dict[str, str]], api_base: str = None, api_key: str = None, **kwargs) -> AsyncGenerator[str, None]:
        # Check if we should add /no_think tag (default to True for backward compatibility)

        current_model = self.model
        current_base = api_base or self.api_base
        current_key = api_key or self.api_key

        # Auto-fix model name for OpenAI Proxy
        if settings.LLM_PROVIDER == "openai" and not current_model.startswith("openai/"):
            current_model = f"openai/{current_model}"

        if settings.ENABLE_LLM_LOGS:
            print(f"\n========== [LLM Stream Request] ==========")
            print(f"Model: {current_model}")
            print(f"Messages: {messages}")
            print(f"==========================================\n")

        response = await acompletion(
            model=current_model,
            messages=messages,
            stream=True,
            api_base=current_base,
            api_key=current_key,
            **kwargs
        )
        
        full_content = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if settings.ENABLE_LLM_LOGS:
                    full_content += content
                yield content
        
        if settings.ENABLE_LLM_LOGS:
            print(f"\n========== [LLM Stream Response] ==========")
            print(f"Model: {current_model}")
            print(f"Full Content: {full_content}")
            print(f"===========================================\n")
