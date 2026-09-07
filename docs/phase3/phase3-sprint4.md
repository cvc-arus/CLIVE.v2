### Summary of Our Verification & Quality Gates

To lock in this step's contract, ensure that your design document (docs/phase3-sprint4.md) records the exact execution sequence we defined in the previous steps:

## A. The Offline vs. Online Test Execution Sequence

The developer must run the test suites in this strict sequence:

# 1. Run all unit tests locally with Docker stopped (zero network calls)
pytest -q -m "not integration"

# 2. Boot up the high-fidelity mock service in the background
docker compose up -d --build simpro-mock

# 3. Run the live integration test suites against the running mock
pytest -q -m integration

## B. The Static Quality Check Sequence

Before any commit can be staged, the developer must prove that the workspace is clean of formatting bugs and whitespace discrepancies:

# Run Ruff linting and formatting syntax checks
ruff check .
ruff format --check .

# Reject any accidental trailing whitespaces or conflict markers
git diff --check

# Check what files are dirty or untracked
git status --short

## C. The Staging and Commit Sequence

Once everything is confirmed clean, the commit is recorded intentionally:

# Stage all approved changes (avoiding cached or temporary metadata)
git add -A

# Commit with a clear, descriptive architectural prefix
git commit -m "feat: add typed Simpro client layer"

# Verify that the working directory is now completely clean (returns no output)
git status --short

## D. The Intact Volume Cleanup Rule

We preserve our seeded database schemas during development using a safe cleanup command:

docker compose down

Why? Because omitting the -v flag guarantees that your local PostgreSQL database volumes are not destroyed, preserving vital testing state across restarts.

 ---