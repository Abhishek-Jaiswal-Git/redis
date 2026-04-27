import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from demo_data import apply_random_updates, player_name, seed_players
from leaderboard import Leaderboard
from redis_client import RedisClient


DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://34.93.131.87:6380")
DEFAULT_PLAYERS = int(os.getenv("PLAYERS", "1000"))


st.set_page_config(
    page_title="Redis Leaderboard",
    page_icon=":material/leaderboard:",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-left: 1rem; padding-right: 1rem; max-width: none;}
    [data-testid="stMetricValue"] { font-size: 1.45rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #e5e7eb; border-radius: 8px; }
    .stat-box {
        min-height: 5.2rem;
        padding: 0.2rem 0 0.4rem 0;
    }
    .stat-label {
        color: #4b5563;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .stat-value {
        color: #111827;
        font-size: 1.75rem;
        font-weight: 800;
        line-height: 1.05;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    .stat-subvalue {
        color: #6b7280;
        font-size: 0.8rem;
        margin-top: 0.2rem;
    }
    .score-row {
        border-bottom: 1px solid #e5e7eb;
        padding: 0.55rem 0 0.7rem 0;
    }
    .score-row-header {
        align-items: baseline;
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.35rem;
    }
    .score-row-player {
        font-size: 1.05rem;
        font-weight: 700;
    }
    .score-row-score {
        color: #374151;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 1rem;
    }
    .redis-command {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.7rem 0.85rem;
        background: #f9fafb;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main() -> None:
    init_state()

    with st.sidebar:
        st.header("Redis")
        redis_url = st.text_input("URL", value=st.session_state.redis_url)
        total_players = st.number_input("Players", min_value=10, max_value=100_000, value=st.session_state.players, step=100)
        top_n = st.slider("Top N", min_value=3, max_value=50, value=10)
        auto_refresh = st.toggle("Live simulation", value=st.session_state.live)
        updates_per_tick = st.slider("Updates per refresh", min_value=1, max_value=200, value=25)
        refresh_ms = st.slider("Refresh interval (ms)", min_value=250, max_value=5_000, value=1_000, step=250)

        st.session_state.redis_url = redis_url
        st.session_state.players = int(total_players)
        st.session_state.live = auto_refresh

        col_a, col_b = st.columns(2)
        seed_clicked = col_a.button("Seed", width="stretch")
        reset_clicked = col_b.button("Reset", width="stretch")

    try:
        redis = connect(redis_url)
        leaderboard = Leaderboard(redis)
    except OSError as error:
        st.error(f"Could not connect to Redis: {error}")
        return

    try:
        handle_seed_and_reset(leaderboard, seed_clicked, reset_clicked, int(total_players))
        if auto_refresh:
            started = time.perf_counter()
            changed = apply_random_updates(leaderboard, int(total_players), updates_per_tick)
            st.session_state.last_tick_ms = (time.perf_counter() - started) * 1000
            st.session_state.last_changed = changed[-1] if changed else None

        top_rows = leaderboard.top_n(top_n)
        render_header(leaderboard, top_rows, updates_per_tick)

        score_col, actions_col = st.columns([1.75, 0.85], gap="large")
        with score_col:
            render_scoreboard(top_rows, top_n)
        with actions_col:
            render_functional_requirements(leaderboard, top_n)
            render_redis_panel(leaderboard, top_n)
    except RuntimeError as error:
        st.error(f"Redis command failed: {error}")
    finally:
        redis.close()

    if auto_refresh:
        time.sleep(refresh_ms / 1000)
        st.rerun()


def init_state() -> None:
    defaults = {
        "redis_url": DEFAULT_REDIS_URL,
        "players": DEFAULT_PLAYERS,
        "live": False,
        "last_tick_ms": 0.0,
        "last_changed": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def connect(redis_url: str) -> RedisClient:
    url = urlparse(redis_url)
    database = int(url.path.lstrip("/")) if url.path and url.path != "/" else None
    redis = RedisClient(
        url.hostname or "127.0.0.1",
        url.port or 6379,
        username=url.username,
        password=url.password,
        database=database,
    )
    redis.connect()
    return redis


def handle_seed_and_reset(leaderboard: Leaderboard, seed_clicked: bool, reset_clicked: bool, total_players: int) -> None:
    if reset_clicked:
        leaderboard.reset()
        st.toast("Leaderboard reset")
    if seed_clicked or leaderboard.count() == 0:
        leaderboard.reset()
        seed_players(leaderboard, total_players)
        st.toast(f"Seeded {total_players} players")


def render_header(leaderboard: Leaderboard, top_rows, updates_per_tick: int) -> None:
    leader = top_rows[0] if top_rows else {"player_id": "-", "score": 0}

    st.title("Redis Real-Time Leaderboard")
    stat_a, stat_b, stat_c, stat_d = st.columns([1, 1.35, 1, 1])
    with stat_a:
        render_stat("Players", f"{leaderboard.count():,}")
    with stat_b:
        render_stat("Leader", leader["player_id"])
    with stat_c:
        render_stat("Top Score", f"{leader['score']:,}")
    with stat_d:
        render_stat("Last Tick", f"{st.session_state.last_tick_ms:.1f} ms", f"{updates_per_tick} updates")


def render_stat(label: str, value: str, subvalue: str = "") -> None:
    subvalue_html = f'<div class="stat-subvalue">{subvalue}</div>' if subvalue else ""
    st.markdown(
        f"""
        <div class="stat-box">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            {subvalue_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scoreboard(top_rows, top_n: int) -> None:
    st.subheader(f"Global Top {top_n}")
    st.dataframe(top_rows, hide_index=True, width="stretch", height=360)

    st.subheader("Live Score Spread")
    max_score = max((row["score"] for row in top_rows), default=1)
    for row in top_rows:
        ratio = row["score"] / max_score if max_score else 0
        st.markdown(
            f"""
            <div class="score-row">
                <div class="score-row-header">
                    <span class="score-row-player">#{row["rank"]} {row["player_id"]}</span>
                    <span class="score-row-score">{row["score"]:,}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(ratio)


def render_functional_requirements(leaderboard: Leaderboard, top_n: int) -> None:
    st.subheader("Functional Requirements")
    update_tab, top_tab, player_tab = st.tabs(
        [
            "Add/update score",
            "Retrieve Top-N players",
            "Retrieve player rank and score",
        ]
    )

    with update_tab:
        left, right = st.columns([1, 1])
        with left:
            target_number = st.number_input(
                "Player",
                min_value=1,
                max_value=st.session_state.players,
                value=1,
                key="update_player_number",
            )
            target_id = player_name(int(target_number))
            st.metric("Selected player", target_id)
        with right:
            delta = st.number_input(
                "Increment by",
                min_value=-10_000,
                max_value=100_000,
                value=1_000,
                step=100,
                key="increment_delta",
            )
            absolute_score = st.number_input(
                "Set score to",
                min_value=0,
                max_value=10_000_000,
                value=75_000,
                step=1_000,
                key="absolute_score",
            )

        action_a, action_b = st.columns(2)
        if action_a.button("Run ZINCRBY", width="stretch"):
            new_score = leaderboard.increment_score(target_id, int(delta))
            st.session_state.last_action = f"{target_id} score is now {new_score:,}"
            st.rerun()
        if action_b.button("Run ZADD", width="stretch"):
            leaderboard.update_score(target_id, int(absolute_score))
            st.session_state.last_action = f"{target_id} score set to {int(absolute_score):,}"
            st.rerun()
        if st.session_state.get("last_action"):
            st.success(st.session_state.last_action)

    with top_tab:
        requested_top_n = st.slider(
            "N",
            min_value=1,
            max_value=100,
            value=top_n,
            key="requirement_top_n",
        )
        st.dataframe(leaderboard.top_n(requested_top_n), hide_index=True, width="stretch")

    with player_tab:
        lookup_number = st.number_input(
            "Player",
            min_value=1,
            max_value=st.session_state.players,
            value=1,
            key="lookup_player_number",
        )
        lookup_id = player_name(int(lookup_number))
        player = leaderboard.get_player(lookup_id)
        rank = "-" if player["rank"] is None else player["rank"]
        score = "-" if player["score"] is None else f"{player['score']:,}"
        rank_col, score_col = st.columns(2)
        rank_col.metric("Rank", rank)
        score_col.metric("Score", score)


def render_redis_panel(leaderboard: Leaderboard, top_n: int) -> None:
    st.subheader("Redis Commands")
    commands = [
        f"ZINCRBY {leaderboard.key} <delta> <playerId>",
        f"ZREVRANGE {leaderboard.key} 0 {top_n - 1} WITHSCORES",
        f"ZREVRANK {leaderboard.key} <playerId>",
        f"ZSCORE {leaderboard.key} <playerId>",
    ]
    st.markdown(
        "".join(f'<div class="redis-command">{command}</div>' for command in commands),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
