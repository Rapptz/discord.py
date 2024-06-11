import sys
import pytest
import cov.cov


def main() -> None:
    arguments = sys.argv

    pytest.main(arguments[1:])
    cov.cov.print_table()


if __name__ == "__main__":
    main()
