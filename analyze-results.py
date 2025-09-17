#!/usr/bin/env python3

import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime

class BenchmarkAnalyzer:
    def __init__(self):
        self.results = {}
        
    def load_results(self, results_dir="results"):
        """Load all benchmark result files"""
        for filename in os.listdir(results_dir):
            if filename.endswith('.json') and 'ffmpeg_benchmark' in filename:
                filepath = os.path.join(results_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    arch = data['system_info']['architecture']
                    self.results[arch] = data
        
        print(f"Loaded results for architectures: {list(self.results.keys())}")
    
    def create_comparison_dataframe(self):
        """Create DataFrame for comparison analysis"""
        rows = []
        
        for arch, data in self.results.items():
            system_info = data['system_info']
            for result in data['benchmark_results']:
                if result.get('success', False):
                    rows.append({
                        'architecture': arch,
                        'cpu_count': system_info['cpu_count'],
                        'memory_total_gb': system_info['memory_total'] / (1024**3),
                        'test_name': result['test_name'],
                        'duration': result['duration'],
                        'avg_cpu_usage': result['avg_cpu_usage'],
                        'max_cpu_usage': result['max_cpu_usage'],
                        'avg_memory_usage': result['avg_memory_usage'],
                        'output_file_size_mb': result['output_file_size'] / (1024**2),
                        'fps': self.calculate_fps(result)
                    })
        
        return pd.DataFrame(rows)
    
    def calculate_fps(self, result):
        """Calculate frames per second (estimate based on duration)"""
        # Assume 30 fps input for calculation
        if result['duration'] > 0:
            return 30 / result['duration']
        return 0
    
    def generate_performance_report(self):
        """Generate comprehensive performance comparison report"""
        df = self.create_comparison_dataframe()
        
        if df.empty:
            print("No data available for analysis")
            return
        
        report = []
        report.append("# FFmpeg Benchmark Analysis Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Architecture summary
        report.append("## Architecture Summary")
        for arch in df['architecture'].unique():
            arch_data = df[df['architecture'] == arch]
            avg_duration = arch_data['duration'].mean()
            avg_cpu = arch_data['avg_cpu_usage'].mean()
            
            report.append(f"### {arch}")
            report.append(f"- Average encoding time: {avg_duration:.2f}s")
            report.append(f"- Average CPU usage: {avg_cpu:.1f}%")
            report.append(f"- Tests completed: {len(arch_data)}")
            report.append("")
        
        # Performance comparison by test type
        report.append("## Performance Comparison by Test Type")
        
        test_types = ['h264_1mbps', 'h264_5mbps', 'h265_1mbps', 'h265_5mbps']
        
        for test_type in test_types:
            test_data = df[df['test_name'].str.contains(test_type)]
            if not test_data.empty:
                report.append(f"### {test_type.upper()}")
                
                for arch in test_data['architecture'].unique():
                    arch_test_data = test_data[test_data['architecture'] == arch]
                    avg_duration = arch_test_data['duration'].mean()
                    avg_fps = arch_test_data['fps'].mean()
                    
                    report.append(f"- {arch}: {avg_duration:.2f}s avg, {avg_fps:.2f} fps")
                
                report.append("")
        
        # Performance ratios
        if len(df['architecture'].unique()) >= 2:
            archs = list(df['architecture'].unique())
            arch1, arch2 = archs[0], archs[1]
            
            report.append("## Performance Ratios")
            
            for test_type in test_types:
                test_data = df[df['test_name'].str.contains(test_type)]
                if not test_data.empty:
                    arch1_avg = test_data[test_data['architecture'] == arch1]['duration'].mean()
                    arch2_avg = test_data[test_data['architecture'] == arch2]['duration'].mean()
                    
                    if arch1_avg > 0 and arch2_avg > 0:
                        ratio = arch1_avg / arch2_avg
                        faster_arch = arch1 if ratio > 1 else arch2
                        ratio = max(ratio, 1/ratio)
                        
                        report.append(f"- {test_type}: {faster_arch} is {ratio:.2f}x faster")
            
            report.append("")
        
        # Save report
        report_text = "\n".join(report)
        with open("benchmark_analysis_report.md", "w") as f:
            f.write(report_text)
        
        print("Analysis report saved to: benchmark_analysis_report.md")
        return report_text
    
    def create_visualizations(self):
        """Create performance visualization charts"""
        df = self.create_comparison_dataframe()
        
        if df.empty:
            print("No data available for visualization")
            return
        
        # Performance comparison chart
        plt.figure(figsize=(12, 8))
        
        # Duration comparison
        plt.subplot(2, 2, 1)
        df.groupby(['architecture', 'test_name'])['duration'].mean().unstack().plot(kind='bar')
        plt.title('Average Encoding Duration by Architecture')
        plt.ylabel('Duration (seconds)')
        plt.xticks(rotation=45)
        
        # CPU usage comparison
        plt.subplot(2, 2, 2)
        df.groupby(['architecture', 'test_name'])['avg_cpu_usage'].mean().unstack().plot(kind='bar')
        plt.title('Average CPU Usage by Architecture')
        plt.ylabel('CPU Usage (%)')
        plt.xticks(rotation=45)
        
        # FPS comparison
        plt.subplot(2, 2, 3)
        df.groupby(['architecture', 'test_name'])['fps'].mean().unstack().plot(kind='bar')
        plt.title('Processing Speed (FPS) by Architecture')
        plt.ylabel('Frames per Second')
        plt.xticks(rotation=45)
        
        # File size comparison
        plt.subplot(2, 2, 4)
        df.groupby(['architecture', 'test_name'])['output_file_size_mb'].mean().unstack().plot(kind='bar')
        plt.title('Output File Size by Architecture')
        plt.ylabel('File Size (MB)')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('ffmpeg_benchmark_comparison.png', dpi=300, bbox_inches='tight')
        print("Visualization saved to: ffmpeg_benchmark_comparison.png")

def main():
    analyzer = BenchmarkAnalyzer()
    
    # Load results
    analyzer.load_results()
    
    if not analyzer.results:
        print("No benchmark results found!")
        sys.exit(1)
    
    # Generate report and visualizations
    analyzer.generate_performance_report()
    analyzer.create_visualizations()
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()