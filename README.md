# FFmpeg Benchmark: x86 vs Graviton Performance Comparison

This repository contains a comprehensive benchmark suite for comparing FFmpeg performance between x86 (Intel/AMD) and ARM-based AWS Graviton instances.

## Quick Start

### 1. Launch Instances

Use the Ubuntu 22.04 image for benchmark


### 2. Setup Instances
```bash
# Copy setup script to instances
scp -i ~/.ssh/your-key.pem setup-instances.sh ubuntu@<instance-ip>:~/
scp -i ~/.ssh/your-key.pem *.py ubuntu@<instance-ip>:~/

# SSH to each instance and run setup
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>
chmod +x setup-instances.sh
./setup-instances.sh
```

### 3. Run Benchmarks
```bash
# On each instance, run the full benchmark
chmod +x run-full-benchmark.sh
./run-full-benchmark.sh
```

### 4. Collect and Analyze Results
```bash
# Download results from all instances
scp -i ~/.ssh/your-key.pem ubuntu@<instance-ip>:~/ffmpeg-benchmark/results/*.json ./results/

# Run analysis (requires results from multiple architectures)
python3 analyze-results.py
```

## Files Description

- **ffmpeg-benchmark-plan.md**: Detailed benchmark strategy and methodology
- **setup-instances.sh**: Instance preparation script (installs FFmpeg, dependencies)
- **benchmark-runner.py**: Main benchmark execution script with performance monitoring
- **analyze-results.py**: Results analysis and comparison report generator
- **run-full-benchmark.sh**: Complete benchmark orchestration script

## Test Scenarios

### Video Encoding Tests
- H.264 encoding (1Mbps, 5Mbps bitrates)
- H.265/HEVC encoding (1Mbps, 5Mbps bitrates)
- Multiple input resolutions (4K, 1080p, 720p)

### Metrics Collected
- Encoding duration (seconds)
- CPU utilization (average and peak)
- Memory usage
- Output file sizes
- Processing speed (FPS)

## Instance Types Tested

### x86 Instances
- c5.xlarge (4 vCPU, 8 GB RAM) - Intel Xeon Platinum 8124M
- c7i.xlarge (4 vCPU, 8 GB RAM) - Intel Xeon Ice Lake
- c7a.xlarge (4 vCPU, 8 GB RAM) - AMD EPYC 3rd Gen

### Graviton Instances
- c8g.xlarge (4 vCPU, 8 GB RAM) - AWS Graviton4

## Expected Outputs

1. **JSON Results**: Detailed performance metrics per test
2. **Analysis Report**: Markdown report with performance comparisons
3. **Visualizations**: Charts comparing architectures across different metrics
4. **Cost Analysis**: Performance per dollar calculations

## Prerequisites

- AWS CLI configured
- Terraform installed
- EC2 Key Pair created
- Python 3.7+ with pip

## Cost Considerations

Estimated costs for running the full benchmark suite:
- 4 instances × 2 hours × $0.15-0.25/hour = $1.20-2.00 total
- Actual costs depend on instance types and region

## Cleanup

```bash
# Destroy infrastructure when done
terraform destroy -var="key_pair_name=your-key-pair"
```