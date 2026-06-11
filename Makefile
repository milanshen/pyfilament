image-base:
	podman build -f Dockerfile -t pyfilament/filament-base:dev-latest .

image-ui:
	podman build -f ui/Dockerfile -t pyfilament/ui:dev-latest ui

install:
	poetry install

upgrade:
	poetry run alembic upgrade head

lint:
	poetry run ruff check src/ --ignore F401,E402,E731,F841,F403,E712,E722,E711,F541

test:
	poetry run pytest

test-coverage:
	poetry run coverage run -m pytest

coverage-clean:
	rm -rf .coverage*

coverage-report:
	poetry run coverage xml -o .coverage.xml && poetry run coverage html -d .coverage_html && poetry run diff-cover .coverage.xml --compare-branch=main --html-report .coverage_diff.html

coverage: coverage-clean test-coverage coverage-report
