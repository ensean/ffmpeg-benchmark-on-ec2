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
    
    def get_video_info(self, video_path):
        """Get video duration and frame rate"""
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            if video_stream:
                duration = float(data['format']['duration'])
                fps = eval(video_stream['r_frame_rate'])
                return duration, fps
        return None, None
    
    def calculate_vmaf(self, reference_video, encoded_video):
        """Calculate VMAF score between reference and encoded video"""
        cmd = [
            "ffmpeg", "-i", encoded_video, "-i", reference_video,
            "-lavfi", "libvmaf=log_fmt=json:log_path=/tmp/vmaf.json",
            "-f", "null", "-"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            with open('/tmp/vmaf.json', 'r') as f:
                vmaf_data = json.load(f)
                return vmaf_data['pooled_metrics']['vmaf']['mean']
        except:
            return None
    
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
            
            # Get input and output files
            input_file = cmd[cmd.index("-i") + 1] if "-i" in cmd else None
            output_file = None
            for arg in cmd:
                if arg.endswith(('.mp4', '.mkv', '.webm', '.avi')) and not arg == input_file:
                    output_file = arg
                    break
            
            file_size = os.path.getsize(output_file) if output_file and os.path.exists(output_file) else 0
            
            # Calculate real-time factor using output video duration
            output_duration, input_fps = self.get_video_info(output_file) if output_file and os.path.exists(output_file) else (None, None)
            real_time_factor = output_duration / duration if output_duration and duration > 0 else None
            
            # Calculate VMAF if both files exist (limit to same duration)
            vmaf_score = None
            if input_file and output_file and os.path.exists(input_file) and os.path.exists(output_file):
                # For VMAF, we need to compare the same duration segments
                if output_duration:
                    # Create temporary input segment matching output duration
                    temp_input = "/tmp/temp_input_segment.mp4"
                    segment_cmd = ["ffmpeg", "-y", "-i", input_file, "-t", str(output_duration), "-c", "copy", temp_input]
                    try:
                        subprocess.run(segment_cmd, capture_output=True, timeout=300)
                        vmaf_score = self.calculate_vmaf(temp_input, output_file)
                        os.remove(temp_input)
                    except:
                        pass
            
            test_result = {
                "test_name": test_name,
                "command": ' '.join(cmd),
                "duration": duration,
                "success": result.returncode == 0,
                "avg_cpu_usage": avg_cpu,
                "max_cpu_usage": max_cpu,
                "avg_memory_usage": avg_memory,
                "output_file_size": file_size,
                "video_duration": output_duration,
                "input_fps": input_fps,
                "real_time_factor": real_time_factor,
                "vmaf_score": vmaf_score,
                "timestamp": datetime.now().isoformat(),
                "stderr": result.stderr,
                "stdout": result.stdout
            }
            
            self.results.append(test_result)
            rtf_str = f", RTF: {real_time_factor:.2f}x" if real_time_factor else ""
            vmaf_str = f", VMAF: {vmaf_score:.1f}" if vmaf_score else ""
            print(f"Test completed in {duration:.2f}s (CPU: {avg_cpu:.1f}%{rtf_str}{vmaf_str})")
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
    
    def run_encoding_tests(self, input_file, duration=None):
        """Run various encoding tests"""
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Check input video duration and limit if necessary
        input_duration, _ = self.get_video_info(input_file)
        if duration and input_duration and duration > input_duration:
            print(f"Warning: Requested duration {duration}s exceeds video length {input_duration:.1f}s. Using full video.")
            duration = None
        
        # Add duration parameter to FFmpeg commands if specified
        duration_args = ["-t", str(duration)] if duration else []
        
        tests = [
            # H.264 encoding tests
            {
                "name": f"h264_1mbps_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-c:v", "libx264", "-b:v", "1M", "-c:a", "aac", f"output/h264_1m_{base_name}.mp4"]
            },
            {
                "name": f"h264_5mbps_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-c:v", "libx264", "-b:v", "5M", "-c:a", "aac", f"output/h264_5m_{base_name}.mp4"]
            },
            # H.265 encoding tests
            {
                "name": f"h265_1mbps_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-c:v", "libx265", "-b:v", "1M", "-c:a", "aac", f"output/h265_1m_{base_name}.mp4"]
            },
            {
                "name": f"h265_5mbps_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-c:v", "libx265", "-b:v", "5M", "-c:a", "aac", f"output/h265_5m_{base_name}.mp4"]
            },
            # Transcode to different resolutions
            {
                "name": f"transcode_720p_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-vf", "scale=1280:720", "-c:v", "libx265", "-crf", "23", "-c:a", "aac", f"output/720p_{base_name}.mp4"]
            },
            {
                "name": f"transcode_540p_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-vf", "scale=960:540", "-c:v", "libx265", "-crf", "23", "-c:a", "aac", f"output/540p_{base_name}.mp4"]
            },
            {
                "name": f"transcode_360p_{base_name}",
                "cmd": ["ffmpeg", "-y"] + duration_args + ["-i", input_file, "-vf", "scale=640:360", "-c:v", "libx265", "-crf", "23", "-c:a", "aac", f"output/360p_{base_name}.mp4"]
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
    parser.add_argument('--duration', type=int, help='Duration in seconds to process (default: full video)')
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
        benchmark.run_encoding_tests(input_file, args.duration)
    
    # Save results
    benchmark.save_results()
    
    print(f"\nBenchmark complete! Ran {len(benchmark.results)} tests.")

if __name__ == "__main__":
    main()