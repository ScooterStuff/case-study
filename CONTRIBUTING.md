# Contributing

```bash
cp .env.example .env   # or skip and use MOCK_LLM=1
make setup             # venv + deps + pre-commit hooks
make test              # pytest + jest
make lint              # ruff check + format
```

- Conventional commits: `feat(scope): …`, `fix(scope): …`, `test: …`, `chore: …`.
- `pre-commit install` runs ruff/format/detect-secrets on every commit.
- Agent *quality* changes need an eval case in `eval/cases.json`; run
  `make eval` and commit the regenerated `eval/RESULTS.md`.
