#!/usr/bin/env python3

import os
import sys
import time
import json
import subprocess
import psutil
import threading
from datetime import datetime
import argparse

class FFmpegBenchmark:
    def __init__(self, output_dir="results"):
        self.output_dir = output_dir
        self.results = []
        self.monitoring = True
        
    def get_system_info(self):
        """Collect system information"""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "memory_total": psutil.virtual_memory().total,
            "architecture": os.uname().machine,
            "platform": os.uname().sysname
        }
    
    def monitor_resources(self, interval=1):
        """Monitor CPU and memory usage during encoding"""
        self.cpu_usage = []
        self.memory_usage = []
        
        while self.monitoring:
            self.cpu_usage.append(psutil.cpu_percent())
            self.memory_usage.append(psutil.virtual_memory().percent)
            time.sleep(interval)
    
    def run_ffmpeg_command(self, cmd, test_name):
        """Execute FFmpeg command and collect metrics"""
        print(f"Running test: {test_name}")
        print(f"Command: {' '.join(cmd)}")
        
        # Start resource monitoring
        self.monitoring = True
        monitor_thread = threading.Thread(target=self.monitor_resources)
        monitor_thread.start()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Run FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            end_time = time.time()
            
            # Stop monitoring
            self.monitoring = False
            monitor_thread.join()
            
            # Calculate metrics
            duration = end_time - start_time
            avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
            max_cpu = max(self.cpu_usage) if self.cpu_usage else 0
            avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
            
            # Get output file size
            output_file = None
            for arg in cmd:
                if arg.endswith(('.mp4', '.mkv', '.webm', '.avi')):
                    output_file = arg
                    break
            
            file_size = os.path.getsize(output_file) if output_file and os.path.exists(output_file) else 0
            
            test_result = {
                "test_name": test_name,
                "command": ' '.join(cmd),
                "duration": duration,
                "success": result.returncode == 0,
                "avg_cpu_usage": avg_cpu,
                "max_cpu_usage": max_cpu,
                "avg_memory_usage": avg_memory,
                "output_file_size": file_size,
                "timestamp": datetime.now().isoformat(),
                "stderr": result.stderr,
                "stdout": result.stdout
            }
            
            self.results.append(test_result)
            print(f"Test completed in {duration:.2f}s (CPU: {avg_cpu:.1f}%)")
            return test_result
            
        except subprocess.TimeoutExpired:
            self.monitoring = False
            monitor_thread.join()
            print(f"Test {test_name} timed out")
            return None
        except Exception as e:
            self.monitoring = False
            monitor_thread.join()
            print(f"Test {test_name} failed: {e}")
            return None
    
    def run_encoding_tests(self, input_file):
        """Run various encoding tests"""
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        tests = [
            # H.264 encoding tests
            {
                "name": f"h264_1mbps_{base_name}",
                "cmd": ["ffmpeg", "-y", "-i", input_file, "-c:v", "libx264", "-b:v", "1M", "-c:a", "aac", f"output/h264_1m_{base_name}.mp4"]
            },
            {
                "name": f"h264_5mbps_{base_name}",
                "cmd": ["ffmpeg", "-y", "-i", input_file, "-c:v", "libx264", "-b:v", "5M", "-c:a", "aac", f"output/h264_5m_{base_name}.mp4"]
            },
            # H.265 encoding tests
            {
                "name": f"h265_1mbps_{base_name}",
                "cmd": ["ffmpeg", "-y", "-i", input_file, "-c:v", "libx265", "-b:v", "1M", "-c:a", "aac", f"output/h265_1m_{base_name}.mp4"]
            },
            {
                "name": f"h265_5mbps_{base_name}",
                "cmd": ["ffmpeg", "-y", "-i", input_file, "-c:v", "libx265", "-b:v", "5M", "-c:a", "aac", f"output/h265_5m_{base_name}.mp4"]
            }
        ]
        
        for test in tests:
            self.run_ffmpeg_command(test["cmd"], test["name"])
    
    def save_results(self):
        """Save benchmark results to JSON file"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Add system info to results
        final_results = {
            "system_info": self.get_system_info(),
            "benchmark_results": self.results,
            "total_tests": len(self.results),
            "successful_tests": len([r for r in self.results if r.get("success", False)])
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arch = os.uname().machine
        filename = f"{self.output_dir}/ffmpeg_benchmark_{arch}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"Results saved to: {filename}")
        return filename

def main():
    parser = argparse.ArgumentParser(description='FFmpeg Benchmark Runner')
    parser.add_argument('--input-dir', default='input', help='Input directory with test files')
    parser.add_argument('--output-dir', default='results', help='Output directory for results')
    args = parser.parse_args()
    
    benchmark = FFmpegBenchmark(args.output_dir)
    
    # Find input files
    input_files = []
    for file in os.listdir(args.input_dir):
        if file.endswith(('.mp4', '.mov', '.avi', '.mkv')):
            input_files.append(os.path.join(args.input_dir, file))
    
    if not input_files:
        print("No input files found!")
        sys.exit(1)
    
    print(f"Found {len(input_files)} input files")
    
    # Run tests for each input file
    for input_file in input_files:
        print(f"\nTesting with: {input_file}")
        benchmark.run_encoding_tests(input_file)
    
    # Save results
    benchmark.save_results()
    
    print(f"\nBenchmark complete! Ran {len(benchmark.results)} tests.")

if __name__ == "__main__":
    main()