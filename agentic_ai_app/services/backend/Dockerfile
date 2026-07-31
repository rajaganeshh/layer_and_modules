ARG BASE_IMAGE
FROM $BASE_IMAGE

ARG APPLICATION_NAME

# Copy application source code
COPY services/${APPLICATION_NAME}/src/ /app/

# Set working directory
WORKDIR /app

# Install ca-certificates (required for HTTPS) and any other dependencies
RUN apk update && apk upgrade && apk add --no-cache ca-certificates bash

# Debug: list contents
RUN pwd && ls -ltr *

# Expose port
EXPOSE 80

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]