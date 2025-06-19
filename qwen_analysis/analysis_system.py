# qwen_analysis/analysis_system.py
import dashscope
from .token_tracker import TokenUsageTracker
from .model_selector import ModelSelector
from dashscope import Generation
import time  # 引入时间模块

class QwenAnalysisSystem:
    def __init__(self):
        # dashscope.api_key = 'sk-4304728c669f4aeb83144e394a6b67c1'  # 移除硬编码
        self.token_tracker = TokenUsageTracker()
        self.model_selector = ModelSelector(self.token_tracker)

    def process(self, question, apikey=None):
        print("接收问题:", question[:50] + "..." if len(question) > 50 else question)
    
        # 总计时器
        total_start = time.time()
    
        # 阶段1：模型选择
        select_start = time.time()
        selected_model = self.model_selector.select_model(question, apikey=apikey)
        select_end = time.time()
        print(f"选定模型: {selected_model}")
    
        # 阶段2：调用模型处理
        model_process_start = time.time()
        final_answer = self._process_with_model(selected_model, question, apikey=apikey)
        model_process_end = time.time()

        # 阶段3：结果后处理（示例）
        post_start = time.time()
        final_answer = final_answer.strip()  # 假设做了清理操作
        post_end = time.time()

        # 总耗时
        total_end = time.time()

        # 输出耗时统计
        print("\n【详细性能分析】")
        print(f"模型选择耗时: {(select_end - select_start) * 1000:.2f} ms")
        print(f"模型调用耗时: {(model_process_end - model_process_start) * 1000:.2f} ms")
        print(f"结果后处理耗时: {(post_end - post_start) * 1000:.2f} ms")
        print(f"总耗时: {(total_end - total_start) * 1000:.2f} ms\n")

        return {
            "final_answer": final_answer,
            "token_usage": self.token_tracker.token_usage_stats,
            "selected_model": selected_model,
            "performance": {
                "model_selection": select_end - select_start,
                "api_call": model_process_end - model_process_start,
                "post_processing": post_end - post_start,
                "total": total_end - total_start
            }
        }
    
    def _process_with_model(self, model_name, question, apikey=None):
        try:
            print(f"【DEBUG】正在使用模型 {model_name} 处理问题：{question[:30]}...")

            # API 调用前准备（可包括 prompt 构建、参数验证）
            pre_start = time.time()
            # 示例：构建完整 prompt
            full_prompt = f"用户提问：\n{question}\n请给出专业回答："
            pre_end = time.time()

            # API 调用
            call_start = time.time()
            response = Generation.call(model=model_name, prompt=full_prompt, api_key=apikey)
            call_end = time.time()

            # Token 解析
            token_parse_start = time.time()
            if hasattr(response, 'usage') and response.usage is not None:
                usage = response.usage
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens
            else:
                input_tokens = 0
                output_tokens = 0
            token_parse_end = time.time()

            # Token 写入统计
            token_record_start = time.time()
            self.token_tracker.record_token_usage(model_name, input_tokens, output_tokens)
            token_record_end = time.time()

            # 结果提取
            result_extract_start = time.time()
            answer = response.output.text.strip() if response.output else "[空响应]"
            result_extract_end = time.time()

            print(f"调用前准备耗时: {(pre_end - pre_start) * 1000:.2f} ms")
            print(f"API 调用耗时（纯网络）: {(call_end - call_start) * 1000:.2f} ms")
            print(f"Token 解析耗时: {(token_parse_end - token_parse_start) * 1000:.2f} ms")
            print(f"Token 写入耗时: {(token_record_end - token_record_start) * 1000:.2f} ms")
            print(f"结果提取耗时: {(result_extract_end - result_extract_start) * 1000:.2f} ms")

        except Exception as e:
            answer = f"[错误] 模型调用失败: {str(e)}"
        return answer
