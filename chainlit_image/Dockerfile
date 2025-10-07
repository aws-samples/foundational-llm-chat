FROM ghcr.io/astral-sh/uv:python3.13-alpine

# update the apk 
RUN apk upgrade --no-cache

# add build-base for gcc compiler
RUN apk add --no-cache build-base

# add a new user and change to the new user
# this is done to do not run the container as Root
# Create a group and user
RUN addgroup -S chainlitworkergroup && adduser -S chainlitworker -G chainlitworkergroup
USER chainlitworker

# Optimize environment variables:
# - Disable Python log buffering to avoid losing logs during unhandled error/termination
# - Compile bytecode for files after installation, for performance
# - Use the specific, pre-installed Python version from the source container above
# - Never download other Python versions
ENV PYTHONUNBUFFERED 1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON=python3.13 \
    UV_PYTHON_DOWNLOADS=never

# Set the working directory where user has access
WORKDIR /home/chainlitworker/app

# Update path to access user-installed libraries (in advance, to suppress warnings later)
ENV PATH="/home/chainlitworker/.local/bin:${PATH}"

# Copy just the requirements file at this stage, so that changes to the Python source don't need to
# trigger a whole dependency install re-run
COPY  --chown=chainlitworker:chainlitworker \
  ./foundational-llm-chat_app/pyproject.toml ./foundational-llm-chat_app/uv.lock ./

# Install the requirements (but not the package itself because we haven't copied the code yet)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code over & install it
COPY --chown=chainlitworker:chainlitworker ./foundational-llm-chat_app .
RUN uv sync --frozen --no-dev

EXPOSE 8080

CMD ["uv", "run", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8080"]
