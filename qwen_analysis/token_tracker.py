class TokenUsageTracker:
    def __init__(self):
        self.usage = {}
        # 兼容 analysis_system.py 中使用的 token_usage_stats 属性
        self.token_usage_stats = {}  # 初始化为空字典

    def record_token_usage(self, model_name, input_tokens, output_tokens):
        # 更新 usage 字典
        if model_name not in self.usage:
            self.usage[model_name] = {"input": 0, "output": 0}
        self.usage[model_name]["input"] += input_tokens
        self.usage[model_name]["output"] += output_tokens

        # 同步更新 token_usage_stats（如果你在外部读取它）
        if model_name not in self.token_usage_stats:
            self.token_usage_stats[model_name] = {"input": 0, "output": 0}
        self.token_usage_stats[model_name]["input"] += input_tokens
        self.token_usage_stats[model_name]["output"] += output_tokens