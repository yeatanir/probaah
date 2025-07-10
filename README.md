# Probaah - Automated Research Workflow Engine

> *Where research flows naturally* - প্ৰবাহ

## Quick Start

```bash
# Clone and setup
git clone https://github.com/anirban-psu/probaah.git
cd probaah
./setup.sh --user anirban --cluster roar_collab
```

---

## Repository Structure

```
probaah/
├── README.md                     # This file
├── claude.md                     # Claude Code context file
├── setup.sh                      # One-command setup script
├── requirements.txt              # Python dependencies
├── .gitignore                    # Ignore sensitive files
├── LICENSE                       # MIT License
│
├── core/                         # Core engine (scalable)
│   ├── __init__.py
│   ├── user_manager.py          # Single user → multi-tenant
│   ├── project_manager.py       # Project organization
│   ├── sync_engine.py           # Cross-device sync
│   ├── plugin_loader.py         # Modular plugins
│   └── config_manager.py        # Configuration handling
│
├── plugins/                      # Feature modules
│   ├── __init__.py
│   ├── slurm_integration/       # SLURM job management
│   │   ├── __init__.py
│   │   ├── monitor.py
│   │   ├── submit.py
│   │   └── templates/
│   ├── email_automation/        # Email triggers & notifications
│   │   ├── __init__.py
│   │   ├── outlook_integration.py
│   │   └── templates/
│   ├── paper_delivery/          # Daily papers system
│   │   ├── __init__.py
│   │   ├── arxiv_scraper.py
│   │   └── formatters/
│   ├── visualization/           # Ovito Python integration
│   │   ├── __init__.py
│   │   ├── trajectory_analyzer.py
│   │   └── rendering/
│   └── custom_scripts/          # AI-generated script management
│       ├── __init__.py
│       ├── generator.py
│       └── templates/
│
├── config/                       # Configuration templates
│   ├── user_profile.yaml.template
│   ├── cluster_config.yaml.template
│   ├── sync_settings.yaml.template
│   └── plugin_settings.yaml.template
│
├── templates/                    # Project & file templates
│   ├── reaxff/
│   │   ├── input_files/
│   │   ├── job_scripts/
│   │   └── analysis_scripts/
│   ├── gaussian/
│   ├── ams/
│   └── custom/
│
├── context/                      # Context files for Claude
│   ├── reaxff_documentation/
│   ├── slurm_commands/
│   ├── python_libraries/
│   └── best_practices/
│
├── cli/                          # Command line interface
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── commands/
│   │   ├── project.py
│   │   ├── jobs.py
│   │   ├── sync.py
│   │   └── config.py
│   └── utils/
│
├── tests/                        # Test suite
│   ├── test_core/
│   ├── test_plugins/
│   └── test_integration/
│
├── docs/                         # Documentation
│   ├── getting_started.md
│   ├── architecture.md
│   ├── plugin_development.md
│   └── examples/
│
└── scripts/                      # Utility scripts
    ├── install_dependencies.sh
    ├── setup_ssh_keys.sh
    └── backup_configs.sh
```

---

## Core Files to Create First

### 1. setup.sh
```bash
#!/bin/bash
# Probaah Setup Script
echo "🌊 Setting up Probaah (প্ৰবাহ) - Where research flows naturally"

# Check requirements
python3 --version || { echo "Python 3.8+ required"; exit 1; }
git --version || { echo "Git required"; exit 1; }

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python3 -m probaah.cli.main init "$@"

echo "✅ Probaah setup complete! Try: probaah project create test-project"
```

### 2. requirements.txt
```
# Core dependencies
pyyaml>=6.0
click>=8.0
rich>=13.0
paramiko>=3.0
requests>=2.28

# Scientific computing
numpy>=1.21
pandas>=1.5
matplotlib>=3.6

# Email integration
exchangelib>=5.0

# Optional visualization
ovito>=3.9.0

# Development
pytest>=7.0
black>=22.0
flake8>=5.0
```

### 3. .gitignore
```
# Sensitive files - NEVER commit these!
config/user_profile.yaml
config/*_credentials.yaml
.ssh_keys/
*.pem

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
data/sensitive/
logs/
temp/
*.tmp

# Large files (use Git LFS instead)
*.xyz
*.bgf
*.traj
*.mp4
```

### 4. LICENSE
```
MIT License

Copyright (c) 2025 Anirban Pal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Initial Commands Available

```bash
# Project management
probaah project create "lithium-battery-study" --type reaxff
probaah project list
probaah project status

# Job management  
probaah jobs submit input.xyz --cluster roar_collab --time 48h
probaah jobs monitor
probaah jobs list --running

# Configuration
probaah config setup --cluster roar_collab
probaah config sync --devices laptop,macmini,onedrive

# Development
probaah script generate "radial distribution analysis" --auto-doc
probaah template create --type custom --name my-analysis
```

---

## Next Steps (After Initial Setup)

1. **Configure SSH**: `probaah config ssh --cluster roar_collab`
2. **Set up sync**: `probaah sync setup --onedrive --devices laptop,macmini`
3. **Create first project**: `probaah project create test --type reaxff`
4. **Submit test job**: `probaah jobs submit test.xyz --dry-run`

---

## Development Roadmap

- [x] Core architecture design
- [ ] Basic project management (Week 1)
- [ ] SLURM integration (Week 1)
- [ ] Email notifications (Week 2)
- [ ] Ovito visualization (Week 2)
- [ ] Daily papers delivery (Week 3)
- [ ] Multi-device sync (Week 3)
- [ ] Plugin marketplace (Future)

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test thoroughly
4. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

*Probaah (প্ৰবাহ): Where computational chemistry research flows naturally*
