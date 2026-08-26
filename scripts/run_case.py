import argparse
from pathlib import Path

from fem_engine.run import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an FEM case from a TOML config.")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run_dir = run(args.config)
    print(f"Wrote outputs to {run_dir}")


if __name__ == "__main__":
    main()
