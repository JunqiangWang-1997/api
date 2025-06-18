import time
import random
from dashscope import Generation
from .config import MODEL_SELECTION_PROMPT_PATH

class ModelSelector:
    def __init__(self, token_tracker):
        self.token_tracker = token_tracker
        self.prompt_template = self._load_prompt_template(MODEL_SELECTION_PROMPT_PATH)

        # 可用于“模型选择任务”的 Turbo 模型列表（排除 latest）
        self.turbo_eval_models = [
            "qwen-turbo",
            "qwen-turbo-2025-02-11",
            "qwen-turbo-0919",
            "qwen-turbo-1101",
            "qwen-turbo-0624"
        ]

    def _load_prompt_template(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def select_model(self, question, apikey=None):
        # 随机选择一个 Turbo 模型进行模型选择（评估）
        eval_model = random.choice(self.turbo_eval_models)
        prompt = self.prompt_template.replace("{question}", question)

        start_time = time.time()
        selected_model = "qwen-turbo-latest"  # 默认 fallback

        try:
            response = Generation.call(
                model=eval_model,
                prompt=prompt,
                api_key=apikey
            )
            selected_model = response.output.text.strip()
        except Exception as e:
            print(f"[错误] 模型选择失败（使用模型 {eval_model}）: {str(e)}")
            selected_model = "qwen-turbo-latest"

        end_time = time.time()

        # 记录 token 使用情况（记录到实际使用的评估模型）
        if hasattr(response, 'usage'):
            usage = response.usage
            self.token_tracker.record_token_usage(eval_model, usage.input_tokens, usage.output_tokens)

        print(f"选定模型: {selected_model}")
        print(f"模型选择耗时: {(end_time - start_time) * 1000:.2f} ms")

        return selected_model