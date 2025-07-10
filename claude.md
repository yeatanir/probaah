# Probaah - Claude Code Context File

> **IMPORTANT**: This file provides context for Claude Code to work effectively with Probaah (প্ৰবাহ), an automated research workflow system for computational chemistry, specifically ReaxFF simulations.

---

## Project Overview

**Probaah** is a personal research automation system designed for ADHD-friendly computational chemistry workflows. It automates repetitive tasks, organizes research files intelligently, and integrates with SLURM clusters for job management.

**Primary User**: Anirban (akp6421), PhD student in van Duin group at Penn State, working on ReaxFF molecular dynamics simulations.

**Core Philosophy**: "If I have to do it more than twice, the system should do it for me."

---

## System Architecture

```
Probaah Framework
├── core/                    # Core functionality
├── plugins/                 # Modular features
├── templates/               # File templates
├── context/                 # Documentation for Claude
└── cli/                     # Command interface
```

**Key Principles:**
- Modular plugin architecture for scalability
- Configuration-driven (YAML files)
- Cross-platform compatibility (Windows WSL, macOS, Linux)
- Local AI integration (no sensitive data to cloud)
- Git-based version control by default

---

## ReaxFF & Computational Chemistry Context

### What is ReaxFF?
ReaxFF (Reactive Force Field) is a molecular dynamics simulation method that allows chemical bonds to form and break during simulation. Developed by Adri van Duin.

### Common File Types
- **Input Files**:
  - `.xyz` - Atomic coordinates
  - `.bgf` - BioPlex Graphics Format (alternative coordinate format)
  - `tregime.in` - Temperature regime input
  - `ffield` - Force field parameters
  - `control` - Control parameters for simulation
  
- **Output Files**:
  - `xmolout.xyz` - Trajectory file with atomic positions over time
  - `.out` - Main output file with energies, temperatures
  - `.log` - Simulation log file

- **Cluster Files**:
  - `.slurm` or `.sb` - SLURM job submission scripts
  - Queue system: SLURM on Penn State Roar Collab cluster

### Typical ReaxFF Workflow
1. **Preparation**: Create initial structure (.xyz), define force field (ffield), set control parameters
2. **Submission**: Submit job to SLURM cluster via `sbatch`
3. **Monitoring**: Check job status with `squeue -u username`
4. **Analysis**: Process trajectory (`xmolout.xyz`), calculate properties, visualize with Ovito
5. **Visualization**: Create movies, snapshots, analyze molecular behavior

---

## Cluster Environment: Penn State Roar Collab

### Connection Details
- **Hostname**: `submit.aci.ics.psu.edu`
- **Username**: `akp6421`
- **Queue System**: SLURM
- **Common Partitions**: `open`, `sla-prio`
- **Time Limits**: Max 168 hours (7 days) for long jobs

### SLURM Commands
```bash
# Submit job
sbatch job_script.slurm

# Check queue
squeue -u akp6421

# Check job details
scontrol show job JOBID

# Cancel job
scancel JOBID

# Job history
sacct -u akp6421 --starttime=2025-07-01
```

### Typical SLURM Script Template
```bash
#!/bin/bash
#SBATCH --job-name=reaxff_sim
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=20
#SBATCH --time=48:00:00
#SBATCH --mem=32GB
#SBATCH --partition=open

module load reaxff

# Run simulation
reaxff < tregime.in > output.log
```

---

## Available Tools & Libraries

### Python Libraries (Confirmed Available)
```python
# Core scientific computing
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# File handling
import yaml
import json
import paramiko  # SSH connections

# Visualization (when available)
import ovito  # Molecular visualization
from ovito.io import import_file
from ovito.modifiers import *

# Email integration
from exchangelib import *  # Outlook integration

# CLI tools
import click  # Command line interface
from rich import print  # Beautiful terminal output
```

### System Tools
- **Git**: Version control (every project is a Git repository)
- **SSH**: Cluster access via paramiko
- **YAML**: Configuration files
- **Outlook API**: Email automation via Microsoft Graph

---

## Project Structure Standards

### Standard Project Layout
```
project_name_YYYYMMDD/
├── README.md                 # Auto-generated summary
├── .probaah-config.yaml     # Project configuration
├── input_files/
│   ├── templates/           # Reusable templates
│   ├── current/             # Active inputs
│   └── archive/             # Completed runs
├── job_scripts/
│   ├── slurm_templates/
│   ├── active_jobs/
│   └── completed_jobs/
├── trajectories/
│   ├── raw/                 # xmolout.xyz files
│   ├── processed/           # Analyzed data
│   └── videos/              # MP4 renders
├── analysis/
│   ├── scripts/             # Custom analysis
│   ├── results/             # Output data
│   └── figures/             # Publication plots
└── notes/
    ├── daily_logs/
    └── observations/
```

### File Naming Conventions
- Dates: `YYYYMMDD` format
- Projects: `descriptive_name_date`
- Jobs: `jobtype_system_temperature_date`
- Scripts: `analysis_description_vN.py`

---

## Common Tasks & Code Patterns

### 1. Project Creation
```python
def create_project(name, project_type="reaxff"):
    """Create organized project structure"""
    timestamp = datetime.now().strftime("%Y%m%d")
    project_dir = f"{name}_{timestamp}"
    
    # Create standard directories
    directories = [
        "input_files/templates",
        "job_scripts/slurm_templates", 
        "trajectories/raw",
        "analysis/scripts",
        "notes/daily_logs"
    ]
    
    for dir_path in directories:
        os.makedirs(f"{project_dir}/{dir_path}", exist_ok=True)
```

