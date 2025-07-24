FROM ubuntu:22.04

# Install SSH server and other utilities
RUN apt-get update && apt-get install -y \
    openssh-server \
    curl \
    wget \
    vim \
    python3 \
    python3-pip \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create SSH directory and set up SSH
RUN mkdir /var/run/sshd

# Accept password as build argument, default to password123
ARG ROOT_PASSWORD=password123
RUN echo "root:${ROOT_PASSWORD}" | chpasswd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Create flag directory
RUN mkdir -p /root

# Copy flag generation script
COPY generate_flag.py /root/generate_flag.py
RUN chmod +x /root/generate_flag.py

# Expose SSH port
EXPOSE 22

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"] 