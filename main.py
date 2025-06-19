from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, AsyncGenerator
import json
import time
import traceback
import asyncio
import logging
import uvicorn # 导入 uvicorn

# 引入自定义分析系统模块
from qwen_analysis.analysis_system import QwenAnalysisSystem

app = FastAPI()
system = QwenAnalysisSystem()

logging.basicConfig(
    level=logging.DEBUG,  # 确保日志级别设置为 DEBUG
    format="【%(levelname)s】%(message)s",
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 简单分词函数，后续可替换为真实分词器
# 真实环境下建议用模型官方分词器
# 例如：from transformers import AutoTokenizer
def tokenize(text: str) -> list:
    import re
    return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)

async def generate_stream(result: Dict) -> AsyncGenerator[str, None]:
    content = result["final_answer"]
    tokens = tokenize(content)
    token_count = 0
    for token in tokens:
        token_count += 1
        data_chunk = {
            'id': f'chatcmpl-{int(time.time())}',
            'object': 'chat.completion.chunk',
            'created': int(time.time()),
            'model': result['selected_model'],
            'choices': [{
                'index': 0,
                'delta': {
                    'role': 'assistant',
                    'content': token
                },
                'finish_reason': None
            }]
        }
        logging.debug(f"Sending token: {token}")
        yield f"data: {json.dumps(data_chunk)}\n\n"
        await asyncio.sleep(0.01)  # 可根据需要调整流速

    # usage 信息，结合 analysis_system.py 的 token_usage 统计
    token_usage = result.get("token_usage", {})
    prompt_tokens = sum(v['input'] for v in token_usage.values())
    # completion_tokens 用本次流式 token_count 替代
    total_tokens = prompt_tokens + token_count
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": token_count,
        "total_tokens": total_tokens
    }
    data_end = {
        'id': f'chatcmpl-{int(time.time())}',
        'object': 'chat.completion.chunk',
        'created': int(time.time()),
        'model': result['selected_model'],
        'choices': [{
            'index': 0,
            'delta': {},
            'finish_reason': 'stop'
        }],
        'usage': usage
    }
    logging.debug(f"Sending end chunk with usage: {usage}")
    yield f"data: {json.dumps(data_end)}\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        # 获取 API key（优先 header）
        apikey = request.headers.get("x-api-key")
        if not apikey:
            raise HTTPException(status_code=401, detail="Missing API key in header")

        # 获取原始 body 并解析 JSON
        body = await request.body()
        logging.debug("接收到的原始请求体: %s", body.decode('utf-8')[:500] + "...")  # 打印部分请求内容
        data = json.loads(body.decode('utf-8'))

        messages: List[Dict[str, str]] = data.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="Missing messages")

        # 提取用户最后一条问题
        question = messages[-1]["content"]
        logging.info("提取到用户问题: %s...", question[:100])  # 修改为 logging

        # 调用系统处理，传递 apikey
        result = system.process(question, apikey=apikey)

        # 输出结果示例（可用于日志或监控）
        logging.debug("返回结果预览: %s...", result["final_answer"][:100])  # 修改为 logging

        stream = data.get("stream", True)  # 默认开启流式响应

        if not stream:
            # 非流式响应
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": result["selected_model"],
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["final_answer"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": sum(v['input'] for v in result["token_usage"].values()),
                    "completion_tokens": sum(v['output'] for v in result["token_usage"].values()),
                    "total_tokens": sum(v['input'] + v['output'] for v in result["token_usage"].values())
                }
            }
        else:
            # 流式响应
            headers = {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'  # 禁用 Nginx 缓冲
            }
            return StreamingResponse(generate_stream(result), headers=headers)

    except json.JSONDecodeError as jde:
        logging.error("JSON 解码失败: %s", str(jde))
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except KeyError as ke:
        logging.error("缺少必要字段: %s", str(ke))
        raise HTTPException(status_code=400, detail=f"Missing required key: {str(ke)}")
    except Exception as e:
        logging.error("未知异常: %s", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def main():
    # 启动 FastAPI 应用
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
