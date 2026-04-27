import os
import random
import sys
import time
from urllib.parse import urlparse

from demo_data import apply_random_updates, player_name, seed_players
from leaderboard import Leaderboard
from redis_client import RedisClient


REDIS_URL = os.getenv("REDIS_URL", "redis://34.93.131.87:6380")
PLAYERS = int(os.getenv("PLAYERS", "1000"))
TICKS = int(os.getenv("TICKS", "30"))
UPDATES_PER_TICK = int(os.getenv("UPDATES_PER_TICK", "25"))
INTERVAL_MS = int(os.getenv("INTERVAL_MS", "400"))


def main() -> int:
    url = urlparse(REDIS_URL)
    host = url.hostname or "127.0.0.1"
    port = url.port or 6379
    database = int(url.path.lstrip("/")) if url.path and url.path != "/" else None

    redis = RedisClient(
        host,
        port,
        username=url.username,
        password=url.password,
        database=database,
    )
    leaderboard = Leaderboard(redis)

    try:
        redis.connect()
        leaderboard.reset()
        seed_players(leaderboard, PLAYERS)
        print(f"Connected to Redis at {host}:{port}")
        print(f"Seeded {leaderboard.count()} players into one Redis sorted set.")
        print("Streaming score updates. Press Ctrl+C to stop.\n")
        render(leaderboard, "initial")

        for tick in range(1, TICKS + 1):
            started = time.perf_counter()
            changed_players = apply_random_updates(leaderboard, PLAYERS, UPDATES_PER_TICK)
            latency_ms = (time.perf_counter() - started) * 1000
            sample_id = random.choice(changed_players)
            sample = leaderboard.get_player(sample_id)

            time.sleep(INTERVAL_MS / 1000)
            render(
                leaderboard,
                (
                    f"tick {tick} | {UPDATES_PER_TICK} updates in {latency_ms:.2f}ms | "
                    f"sample {sample_id}: rank {sample['rank']}, score {sample['score']}"
                ),
            )
    except (ConnectionError, OSError) as error:
        print(error, file=sys.stderr)
        print("Start Redis first, then run: python3 src/demo.py", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        redis.close()

    return 0


def render(leaderboard: Leaderboard, label: str) -> None:
    print("\033c", end="")
    print(f"Real-time Redis Leaderboard ({label})")
    print("rank  player       score")
    print("------------------------")
    for row in leaderboard.top_n(10):
        print(f"{row['rank']:>4}  {row['player_id']:<10}  {row['score']:>6}")
    print(
        "\nRedis commands used: ZADD/ZINCRBY for writes, ZREVRANGE for Top-N, "
        "ZREVRANK+ZSCORE for player lookup, PUBLISH for update events."
    )


if __name__ == "__main__":
    raise SystemExit(main())
