"""
Supabase 客户端工具
"""

import os
from supabase import create_client, Client
from typing import Optional


class SupabaseClient:
    """Supabase 客户端单例类"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """
        获取 Supabase 客户端实例（单例模式）

        Returns:
            Supabase 客户端实例
        """
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or url == "your_supabase_url":
                raise ValueError("SUPABASE_URL 未配置或配置错误")

            if not key or key == "your_service_role_key":
                raise ValueError("SUPABASE_KEY 未配置或配置错误")

            cls._instance = create_client(url, key)
            print(f"✅ Supabase 客户端已初始化: {url}")

        return cls._instance


# 导出便捷函数
def get_supabase() -> Client:
    """
    获取 Supabase 客户端

    Returns:
        Supabase 客户端实例
    """
    return SupabaseClient.get_client()
