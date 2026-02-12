from mcp.server.fastmcp import FastMCP
from .feishu_client import FeishuClient
import os

# 初始化 MCP Server
mcp = FastMCP("feishu")

# 从环境变量获取配置
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

def get_client():
    if not APP_ID or not APP_SECRET:
        raise ValueError("Missing FEISHU_APP_ID or FEISHU_APP_SECRET env vars")
    return FeishuClient(APP_ID, APP_SECRET)

@mcp.resource("feishu://doc/{doc_id}")
async def get_doc_content(doc_id: str) -> str:
    """读取飞书云文档内容 (Raw Content)"""
    client = get_client()
    try:
        content = await client.get_document_raw_content(doc_id)
        return content
    finally:
        await client.close()

@mcp.tool()
async def read_feishu_doc(url: str) -> str:
    """
    读取飞书云文档。
    Args:
        url: 飞书文档的完整链接 (e.g. https://xxx.feishu.cn/docx/doxcn...)
    """
    try:
        # 简单提取 token: 从 url 中截取
        if "/docx/" in url:
            doc_id = url.split("/docx/")[1].split("?")[0].split("/")[0]
        elif "feishu.cn/docs/" in url: # 兼容旧版 doc
             return "Error: 暂不支持旧版 doc，请升级为 docx"
        else:
            # 尝试直接把 url 当作 token 使用（兜底）
            doc_id = url
            
        client = get_client()
        try:
            content = await client.get_document_raw_content(doc_id)
            return content
        finally:
            await client.close()
    except Exception as e:
        return f"Error reading doc: {str(e)}"

if __name__ == "__main__":
    mcp.run()
