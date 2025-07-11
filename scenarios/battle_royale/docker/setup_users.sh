#!/bin/bash
set -e

for i in 1 2 3; do
  user="red$i"
  pass="red${i}pass"
  useradd -m -s /bin/bash $user
  echo "$user:$pass" | chpasswd
  usermod -aG sudo $user
  echo "$user created with password $pass"
  echo "SSH: $user@<container_ip> (password: $pass)"
done 