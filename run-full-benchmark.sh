#!/bin/bash

# Full FFmpeg Benchmark Execution Script
# Run this on both x86 and Graviton instances

set -e

echo "Starting FFmpeg benchmark suite..."

# Create necessary directories
mkdir -p ~/ffmpeg-benchmark/{input,output,results,logs}
cd ~/ffmpeg-benchmark

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg not found! Please run setup-instances.sh first."
    exit 1
fi

# Log system information
echo "=== System Information ===" | tee logs/system_info.log
uname -a | tee -a logs/system_info.log
lscpu | tee -a logs/system_info.log
free -h | tee -a logs/system_info.log
ffmpeg -version | head -n1 | tee -a logs/system_info.log

# Check for input files
if [ ! "$(ls -A input/)" ]; then
    echo "No input files found. Downloading benchmark videos..."
    cd input
    
    # Download standard benchmark videos
    wget -O big_buck_bunny_1080p.mp4 "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    wget -O sintel_4k.mp4 "https://download.blender.org/demo/movies/Sintel.2010.2160p.mkv" || echo "Sintel 4K not available"
    
    cd ..
fi

# Run the benchmark
echo "Starting benchmark execution..."
python3 ../benchmark-runner.py --input-dir input --output-dir results

# Generate analysis if we have results from multiple architectures
echo "Checking for analysis..."
if [ -f ../analyze-results.py ]; then
    python3 ../analyze-results.py
fi

echo "Benchmark complete!"
echo "Results saved in: $(pwd)/results/"
echo "Logs saved in: $(pwd)/logs/"

# Display quick summary
echo ""
echo "=== Quick Summary ==="
echo "Architecture: $(uname -m)"
echo "Test files processed: $(ls input/ | wc -l)"
echo "Results generated: $(ls results/*.json 2>/dev/null | wc -l)"
echo "Output files created: $(ls output/ 2>/dev/null | wc -l)"