from typing import Iterable, List, Optional, Tuple

import redis


class RedisClient:
    """Small wrapper around redis-py used by the leaderboard demo."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        timeout: float = 5.0,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[int] = None,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.username = username
        self.password = password
        self.database = database or 0
        self._client = redis.Redis(
            host=host,
            port=port,
            db=self.database,
            username=username,
            password=password,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            decode_responses=True,
        )

    def connect(self) -> None:
        self._client.ping()

    def close(self) -> None:
        self._client.close()

    def delete(self, key: str) -> int:
        return int(self._client.delete(key))

    def zadd(self, key: str, mapping: dict[str, int]) -> int:
        return int(self._client.zadd(key, mapping))

    def zincrby(self, key: str, delta: int, member: str) -> float:
        return float(self._client.zincrby(key, delta, member))

    def zrevrange(self, key: str, start: int, end: int, withscores: bool = False):
        return self._client.zrevrange(key, start, end, withscores=withscores)

    def zrevrank(self, key: str, member: str) -> Optional[int]:
        rank = self._client.zrevrank(key, member)
        return None if rank is None else int(rank)

    def zscore(self, key: str, member: str) -> Optional[float]:
        score = self._client.zscore(key, member)
        return None if score is None else float(score)

    def zcard(self, key: str) -> int:
        return int(self._client.zcard(key))

    def publish(self, channel: str, payload: str) -> int:
        return int(self._client.publish(channel, payload))

    def pipeline_zincrby(self, key: str, updates: Iterable[Tuple[str, int]]) -> List[float]:
        pipe = self._client.pipeline(transaction=False)
        for player_id, delta in updates:
            pipe.zincrby(key, delta, player_id)
        return [float(value) for value in pipe.execute()]