### 2. SLURM Job Monitoring
```python
def check_jobs(username="akp6421"):
    """Check SLURM job status via SSH"""
    ssh = paramiko.SSHClient()
    ssh.connect("submit.aci.ics.psu.edu")
    
    stdin, stdout, stderr = ssh.exec_command(f"squeue -u {username}")
    return stdout.read().decode()
```

### 3. Trajectory Analysis
```python
def analyze_trajectory(xyz_file):
    """Basic trajectory analysis with Ovito"""
    pipeline = import_file(xyz_file)
    
    # Add modifiers
    pipeline.modifiers.append(CoordinationAnalysisModifier())
    pipeline.modifiers.append(CommonNeighborAnalysisModifier())
    
    return pipeline
```

### 4. Email Automation
```python
def send_completion_email(job_name, status):
    """Send job completion notification"""
    subject = f"🎉 Job {job_name} completed!"
    body = f"""
    Your ReaxFF simulation has finished.
    Status: {status}
    
    Ready for analysis? Reply 'Yes' to start automated analysis.
    """
    # Implementation using exchangelib
```

---

## Configuration Examples

### User Profile (user_profile.yaml)
```yaml
user:
  name: "Anirban"
  email: "akp6421@psu.edu"
  cluster_username: "akp6421"
  research_focus: ["ReaxFF", "materials", "battery"]

clusters:
  roar_collab:
    hostname: "submit.aci.ics.psu.edu"
    username: "akp6421"
    max_jobs: 50
    default_partition: "open"

sync:
  devices: ["laptop-wsl", "macmini"]
  onedrive: true
  auto_backup: true
```

### Project Config (.probaah-config.yaml)
```yaml
project:
  name: "lithium_battery_degradation"
  type: "reaxff"
  created: "2025-07-09"
  description: "Li-ion battery SEI formation study"

simulation:
  force_field: "ffield.reax"
  temperature: "298K"
  pressure: "1atm"
  steps: 1000000

analysis:
  auto_render: true
  notification_email: true
  backup_to_onedrive: true
```

---

## Error Handling Guidelines

### Common Issues & Solutions
1. **SSH Connection Fails**: Check VPN, verify credentials
2. **Job Submission Errors**: Validate SLURM script syntax
3. **File Not Found**: Use absolute paths, verify sync status
4. **Ovito Import Fails**: Check file format, atom count consistency
5. **Email Sending Fails**: Verify Outlook credentials, API limits

### Debugging Protocol
```python
def debug_mode(func):
    """Wrapper for debugging with detailed logging"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger.info(f"✅ {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ {func.__name__} failed: {str(e)}")
            raise
    return wrapper
```

---

## Code Generation Guidelines

### 1. Always Include Docstrings
```python
def analyze_bonds(trajectory_file):
    """
    Analyze bond formation/breaking in ReaxFF trajectory.
    
    Args:
        trajectory_file (str): Path to xmolout.xyz file
        
    Returns:
        dict: Bond analysis results with counts and statistics
        
    Example:
        results = analyze_bonds("trajectory.xyz")
        print(f"Total bonds formed: {results['bonds_formed']}")
    """
```

### 2. Use Type Hints
```python
from typing import List, Dict, Optional
from pathlib import Path

def process_results(
    files: List[Path], 
    output_dir: Path,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
```

### 3. Error Handling
```python
try:
    # Risky operation
    result = risky_function()
except FileNotFoundError:
    logger.error("Input file not found")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 4. Configuration-Driven
```python
def load_config(config_path: str = "config/user_profile.yaml"):
    """Load user configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
```

---

## CLI Command Patterns

### Standard Command Structure
```bash
probaah <category> <action> [arguments] [options]

# Examples:
probaah project create "battery-study" --type reaxff
probaah jobs submit input.xyz --time 48h --partition open
probaah sync status --devices all
probaah config setup --cluster roar_collab
```

### Plugin Commands
```bash
probaah <plugin> <action> [arguments]

# Examples:
probaah slurm monitor --user akp6421
probaah email setup --provider outlook
probaah ovito render trajectory.xyz --output video.mp4
```

---

## Security & Best Practices

### 1. Never Commit Sensitive Data
- SSH private keys
- API credentials
- User email addresses
- Cluster passwords

### 2. Use Environment Variables
```python
import os
cluster_host = os.getenv('CLUSTER_HOST', 'submit.aci.ics.psu.edu')
username = os.getenv('CLUSTER_USER', 'default_user')
```

### 3. Validate Inputs
```python
def validate_xyz_file(filepath):
    """Validate XYZ file format"""
    if not filepath.endswith('.xyz'):
        raise ValueError("File must be .xyz format")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
```

---

## Testing Guidelines

### Unit Tests
```python
def test_project_creation():
    """Test project directory structure creation"""
    project = create_project("test_project")
    assert os.path.exists(f"{project}/input_files")
    assert os.path.exists(f"{project}/analysis/scripts")
```

### Integration Tests
```python
def test_slurm_connection():
    """Test SLURM cluster connectivity"""
    jobs = check_jobs("akp6421")
    assert isinstance(jobs, str)
    assert "JOBID" in jobs  # Header should be present
```

---

## Remember: User Context

**User Profile**: Anirban has ADHD and gets frustrated with repetitive tasks. He wants maximum automation with minimal setup. He's tech-savvy but not a software engineer - needs tools that are powerful but intuitive.

**Goals**: 
- Eliminate boring repetitive tasks
- Organize chaotic research files
- Automate job submission and monitoring
- Focus on research, not file management

**Constraints**:
- Works on both Windows (WSL) and macOS
- Uses Penn State infrastructure (Roar Collab, OneDrive, Outlook)
- Needs free/open-source tools (student budget)
- Prefers command-line interfaces

---

*This context file ensures Claude Code understands the domain, tools, and user needs for effective Probaah development.*
