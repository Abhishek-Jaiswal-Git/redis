# Real-Time Redis Leaderboard

This demo implements a real-time gaming leaderboard for roughly 1000 concurrent players whose scores change continuously. The important part is Redis: the app code is intentionally small, while Redis handles ordering, rank lookup, and fast Top-N reads.

## Data Model

Primary structure:

```text
ZSET leaderboard:game:global
member = player id, for example player:0042
score  = numeric game score
```

Redis sorted sets are a natural fit because they keep members ordered by score while supporting score updates.

Commands used:

| Requirement | Redis command | Complexity |
| --- | --- | --- |
| Add/update score | `ZADD leaderboard:game:global <score> <playerId>` | `O(log N)` |
| Increment score | `ZINCRBY leaderboard:game:global <delta> <playerId>` | `O(log N)` |
| Retrieve Top-N | `ZREVRANGE leaderboard:game:global 0 N-1 WITHSCORES` | `O(log N + N)` |
| Retrieve rank | `ZREVRANK leaderboard:game:global <playerId>` | `O(log N)` |
| Retrieve score | `ZSCORE leaderboard:game:global <playerId>` | `O(1)` |
| Broadcast update | `PUBLISH leaderboard:updates <json>` | `O(subscribers)` |

For richer production profiles, keep player metadata separately in `HASH player:<id>` or in the primary database. The leaderboard should only store fields needed for ranking.

## Why Redis

Redis brings three useful properties to this problem:

1. **Low-latency rank maintenance:** every score update updates the ordered index immediately.
2. **Simple read path:** Top 10 is one command and does not require sorting in the app.
3. **Atomic commands:** each `ZADD` or `ZINCRBY` is atomic, so concurrent writers do not corrupt rankings.

With 1000 active users this is comfortably small for one Redis instance. The same pattern also scales well to many more players, especially when leaderboards are partitioned by game, season, region, or time window.

## Demo

The demo is a zero-dependency Python CLI. It talks to Redis using RESP over TCP, seeds 1000 players into a sorted set, then continuously updates random players and redraws the Top 10. It also publishes update events to show how another process could refresh a UI.

There is also a Streamlit UI for visualizing the same Redis sorted set in a browser.

### Prerequisites

Python 3.9+ and access to the Redis OSS server at `34.93.131.87:6380`.

Run the demo directly against that server:

```bash
python3 main.py --cli
```

Run the Streamlit UI:

```bash
python3 -m pip install -r requirements.txt
streamlit run main.py --server.port 8501
```

The UI shows live Top-N rankings, score bars, total players, the current leader, reset/seed controls, a live simulation toggle, and three requirement tabs: add/update score, retrieve Top-N players, and retrieve a player's rank and score.

The default URL is:

```bash
redis://34.93.131.87:6380
```

Optional settings:

```bash
PLAYERS=1000 TICKS=60 UPDATES_PER_TICK=50 INTERVAL_MS=250 python3 main.py --cli
REDIS_URL=redis://34.93.131.87:6380 python3 main.py --cli
REDIS_URL=redis://34.93.131.87:6380 streamlit run main.py --server.port 8501
```

If you want to run against local Redis instead:

```bash
docker run --rm -p 6379:6379 redis:7
REDIS_URL=redis://127.0.0.1:6379 python3 main.py --cli
```

### Verification

Run the lightweight contract test:

```bash
python3 -m unittest discover -s test
```

Manual Redis checks while the demo is running:

```bash
redis-cli -h 34.93.131.87 -p 6380 ZCARD leaderboard:game:global
redis-cli -h 34.93.131.87 -p 6380 ZREVRANGE leaderboard:game:global 0 9 WITHSCORES
redis-cli -h 34.93.131.87 -p 6380 ZREVRANK leaderboard:game:global player:0001
redis-cli -h 34.93.131.87 -p 6380 ZSCORE leaderboard:game:global player:0001
```

Expected behavior:

- `ZCARD` returns the number of seeded players.
- `ZREVRANGE ... WITHSCORES` matches the Top 10 printed by the CLI.
- A player's displayed rank is `ZREVRANK + 1`.

## Correctness Validation

Key invariants:

- Every player appears at most once in the sorted set because the player id is the member.
- Updating a player score replaces that member's score rather than adding a duplicate.
- Top-N is always ordered by descending score because reads use `ZREVRANGE`.
- Rank lookup is consistent with the same sorted set because reads use `ZREVRANK`.

For automated validation at larger scale, generate deterministic updates, mirror them in an in-memory reference model, and periodically compare Redis `ZREVRANGE` output with the reference model's sorted result.

## Performance Validation

Measure:

- Write latency: `ZADD`/`ZINCRBY` p50, p95, p99.
- Read latency: `ZREVRANGE 0 9 WITHSCORES` p50, p95, p99.
- Rank lookup latency: `ZREVRANK` + `ZSCORE`.
- Redis CPU, memory, connected clients, rejected connections.
- Command throughput: operations per second.
- Pub/Sub subscriber lag or dropped UI refreshes.
- Error rate and timeout rate in the app.

Load testing approach:

1. Run 1000 simulated players.
2. Apply a realistic update rate, for example 25 to 100 score updates per second.
3. Read Top 10 several times per second from one or more clients.
4. Compare Redis output against a reference model for correctness.
5. Increase update rate until p99 latency or CPU crosses the target threshold.

## Alternatives Considered

| Option | Pros | Cons |
| --- | --- | --- |
| SQL table with index on score | Durable source of truth, familiar operations | High write churn and repeated Top-N queries can become expensive |
| App memory heap | Very low latency inside one process | Hard to share across instances, restart loses state, rank lookup is awkward |
| Kafka plus stream processor | Excellent event pipeline and auditability | More moving pieces, not ideal for direct low-latency rank reads |

The implemented solution uses a Redis sorted set. Production systems often combine Redis with one of these alternatives: Redis serves the live leaderboard, while durable storage keeps long-term history and recovery snapshots.

## Production Notes

- Use one sorted set per leaderboard scope, such as `leaderboard:<gameId>:<seasonId>:global`.
- Add TTLs for short-lived event leaderboards.
- Use Redis replication or managed Redis for high availability.
- Persist score events to a durable log if scores must be replayable.
- For massive leaderboards, shard by game/region and maintain separate global aggregations.
- Define tie-breaking rules explicitly. Redis breaks equal-score ordering lexicographically within sorted-set ordering, which may be acceptable for games where exact ties are rare.
