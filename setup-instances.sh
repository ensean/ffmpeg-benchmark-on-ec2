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

# Check if FFmpeg already exists
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg already installed, skipping..."
else
    echo "Downloading FFmpeg binary..."
    if [ "$ARCH" = "x86_64" ]; then
        wget -O ffmpeg-release.tar.xz "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif [ "$ARCH" = "aarch64" ]; then
        wget -O ffmpeg-release.tar.xz "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
    fi
    
    tar -xf ffmpeg-release.tar.xz
    sudo cp ffmpeg-*/bin/* /usr/local/bin/
    sudo chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
    rm -rf ffmpeg-* ffmpeg-release.tar.xz
fi

# Verify FFmpeg installation
ffmpeg -version

# Install Python dependencies for monitoring and VMAF
pip3 install psutil boto3 matplotlib pandas numpy

# Check if VMAF already exists
if ldconfig -p | grep -q libvmaf; then
    echo "VMAF already installed, skipping..."
else
    echo "Installing VMAF..."
    sudo apt-get install -y build-essential meson ninja-build nasm
    git clone https://github.com/Netflix/vmaf.git
    cd vmaf/libvmaf
    meson setup build --buildtype release
    ninja -vC build
    sudo ninja -C build install
    sudo ldconfig
    cd ../..
fi

# Create benchmark directories
mkdir -p ./ffmpeg-benchmark/{input,output,results,logs}

# Download sample test files
cd ./ffmpeg-benchmark/input

# Download standard benchmark videos
echo "Downloading test files..."

# Big Buck Bunny (1080p, ~158MB, 9:56 duration)
wget -O big_buck_bunny_1080p_fps30.mp4 "https://raw.githubusercontent.com/chintan9/Big-Buck-Bunny/refs/heads/master/BigBuckBunny1080p30s.mp4"

# Tears of Steel (1080p, ~365MB, 12:14 duration)
# wget -O tears_of_steel_1080p.mp4 "https://download.blender.org/demo/movies/ToS/ToS-4k-1920.mov" || echo "Tears of Steel not available"


echo "Setup complete! Instance ready for FFmpeg benchmarking."
echo "Architecture: $ARCH"
echo "FFmpeg version: $(ffmpeg -version | head -n1)"