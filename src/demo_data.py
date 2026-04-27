import random
from typing import List

from leaderboard import Leaderboard


def player_name(player_number: int) -> str:
    return f"player:{player_number:04d}"


def seed_players(leaderboard: Leaderboard, total_players: int = 1000) -> None:
    batch_size = 100
    for start in range(1, total_players + 1, batch_size):
        args = ["ZADD", leaderboard.key]
        end = min(total_players, start + batch_size - 1)
        for player_number in range(start, end + 1):
            args.extend([random.randint(0, 50_000), player_name(player_number)])
        leaderboard.redis.command(*args)


def apply_random_updates(
    leaderboard: Leaderboard,
    total_players: int = 1000,
    updates: int = 25,
    min_delta: int = 100,
    max_delta: int = 5_000,
) -> List[str]:
    changed_players = []
    for _ in range(updates):
        player_id = player_name(random.randint(1, total_players))
        leaderboard.increment_score(player_id, random.randint(min_delta, max_delta))
        changed_players.append(player_id)
    return changed_players
