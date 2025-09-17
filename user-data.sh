#!/bin/bash

# EC2 User Data script for FFmpeg benchmark instances
# Architecture: ${architecture}

set -e

# Update system
apt-get update -y

# Install dependencies
apt-get install -y \
    wget \
    curl \
    xz-utils \
    htop \
    time \
    jq \
    python3 \
    python3-pip \
    awscli

# Download and install FFmpeg from BtbN/FFmpeg-Builds
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    wget -O /tmp/ffmpeg-release.tar.xz "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
elif [ "$ARCH" = "aarch64" ]; then
    wget -O /tmp/ffmpeg-release.tar.xz "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
fi

cd /tmp
tar -xf ffmpeg-release.tar.xz
cp ffmpeg-*/bin/* /usr/local/bin/
chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
rm -rf ffmpeg-* ffmpeg-release.tar.xz

# Install Python packages
pip3 install psutil boto3 matplotlib pandas

# Create ubuntu user directories
sudo -u ubuntu mkdir -p /home/ubuntu/ffmpeg-benchmark/{input,output,results,logs}

# Download benchmark scripts from S3 or GitHub (placeholder)
# In real deployment, you'd upload scripts to S3 and download them here
# aws s3 cp s3://your-bucket/benchmark-scripts/ /home/ubuntu/ffmpeg-benchmark/ --recursive

# Set permissions
chown -R ubuntu:ubuntu /home/ubuntu/ffmpeg-benchmark/

# Log completion
echo "Instance setup complete for ${architecture}" > /home/ubuntu/setup-complete.log
echo "$(date): FFmpeg benchmark instance ready" >> /home/ubuntu/setup-complete.log