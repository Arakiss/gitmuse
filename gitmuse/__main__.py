import sys
from gitmuse.cli.cli_core import run_cli, run_commit


def main():
    if len(sys.argv) == 1:
        run_commit()
    else:
        run_cli()


if __name__ == "__main__":
    main()
