import time
import random
import json
import dashscope # 导入 dashscope
from dashscope import Generation
from .config import MODEL_SELECTION_PROMPT_PATH, COMPLEX_QUESTION_KEYWORDS, MODEL_SELECTION_THRESHOLD

class ModelSelector:
    def __init__(self, token_tracker):
        self.token_tracker = token_tracker
        self.prompt_template = self._load_prompt_template(MODEL_SELECTION_PROMPT_PATH)
        self.local_models = self._load_models("qwen_analysis/models/all_models.json")
        self.remote_models = [] # 初始化为空列表
        self.merged_models = self.local_models # 初始时只包含本地模型
        self.turbo_eval_models = [model["name"] for model in self.merged_models if "turbo" in model["name"].lower() and "latest" not in model["name"].lower()]

    def _load_prompt_template(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_models(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 未找到模型配置文件 {path}，将使用空列表。")
            return []
        except json.JSONDecodeError:
            print(f"错误: 模型配置文件 {path} 格式不正确，将使用空列表。")
            return []

    def _fetch_remote_models(self, apikey):
        try:
            if apikey:
                dashscope.api_key = apikey
            
            # 使用正确的参数名 'page' 和 'page_size'，并尝试获取所有模型
            # 根据之前的日志，API 响应中的 total 字段显示只有 5 个模型，
            # 所以即使设置 page_size 很大，也只能获取到这 5 个。
            # 因此，不再需要分页循环，直接一次性获取。
            response = dashscope.models.Models.list(page=1, page_size=100) # 使用正确的参数名
            print(f"DEBUG: DashScope Models.list() 原始响应: {response}") # 打印完整响应
            if response.status_code == 200:
                models_data = response.output['models'] # 确保是列表
                remote_models = []
                for model in models_data:
                    # 假设 model 是一个字典，包含 'name' 和 'description' 键
                    if isinstance(model, dict) and 'name' in model:
                        remote_models.append({"name": model['name'], "description": model.get('description', ''), "capabilities": [], "cost_category": "unknown", "free_tier_eligible": False})
                    else:
                        print(f"警告: 远程模型数据格式异常，跳过: {model}")
                print(f"成功获取到 {len(remote_models)} 个远程模型。")
                return remote_models
            else:
                print(f"获取远程模型失败: {response.message}")
                return []
        except Exception as e:
            print(f"获取远程模型时发生异常: {str(e)}")
            return []

    def _merge_models(self, local_models, remote_models):
        merged = {model["name"]: model for model in local_models}
        for model in remote_models:
            merged[model["name"]] = model
        return list(merged.values())

    def _is_complex_question(self, question):
        for keyword in COMPLEX_QUESTION_KEYWORDS:
            if keyword in question:
                return True
        if len(question) > MODEL_SELECTION_THRESHOLD.get('length', 100):
            return True
        return False

    def select_model(self, question, apikey=None):
        # 在每次选择模型时，尝试更新远程模型列表
        if apikey: # 只要 apikey 存在就尝试获取远程模型
            self.remote_models = self._fetch_remote_models(apikey)
            self.merged_models = self._merge_models(self.local_models, self.remote_models)
            self.turbo_eval_models = [model["name"] for model in self.merged_models if "turbo" in model["name"].lower() and "latest" not in model["name"].lower()]
            print(f"模型选择器已更新模型列表，当前可用模型数量: {len(self.merged_models)}")

        if self._is_complex_question(question):
            eval_model = random.choice(self.turbo_eval_models) if self.turbo_eval_models else "qwen-turbo-latest"
            prompt = self.prompt_template.replace("{question}", question)

            start_time = time.time()
            selected_model_from_eval = "qwen-turbo-latest" # 默认 fallback

            try:
                response = Generation.call(
                    model=eval_model,
                    prompt=prompt,
                    api_key=apikey
                )
                selected_model_from_eval = response.output.text.strip()
            except Exception as e:
                print(f"[错误] 模型选择失败（使用模型 {eval_model}）: {str(e)}")
                selected_model_from_eval = "qwen-turbo-latest"

            end_time = time.time()

            if hasattr(response, 'usage'):
                usage = response.usage
                self.token_tracker.record_token_usage(eval_model, usage.input_tokens, usage.output_tokens)

            print(f"模型选择器推荐模型: {selected_model_from_eval}")
            print(f"模型选择耗时: {(end_time - start_time) * 1000:.2f} ms")

            # 根据免费额度资格和模型能力进行最终选择
            final_selected_model = selected_model_from_eval
            # 查找推荐模型在合并列表中的详细信息
            recommended_model_info = next((m for m in self.merged_models if m["name"] == selected_model_from_eval), None)

            if recommended_model_info and recommended_model_info.get("free_tier_eligible", False):
                print(f"优先选择免费额度模型: {selected_model_from_eval}")
                final_selected_model = selected_model_from_eval
            else:
                # 如果推荐模型不是免费额度模型，尝试寻找一个合适的免费额度模型作为替代
                # 这里可以根据 capabilities 进行更复杂的匹配
                free_models = [m for m in self.merged_models if m.get("free_tier_eligible", False)]
                if free_models:
                    # 简单示例：如果推荐模型不是免费的，且有免费模型可用，则选择一个免费模型
                    # 更复杂的逻辑可以根据推荐模型的 capabilities 去匹配免费模型
                    print(f"推荐模型 {selected_model_from_eval} 非免费，尝试寻找免费替代模型。")
                    # 假设我们优先选择 qwen-turbo-latest 作为免费替代
                    if "qwen-turbo-latest" in [m["name"] for m in free_models]:
                        final_selected_model = "qwen-turbo-latest"
                        print(f"已选择免费替代模型: {final_selected_model}")
                    elif free_models: # 如果没有 qwen-turbo-latest，就随机选一个免费的
                        final_selected_model = random.choice(free_models)["name"]
                        print(f"已选择随机免费替代模型: {final_selected_model}")
                else:
                    print("没有可用的免费额度模型。")
            
            print(f"最终选定模型: {final_selected_model}")
            return final_selected_model
        else:
            print("问题被判断为简单问题，直接选择 qwen-turbo-latest")
            return "qwen-turbo-latest"
