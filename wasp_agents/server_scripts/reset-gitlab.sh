#!/bin/bash

# Setup script for Reddit and GitLab Docker services
# This script sets up the required Docker containers for WASP benchmark

set -e  # Exit on any error

echo "Setting up GitLab service..."
# Stop and remove existing gitlab container
docker stop gitlab 2>/dev/null || echo "No existing gitlab container to stop"
docker rm gitlab 2>/dev/null || echo "No existing gitlab container to remove"

# Start new gitlab container
echo "Starting GitLab container..."
docker run --name gitlab -d -p 8023:8023 --privileged gitlab-populated-final-port8023 /opt/gitlab/embedded/bin/runsvdir-start

# Configure GitLab external URL
echo "Configuring GitLab external URL..."
docker exec gitlab sed -i "s|^external_url.*|external_url 'http://ec2-18-224-83-14.us-east-2.compute.amazonaws.com:8023'|" /etc/gitlab/gitlab.rb
docker exec gitlab gitlab-ctl reconfigure

echo "GitLab is running on port 8023"