FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system packages
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    iputils-ping \
    telnet \
    netcat \
    nginx \
    apache2 \
    supervisor \
    cron \
    logrotate \
    && rm -rf /var/lib/apt/lists/*

# Create battle user and setup SSH
RUN useradd -m -s /bin/bash battle && \
    echo "battle:battle123" | chpasswd && \
    mkdir -p /home/battle/.ssh && \
    chown -R battle:battle /home/battle

# Setup SSH
RUN mkdir -p /var/run/sshd && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "AllowUsers battle" >> /etc/ssh/sshd_config && \
    echo "PubkeyAuthentication no" >> /etc/ssh/sshd_config && \
    echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config && \
    echo "UsePAM yes" >> /etc/ssh/sshd_config

# SSH login fix
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Create battle directories
RUN mkdir -p /battle/arena && \
    mkdir -p /battle/logs && \
    mkdir -p /battle/services && \
    chown -R battle:battle /battle

# Install Python packages for agents
RUN pip3 install requests flask fastapi uvicorn psutil

# Create startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create monitoring script
COPY monitor.sh /battle/monitor.sh
RUN chmod +x /battle/monitor.sh

# Create service management script
COPY service_manager.py /battle/service_manager.py
RUN chmod +x /battle/service_manager.py

# Expose ports
EXPOSE 22 80 8080

# Set working directory
WORKDIR /battle

# Start SSH and monitoring
CMD ["/start.sh"] 