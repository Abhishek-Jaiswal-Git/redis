import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from redis_client import RedisClient


class Leaderboard:
    def __init__(
        self,
        redis: RedisClient,
        key: str = "leaderboard:game:global",
        channel: str = "leaderboard:updates",
    ):
        self.redis = redis
        self.key = key
        self.channel = channel

    def reset(self) -> None:
        self.redis.command("DEL", self.key)

    def update_score(self, player_id: str, score: int) -> None:
        self.redis.command("ZADD", self.key, score, player_id)
        self._publish_score(player_id, score)

    def increment_score(self, player_id: str, delta: int) -> int:
        new_score = int(float(self.redis.command("ZINCRBY", self.key, delta, player_id)))
        self._publish_score(player_id, new_score, delta)
        return new_score

    def top_n(self, limit: int = 10) -> List[Dict[str, object]]:
        response = self.redis.command("ZREVRANGE", self.key, 0, limit - 1, "WITHSCORES")
        rows = []
        for index in range(0, len(response), 2):
            rows.append(
                {
                    "rank": index // 2 + 1,
                    "player_id": response[index],
                    "score": int(float(response[index + 1])),
                }
            )
        return rows

    def get_player(self, player_id: str) -> Dict[str, Optional[object]]:
        rank = self.redis.command("ZREVRANK", self.key, player_id)
        score = self.redis.command("ZSCORE", self.key, player_id)
        return {
            "player_id": player_id,
            "rank": None if rank is None else int(rank) + 1,
            "score": None if score is None else int(float(score)),
        }

    def count(self) -> int:
        return int(self.redis.command("ZCARD", self.key))

    def _publish_score(self, player_id: str, score: int, delta: Optional[int] = None) -> None:
        payload = {
            "event": "score_updated",
            "player_id": player_id,
            "score": score,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        if delta is not None:
            payload["delta"] = delta
        self.redis.command("PUBLISH", self.channel, json.dumps(payload))

    def mass_increment(self, updates: List[Tuple[str, int]]) -> None:
        """Increments multiple player scores using a single pipeline."""
        commands = [["ZINCRBY", self.key, delta, p_id] for p_id, delta in updates]
        self.redis.pipeline(commands)

