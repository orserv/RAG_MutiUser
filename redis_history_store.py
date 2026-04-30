# import os
# from langchain_redis import RedisChatMessageHistory
# import redis


# def get_redis_history(session_id: str, ttl: int = 3600 * 24 * 7):  # 默认保存7天
#     """
#     根据 session_id 获取 Redis 聊天历史记录对象
#     """
#     # 从环境变量获取 Redis 配置，如果没有则使用默认值
#     redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

#     # key_prefix 用于区分不同业务的 key，避免冲突
#     # 最终在 Redis 中的 key 格式通常为: {key_prefix}:{session_id}
#     history = RedisChatMessageHistory(
#         session_id=session_id,
#         redis_url=redis_url,
#         key_prefix="chat_history:"
#     )

#     # 尝试设置过期时间 (注意：每次添加消息后可能需要重新设置，或者依靠 Redis 策略)
#     # LangChain 的 RedisChatMessageHistory 内部使用 List 或 Hash。
#     # 如果需要严格 TTL，建议在每次 add_message 后调用 expire，
#     # 但 RunnableWithMessageHistory 自动调用 add_messages，我们很难介入。
#     # 一种常见做法是依赖 Redis 的 maxmemory-policy 或在外部定期清理。

#     return history
import json
import redis
from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


class ManualRedisChatHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, redis_url: str = "redis://localhost:6379/0", ttl: int = 604800):
        """
        :param session_id: 这里传入 username
        :param ttl: 过期时间，默认 7 天 (60 * 60 * 24 * 7 = 604800 秒)
        """
        self.session_id = session_id
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key = f"chat_history:{session_id}"
        self.ttl = ttl

    @property
    def messages(self) -> List[BaseMessage]:
        """从 Redis 获取消息列表"""
        items = self.redis_client.lrange(self.key, 0, -1)
        if not items:
            return []
        # 将 JSON 字符串转回 BaseMessage 对象
        dicts = [json.loads(item) for item in items]
        return messages_from_dict(dicts)

    # def add_messages(self, messages: List[BaseMessage]) -> None:
    #     """将消息追加到 Redis 列表"""
    #     for message in messages:
    #         # 将 BaseMessage 转为字典，再转为 JSON 字符串
    #         msg_dict = message_to_dict(message)
    #         self.redis_client.rpush(self.key, json.dumps(msg_dict))

    #     # 可选：设置过期时间，例如 24 小时
    #     self.redis_client.expire(self.key, 86400)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """将消息追加到 Redis 列表，并设置/刷新过期时间"""
        pipe = self.redis_client.pipeline()
        for message in messages:
            msg_dict = message_to_dict(message)
            pipe.rpush(self.key, json.dumps(msg_dict))

        # 关键：设置过期时间为 7 天
        # EXPIRE 命令会在每次写入时重置计时器，实现“活跃用户保留7天， inactive 用户7天后清理”
        pipe.expire(self.key, self.ttl)
        pipe.execute()

    def clear(self) -> None:
        """清空历史"""
        self.redis_client.delete(self.key)


def get_redis_history(session_id: str):
    # 这里 session_id 实际上是 username
    return ManualRedisChatHistory(session_id)
