import os
import httpx
import asyncio
from typing import Optional, Dict, Any

class FeishuClient:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: Optional[str] = None
        self._token_expire_time: float = 0
        self.client = httpx.AsyncClient(base_url=self.BASE_URL)

    async def get_tenant_access_token(self) -> str:
        """获取企业自建应用 token"""
        # 简单处理：暂不考虑 token 过期自动刷新的复杂逻辑，每次都拿新的（飞书有频率限制，后续优化）
        resp = await self.client.post(
            "/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Auth failed: {data}")
        return data["tenant_access_token"]

    async def get_document_raw_content(self, document_id: str) -> str:
        """获取文档纯文本内容 (docx)"""
        token = await self.get_tenant_access_token()
        
        # 飞书 API: 获取文档所有块
        # https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/raw_content
        resp = await self.client.get(
            f"/docx/v1/documents/{document_id}/raw_content",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Get document failed: {data}")
            
        return data["data"]["content"]

    async def close(self):
        await self.client.aclose()

# Test script
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main():
        app_id = os.getenv("FEISHU_APP_ID")
        app_secret = os.getenv("FEISHU_APP_SECRET")
        
        if not app_id or not app_secret:
            print("Error: Missing FEISHU_APP_ID or FEISHU_APP_SECRET")
            return

        client = FeishuClient(app_id, app_secret)
        
        try:
            print("1. Testing Auth...")
            token = await client.get_tenant_access_token()
            print(f"✅ Auth success! Token: {token[:10]}...")
            
            # 这里需要一个真实的文档 token (doc_id) 来测试
            # 格式如：doxcnXXXXXXXXXXXXXXXXXXXXXX
            # print("2. Testing Read Doc...")
            # content = await client.get_document_raw_content("YOUR_DOC_ID")
            # print(f"Content preview: {content[:100]}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.close()

    asyncio.run(main())
