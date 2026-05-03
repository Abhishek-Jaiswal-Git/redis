# Redis Real-Time Data & Replication Project

This repository contains a two-part implementation of distributed data systems using Redis and Python.

## 🚀 Project Overview
* **Part 1: Redis Setup & Replication** — Focuses on cross-server replication between Redis OSS and Redis Enterprise.
* **Part 2: Real-Time Leaderboard Demo** — A Python-based application simulating 1,000 concurrent players with live score updates.

## 🛠 Tech Stack
* **Database:** Redis (OSS & Enterprise)
* **Language:** Python
* **Frontend:** Streamlit for real-time visualization
* **Infrastructure:** Distributed Redis replication

## 📂 Repository Structure
* `Part_1/`: Configuration files and documentation for Redis replication. **[Part 1: Redis Setup & Replication](./Part_1/README-Part1.md)**
* `Part_2/`: Source code for the gaming leaderboard, including `leaderboard.py` and `streamlit_app.py`. **[Part 2: Real-Time Leaderboard](./Part_2/README-Part2.md)**

## 🚦 Getting Started
1. Go to the Part 2 app directory: `cd Part_2`
2. Install dependencies: `python3 -m pip install -r requirements.txt`
3. Run the dashboard: `python3 -m streamlit run streamlit_app.py --server.port 8501`
