# config.py
MODEL_SELECTION_PROMPT_PATH = "qwen_analysis/models/model_selector_prompt.txt"

# DASHSCOPE_API_KEY = 'sk-4304728c669f4aeb83144e394a6b67c1'  # 已移除

MODEL_SELECTION_THRESHOLD = {
    'length': 100,  # 字符数阈值
}

COMPLEX_QUESTION_KEYWORDS = [
    "分析", "比较", "解释", "为什么", "如何", "机制", "原理", 
    "政策", "影响", "评估", "趋势", "研究", "法律"
]
