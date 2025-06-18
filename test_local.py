# test_local.py

import time
from qwen_analysis.analysis_system import QwenAnalysisSystem

def run_test():
    # 初始化系统
    system = QwenAnalysisSystem()

    # 测试问题
    questions = [

        "1+1等于几？"

    ]

    for idx, question in enumerate(questions):
        print(f"\n===== 测试用例 {idx + 1} =====")
        print(f"输入问题: {question}")
        
        # 调用处理流程
        result = system.process(question)

        # 输出结果
        print("\n【最终回答】")
        print(result["final_answer"])
        print("\nToken 使用情况:")
        print(result["token_usage"])
        print("选定模型:", result["selected_model"])
        print("总耗时: %.2f ms" % (result["performance"]["total"] * 1000))

if __name__ == "__main__":
    run_test()