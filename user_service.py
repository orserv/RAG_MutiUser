import redis
import hashlib
import sys


class UserService:
    def __init__(self, redis_url="redis://localhost:6379/0"):
        try:
            self.redis_client = redis.from_url(
                redis_url, decode_responses=True)
            # 测试连接
            self.redis_client.ping()
            print("✅ Redis 连接成功")
        except Exception as e:
            print(f"❌ Redis 连接失败: {e}")
            raise e

        self.user_prefix = "user_info:"

    def _hash_password(self, password: str) -> str:
        """使用 SHA256 哈希密码"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def register(self, username: str, password: str) -> dict:
        """注册用户"""
        print(f"📝 尝试注册用户: {username}")

        if not username or not password:
            return {"status": "error", "message": "用户名和密码不能为空"}

        key = f"{self.user_prefix}{username}"

        # 检查用户是否已存在
        if self.redis_client.exists(key):
            print(f"⚠️ 用户 {username} 已存在")
            return {"status": "error", "message": "用户已存在"}

        user_data = {
            "username": username,
            "password_hash": self._hash_password(password),
        }

        try:
            # 存入 Redis Hash
            self.redis_client.hset(key, mapping=user_data)
            print(f"✅ 用户 {username} 注册成功")
            return {"status": "success", "message": "注册成功"}
        except Exception as e:
            print(f"❌ 注册写入 Redis 失败: {e}")
            return {"status": "error", "message": f"服务器错误: {str(e)}"}

    def login(self, username: str, password: str) -> dict:
        """登录验证"""
        print(f"🔑 尝试登录用户: {username}")
        key = f"{self.user_prefix}{username}"

        # 获取用户数据
        user_data = self.redis_client.hgetall(key)

        if not user_data:
            print(f"⚠️ 用户 {username} 不存在")
            return {"status": "error", "message": "用户不存在"}

        input_hash = self._hash_password(password)
        stored_hash = user_data.get('password_hash')

        print(
            f"🔍 密码比对: 输入Hash={input_hash[:10]}... vs 存储Hash={stored_hash[:10]}...")

        if stored_hash == input_hash:
            print(f"✅ 用户 {username} 登录成功")
            return {"status": "success", "username": username}
        else:
            print(f"❌ 密码错误")
            return {"status": "error", "message": "密码错误"}
