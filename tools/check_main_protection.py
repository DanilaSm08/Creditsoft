"""Run the GitHub branch protection proof against the failing control pull request."""

from prove_controls import prove

if __name__ == "__main__":
    prove(32)
