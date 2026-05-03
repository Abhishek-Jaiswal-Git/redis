import json
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
        self.redis.delete(self.key)

    def update_score(self, player_id: str, score: int) -> None:
        self.redis.zadd(self.key, {player_id: score})
        self._publish_score(player_id, score)

    def increment_score(self, player_id: str, delta: int) -> int:
        new_score = int(self.redis.zincrby(self.key, delta, player_id))
        self._publish_score(player_id, new_score, delta)
        return new_score

    def top_n(self, limit: int = 10) -> List[Dict[str, object]]:
        response = self.redis.zrevrange(self.key, 0, limit - 1, withscores=True)
        rows = []
        for index, (player_id, score) in enumerate(response):
            rows.append(
                {
                    "rank": index + 1,
                    "player_id": player_id,
                    "score": int(score),
                }
            )
        return rows

    def get_player(self, player_id: str) -> Dict[str, Optional[object]]:
        rank = self.redis.zrevrank(self.key, player_id)
        score = self.redis.zscore(self.key, player_id)
        return {
            "player_id": player_id,
            "rank": None if rank is None else int(rank) + 1,
            "score": None if score is None else int(float(score)),
        }

    def count(self) -> int:
        return self.redis.zcard(self.key)

    def _publish_score(self, player_id: str, score: int, delta: Optional[int] = None) -> None:
        payload = {
            "event": "score_updated",
            "player_id": player_id,
            "score": score,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        if delta is not None:
            payload["delta"] = delta
        self.redis.publish(self.channel, json.dumps(payload))

    def mass_increment(self, updates: List[Tuple[str, int]]) -> None:
        """Increments multiple player scores using a single pipeline."""
        self.redis.pipeline_zincrby(self.key, updates)
