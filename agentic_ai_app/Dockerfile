ARG BASE_IMAGE
FROM $BASE_IMAGE

# Copy the src folder from the build context into the image

RUN apk update && apk upgrade && apk add --no-cache curl

RUN apk add --update nodejs npm && node -v && npm -v


# Use golden image as a build argument
#ARG BASE_IMAGE=alpine:latest
#FROM ${BASE_IMAGE}

# Set the working directory in the container

#WORKDIR /app

# Install Node.js and npm
#RUN apk add --no-cache nodejs npm

# Copy requirements file and install dependencies
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
#COPY src/ .

# Expose the port your app runs on (change if needed)
#EXPOSE 8080

# Set the default command to run your app (adjust as needed)
#CMD ["echo", "hello world"]
