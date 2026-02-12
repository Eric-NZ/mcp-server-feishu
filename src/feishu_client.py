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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main():
        app_id = os.getenv("FEISHU_APP_ID")
        app_secret = os.getenv("FEISHU_APP_SECRET")
        
        if not app_id or not app_secret:
            print("Error: 请在 .env 文件中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
            return

        client = FeishuClient(app_id, app_secret)
        print("🔗 正在连接飞书 API...")
        
        try:
            # 1. 测试 Token
            token = await client.get_tenant_access_token()
            print(f"✅ 鉴权成功! Token: {token[:10]}...")
            
            # 2. 测试读取
            url = input("\n请输入飞书文档链接 (支持 Wiki/Docx): ").strip()
            if not url:
                return

            real_token = ""
            if "/wiki/" in url:
                wiki_token = url.split("/wiki/")[1].split("?")[0]
                print(f"🔍 检测到 Wiki 链接，正在解析真实文档 ID...")
                real_token = await client.get_wiki_node_info(wiki_token)
                print(f"📄 真实 Doc ID: {real_token}")
            elif "/docx/" in url:
                real_token = url.split("/docx/")[1].split("?")[0]
            else:
                real_token = url # 假设输入的是纯 ID

            print(f"📖 正在读取内容...")
            content = await client.get_document_raw_content(real_token)
            print(f"\n✅ 读取成功 ({len(content)} 字符):\n" + "-"*30 + f"\n{content[:500]}...\n" + "-"*30)
            
        except Exception as e:
            print(f"\n❌ 出错: {e}")
        finally:
            await client.close()

    asyncio.run(main())
