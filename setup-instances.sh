#!/bin/bash

# FFmpeg Benchmark Instance Setup Script
# Uses FFmpeg binaries from BtbN/FFmpeg-Builds

set -e

echo "Setting up FFmpeg benchmark environment..."

# Detect architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Update system
sudo apt-get update -y

# Install dependencies
sudo apt-get install -y \
    wget \
    curl \
    xz-utils \
    htop \
    time \
    jq \
    python3 \
    python3-pip \
    awscli

# Download FFmpeg from BtbN/FFmpeg-Builds
echo "Downloading FFmpeg binary..."
if [ "$ARCH" = "x86_64" ]; then
    wget -O ffmpeg-release.tar.xz "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
elif [ "$ARCH" = "aarch64" ]; then
    wget -O ffmpeg-release.tar.xz "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
fi

# Extract and install FFmpeg
tar -xf ffmpeg-release.tar.xz
sudo cp ffmpeg-*/bin/* /usr/local/bin/
sudo chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
rm -rf ffmpeg-* ffmpeg-release.tar.xz

# Verify FFmpeg installation
ffmpeg -version

# Install Python dependencies for monitoring
pip3 install psutil boto3 matplotlib pandas

# Create benchmark directories
mkdir -p ~/ffmpeg-benchmark/{input,output,results,logs}

# Download sample test files
cd ~/ffmpeg-benchmark/input

# Download standard benchmark videos
echo "Downloading test files..."

# Big Buck Bunny (1080p, ~158MB, 9:56 duration)
wget -O big_buck_bunny_1080p.mp4 "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

# Sintel (4K, ~347MB, 14:48 duration)
wget -O sintel_4k.mp4 "https://download.blender.org/demo/movies/Sintel.2010.2160p.mkv" || echo "Sintel 4K not available"

# Tears of Steel (1080p, ~365MB, 12:14 duration)
wget -O tears_of_steel_1080p.mp4 "https://download.blender.org/demo/movies/ToS/ToS-4k-1920.mov" || echo "Tears of Steel not available"

# Elephants Dream (720p, ~213MB, 10:54 duration)
wget -O elephants_dream_720p.mp4 "https://download.blender.org/demo/movies/ED_1280.avi" || echo "Elephants Dream not available"

echo "Setup complete! Instance ready for FFmpeg benchmarking."
echo "Architecture: $ARCH"
echo "FFmpeg version: $(ffmpeg -version | head -n1)"