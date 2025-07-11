FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && \
    apt-get install -y openssh-server python3 python3-pip sudo net-tools curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create SSH directory and set root password
RUN mkdir /var/run/sshd && echo 'root:root' | chpasswd

# Allow password authentication
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Add setup scripts
COPY setup_users.sh /setup_users.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /setup_users.sh /entrypoint.sh

# Expose SSH and web ports
EXPOSE 22 80

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"] 