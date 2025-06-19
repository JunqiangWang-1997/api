import sys
import os

# 将当前脚本所在的目录添加到sys.path，确保模块可以被找到
sys.path.insert(0, os.path.dirname(__file__))

def filter_blob(blob):
    # 检查blob数据中是否包含秘密字符串
    if b"REDACTED" in blob.data:
        # 如果找到秘密，打印到标准错误（git-filter-repo会捕获）
        sys.stderr.write("Secret found and redacted in blob!\n")
        # 替换秘密字符串为REDACTED
        blob.data = blob.data.replace(b"REDACTED", b"REDACTED")
    return blob
