# Use an official Python runtime as a parent image
FROM python:3.10.12

# Set the working directory in the container
WORKDIR /Climate-Information-System


# Install system dependencies
RUN apt-get update && apt-get install -y \
pkg-config \
libmariadb-dev \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /Climate-Information-System
COPY . /Climate-Information-System

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
#ENV PYTHONUNBUFFERED=1

# Run the application using SSL

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]


# CMD ["python3", "manage.py", "runserver_plus", "0.0.0.0:8000", "--cert-file", "/Climate-Information-System/cert_django.pem", "--key-file", "/Climate-Information-System/key_django.pem"]

