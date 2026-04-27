import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    if "--cli" in sys.argv or "cli" in sys.argv:
        from demo import main as cli_main

        return cli_main()

    from streamlit_app import main as streamlit_main

    streamlit_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
