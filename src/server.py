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
    读取飞书云文档（支持 docx 和 wiki 链接）。
    Args:
        url: 飞书文档的完整链接 
             e.g. https://xxx.feishu.cn/docx/doxcn...
             e.g. https://xxx.feishu.cn/wiki/wikcn...
    """
    client = get_client()
    try:
        real_token = ""
        
        # 1. 处理 Wiki 链接
        if "/wiki/" in url:
            try:
                # 提取 wiki token
                wiki_token = url.split("/wiki/")[1].split("?")[0]
                # 获取真实 docx token
                real_token = await client.get_wiki_node_info(wiki_token)
            except Exception as e:
                return f"Error resolving wiki url: {str(e)}"
                
        # 2. 处理 Docx 链接
        elif "/docx/" in url:
            try:
                real_token = url.split("/docx/")[1].split("?")[0]
            except:
                return "Error: Invalid docx url format"
        
        # 3. 兜底：假设输入的是 token
        else:
            real_token = url
            
        if not real_token:
            return "Error: Could not extract document token"

        # 读取内容
        content = await client.get_document_raw_content(real_token)
        return content
        
    except Exception as e:
        return f"Error reading doc: {str(e)}"
    finally:
        await client.close()

if __name__ == "__main__":
    mcp.run()
