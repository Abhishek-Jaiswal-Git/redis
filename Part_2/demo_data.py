import random
from typing import List

from leaderboard import Leaderboard


def player_name(player_number: int) -> str:
    return f"player:{player_number:04d}"


def seed_players(leaderboard: Leaderboard, total_players: int = 1000) -> None:
    batch_size = 100
    for start in range(1, total_players + 1, batch_size):
        end = min(total_players, start + batch_size - 1)
        scores = {}
        for player_number in range(start, end + 1):
            scores[player_name(player_number)] = random.randint(0, 20)
        leaderboard.redis.zadd(leaderboard.key, scores)


def apply_random_updates(
    leaderboard: Leaderboard,
    total_players: int = 1000,
    updates: int = 25,
    min_delta: int = 10,
    max_delta: int = 50,
) -> List[str]:
    update_list = []
    changed_players = []
    
    for _ in range(updates):
        player_id = player_name(random.randint(1, total_players))
        delta = random.randint(min_delta, max_delta)
        update_list.append((player_id, delta))
        changed_players.append(player_id)
    
    # Send updates in one Redis pipeline to reduce network round trips.
    leaderboard.mass_increment(update_list)
    return changed_players
