FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GOOD_NEIGHBOR_SCENARIO=/app/evals/scenarios/demo_scenario.json

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY evals/scenarios ./evals/scenarios

RUN pip install --no-cache-dir . \
    && addgroup --system app \
    && adduser --system --ingroup app app

USER app
EXPOSE 8080

CMD ["python", "-m", "good_neighbor.agentcore_app"]
