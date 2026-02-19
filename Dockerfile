# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Set environment variables
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr.
# GRADIO_SERVER_NAME: Binds the Gradio server to all network interfaces.
# GRADIO_SERVER_PORT: Sets the port for the Gradio server.
ENV PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT=8080

# Set the working directory in the container
WORKDIR /app

# Install uv, the fast Python package installer.
RUN pip install uv

# Copy only the files that are listed in the libraries.
COPY pyproject.toml uv.lock ./

#Install the dependencies
RUN uv pip install --system -r pyproject.toml

# create the log directory
run mkdir -p /app/logs

# Copy all the files from the current directory to the container.
COPY . .


# Expose the port the app runs on
EXPOSE 8080

# Run the application using python.
CMD ["python", "src/ChatTwin/GradioUI.py"]
