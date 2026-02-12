import os
import httpx
import asyncio
from typing import Optional, Dict, Any

class FeishuClient:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.client = httpx.AsyncClient(base_url=self.BASE_URL)

    async def get_tenant_access_token(self) -> str:
        """获取企业自建应用 token"""
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

    async def get_wiki_node_info(self, token: str) -> str:
        """获取 Wiki 节点对应的真实文档 token (obj_token)"""
        access_token = await self.get_tenant_access_token()
        # 调用 Wiki 获取节点信息接口
        resp = await self.client.get(
            f"/wiki/v2/spaces/get_node",
            params={"token": token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        data = resp.json()
        if data.get("code") == 0:
            # 返回 obj_token (即真实的 docx token)
            return data["data"]["node"]["obj_token"]
        return token  # 如果失败，原样返回试试

    async def get_document_raw_content(self, document_id: str) -> str:
        """获取文档纯文本内容 (docx)"""
        token = await self.get_tenant_access_token()
        
        # 飞书 API: 获取文档所有块
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
