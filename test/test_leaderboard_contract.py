import unittest


class InMemoryLeaderboard:
    def __init__(self):
        self.scores = {}

    def update_score(self, player_id, score):
        self.scores[player_id] = int(score)

    def increment_score(self, player_id, delta):
        score = self.scores.get(player_id, 0) + int(delta)
        self.scores[player_id] = score
        return score

    def top_n(self, limit):
        ordered = sorted(self.scores.items(), key=lambda row: (-row[1], row[0]))
        return [
            {"rank": index + 1, "player_id": player_id, "score": score}
            for index, (player_id, score) in enumerate(ordered[:limit])
        ]

    def get_player(self, player_id):
        for row in self.top_n(len(self.scores)):
            if row["player_id"] == player_id:
                return row
        return {"rank": None, "player_id": player_id, "score": None}


class LeaderboardContractTest(unittest.TestCase):
    def test_update_top_n_and_player_rank_lookup(self):
        leaderboard = InMemoryLeaderboard()

        leaderboard.update_score("ada", 100)
        leaderboard.update_score("linus", 80)
        leaderboard.update_score("grace", 120)
        leaderboard.increment_score("linus", 50)

        self.assertEqual(
            leaderboard.top_n(2),
            [
                {"rank": 1, "player_id": "linus", "score": 130},
                {"rank": 2, "player_id": "grace", "score": 120},
            ],
        )
        self.assertEqual(
            leaderboard.get_player("ada"),
            {"rank": 3, "player_id": "ada", "score": 100},
        )
        self.assertEqual(
            leaderboard.get_player("missing"),
            {"rank": None, "player_id": "missing", "score": None},
        )


if __name__ == "__main__":
    unittest.main()
