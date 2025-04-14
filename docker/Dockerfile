FROM python:3.10 AS builder

WORKDIR /usr/src/app

RUN python -m venv /avito_env
ENV PATH="/avito_env/bin:$PATH"

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY src src/

FROM python:3.10 AS test_runner
WORKDIR /usr/src/app

COPY --from=builder /avito_env /avito_env
ENV PATH="/avito_env/bin:$PATH"

COPY tests tests/

RUN pip install pytest
WORKDIR /usr/src/app/tests
RUN pytest .

FROM python:3.10 AS service
WORKDIR /usr/src/app

COPY --from=builder /avito_env /avito_env
ENV PATH="/avito_env/bin:$PATH"

COPY src src/

ENV PYTHONPATH=/usr/src/app/src
CMD ["python", "-m", "uvicorn", "src.endpoints.main:app", "--host", "0.0.0.0", "--port", "4000"]