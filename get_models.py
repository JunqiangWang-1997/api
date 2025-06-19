import os
import dashscope
import json

def get_all_dashscope_models():
    # 临时将 API 密钥直接写入脚本，请用户替换为自己的实际密钥
    api_key = "REDACTED" 
    if api_key == "YOUR_DASHSCOPE_API_KEY":
        print("警告: 请将 get_models.py 文件中的 'YOUR_DASHSCOPE_API_KEY' 替换为您的实际 DashScope API 密钥。")
        return []

    dashscope.api_key = api_key
    
    all_models = []
    page = 1
    page_size = 100 # 尝试获取更多模型

    try:
        # 直接使用 page 和 page_size 参数进行一次调用
        response = dashscope.models.Models.list(page=page, page_size=page_size)
        
        # 直接打印 response 对象，无论它是什么类型
        print(f"DEBUG: DashScope Models.list() 响应: {response}")

        # 只有当 response 是 DashScopeAPIResponse 类型且 status_code 为 200 时才尝试处理
        if hasattr(response, 'status_code') and response.status_code == 200:
            # 检查 output 中是否有 total 字段
            total_models = response.output.get('total', 0)
            print(f"DEBUG: API 报告的总模型数量: {total_models}")

            models_data = response.output['models']
            for model in models_data:
                if isinstance(model, dict) and 'name' in model:
                    all_models.append({"name": model['name'], "description": model.get('description', ''), "capabilities": [], "cost_category": "unknown", "free_tier_eligible": False})
                else:
                    print(f"警告: 远程模型数据格式异常，跳过: {model}")
            
            # 如果 total > page_size，则需要分页获取
            # 但根据之前的日志，total 总是 5，所以这里暂时不实现循环分页
            # 如果后续发现 total 变大，再考虑实现分页循环
            
            print(f"成功获取到 {len(all_models)} 个远程模型。")
            return all_models
        else:
            print(f"获取远程模型失败: {response.message}")
            return []
    except Exception as e:
        print(f"获取远程模型时发生异常: {str(e)}")
        return []

if __name__ == "__main__":
    models = get_all_dashscope_models()
    if models:
        print("\n--- 获取到的模型列表 ---")
        for model in models:
            print(f"- 名称: {model['name']}, 描述: {model['description']}")
