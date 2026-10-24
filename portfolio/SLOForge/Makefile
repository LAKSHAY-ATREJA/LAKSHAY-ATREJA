.PHONY: demo format-check lint test verify

demo:
	uv run python demo.py

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

test:
	uv run pytest -q

verify: format-check lint test demo
