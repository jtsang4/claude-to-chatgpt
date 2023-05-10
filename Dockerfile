FROM python:3.9-slim-buster

WORKDIR /app

# Set the environment variables
ENV CLAUDE_BASE_URL="https://api.anthropic.com"
ENV LOG_LEVEL="info"

# Copy the rest of the application code to the container
COPY . .

# Install Poetry
RUN pip install poetry

RUN poetry install --only main

# Expose the port the app runs on
EXPOSE 8000

# Set the command to run the application
CMD ["poetry", "run", "python", "claude_to_chatgpt/app.py"]
