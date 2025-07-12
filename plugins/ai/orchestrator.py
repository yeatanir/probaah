# FILE: plugins/ai/orchestrator.py
"""
AI Orchestrator for Probaah
Central coordinator for natural language workflow automation
"""

import re
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
import yaml

# Import Probaah components
from .packmol_wrapper import ProbaahPackmol
from .visual_validation import VIAMDIntegration
from .tools.existing_probaah_tools import ExistingProbaahTools
from .tools.molecular_tools import MolecularTools

console = Console()

class ProbaahAIOrchestrator:
    """
    Central AI coordinator for natural language workflow automation
    Parses requests and orchestrates existing and new tools
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AI orchestrator
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.tools = self._initialize_tools()
        self.workflow_history = []
        self.current_context = {}
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or defaults"""
        default_config = {
            'ai': {
                'default_model': 'gpt-4o',
                'fallback_model': 'llama3-405b',
                'visual_validation': True,
                'auto_cleanup_delay': 30,
                'orchestrate_existing': True,
                'enhance_analysis': True,
                'enhance_presentations': True
            },
            'molecular': {
                'packmol': {
                    'executable': 'auto',
                    'default_tolerance': 2.0,
                    'timeout_seconds': 300
                },
                'viamd': {
                    'executable': 'auto',
                    'auto_download': False,
                    'temp_cleanup_delay': 30
                }
            },
            'dft': {
                'jaguar': {
                    'license_file': 'auto',
                    'scratch_dir': '/tmp/jaguar'
                },
                'gaussian': {
                    'executable': 'g16',
                    'memory': '8GB'
                }
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge with defaults
                    return {**default_config, **user_config}
            except Exception as e:
                console.print(f"⚠️  Config load error: {e}, using defaults")
                
        return default_config
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize all available tools"""
        tools = {}
        
        try:
            # Initialize molecular tools
            tools['packmol'] = ProbaahPackmol(
                executable_path=self.config['molecular']['packmol'].get('executable')
            )
            tools['viamd'] = VIAMDIntegration(
                viamd_path=self.config['molecular']['viamd'].get('executable')
            )
            
            # Initialize existing Probaah tools
            tools['existing_probaah'] = ExistingProbaahTools()
            tools['molecular_tools'] = MolecularTools()
            
        except Exception as e:
            console.print(f"⚠️  Tool initialization warning: {e}")
            
        return tools
    
    def parse_natural_language_request(self, request: str) -> Dict[str, Any]:
        """
        Parse natural language request into structured commands
        
        Args:
            request: Natural language request
            
        Returns:
            Parsed command structure
        """
        request_lower = request.lower()
        
        # Command parsing patterns
        patterns = {
            'substitute': r'substitute|replace|swap',
            'remove': r'remove|delete|eliminate',
            'add': r'add|insert|place',
            'analyze': r'analyze|analysis|examine|study',
            'validate': r'validate|verify|check|inspect',
            'presentation': r'presentation|slides|powerpoint|ppt',
            'visualize': r'visualize|render|display|show',
            'workflow': r'workflow|pipeline|process|complete'
        }
        
        # Extract entities
        entities = self._extract_entities(request)
        
        # Determine primary action
        primary_action = None
        for action, pattern in patterns.items():
            if re.search(pattern, request_lower):
                primary_action = action
                break
        
        # Build command structure
        command = {
            'original_request': request,
            'primary_action': primary_action,
            'entities': entities,
            'parameters': self._extract_parameters(request),
            'workflow_steps': self._infer_workflow_steps(request, primary_action, entities),
            'timestamp': time.time()
        }
        
        return command
    
    def _extract_entities(self, request: str) -> Dict[str, List[str]]:
        """Extract entities from natural language request"""
        entities = {
            'files': [],
            'molecules': [],
            'numbers': [],
            'properties': []
        }
        
        # File patterns
        file_patterns = [
            r'(\w+\.(xyz|pdb|bgf|traj|car|mol2))',
            r'(\w+_\w+\.(xyz|pdb|bgf|traj|car|mol2))',
            r'([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, request, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    entities['files'].append(match[0])
                else:
                    entities['files'].append(match)
        
        # Molecule patterns
        molecule_patterns = [
            r'\b(O2|N2|CO2|H2O|CH4|C2H6|NH3)\b',
            r'\b([A-Z][a-z]?\d*)\b',
            r'(\d+\s+[A-Z][a-z]?\s*radicals?)',
            r'(\d+\s+[A-Z][a-z]?\s*atoms?)'
        ]
        
        for pattern in molecule_patterns:
            matches = re.findall(pattern, request, re.IGNORECASE)
            entities['molecules'].extend(matches)
        
        # Number patterns
        number_patterns = [
            r'(\d+(?:\.\d+)?)',
            r'(density\s+(\d+(?:\.\d+)?))',
            r'(count\s+(\d+))'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, request, re.IGNORECASE)
            entities['numbers'].extend(matches)
        
        return entities
    
    def _extract_parameters(self, request: str) -> Dict[str, Any]:
        """Extract parameters from natural language request"""
        parameters = {}
        
        # Density parameter
        density_match = re.search(r'density\s+(\d+(?:\.\d+)?)', request, re.IGNORECASE)
        if density_match:
            parameters['density'] = float(density_match.group(1))
        
        # Count parameter
        count_match = re.search(r'(\d+)\s+(?:molecules?|atoms?|radicals?)', request, re.IGNORECASE)
        if count_match:
            parameters['count'] = int(count_match.group(1))
        
        # Visual validation
        if re.search(r'visual|validate|check|inspect', request, re.IGNORECASE):
            parameters['visual_validation'] = True
        
        # Analysis options
        if re.search(r'bond|rdf|energy|plot', request, re.IGNORECASE):
            parameters['analysis_options'] = {
                'bonds': bool(re.search(r'bond', request, re.IGNORECASE)),
                'rdf': bool(re.search(r'rdf', request, re.IGNORECASE)),
                'energy': bool(re.search(r'energy', request, re.IGNORECASE)),
                'plots': bool(re.search(r'plot', request, re.IGNORECASE))
            }
        
        return parameters
    
    def _infer_workflow_steps(self, request: str, primary_action: str, 
                            entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Infer workflow steps from parsed request"""
        steps = []
        
        # Multi-step workflow patterns
        if 'then' in request.lower() or 'and' in request.lower():
            # Split by conjunctions
            parts = re.split(r'\s+(?:then|and|,)\s+', request, flags=re.IGNORECASE)
            
            for part in parts:
                part = part.strip()
                if part:
                    step_action = self._identify_action(part)
                    steps.append({
                        'action': step_action,
                        'description': part,
                        'estimated_time': self._estimate_step_time(step_action)
                    })
        else:
            # Single step
            steps.append({
                'action': primary_action,
                'description': request,
                'estimated_time': self._estimate_step_time(primary_action)
            })
        
        return steps
    
    def _identify_action(self, text: str) -> str:
        """Identify action from text fragment"""
        text_lower = text.lower()
        
        action_patterns = {
            'substitute': r'substitute|replace|swap',
            'analyze': r'analyze|analysis|examine',
            'validate': r'validate|verify|check',
            'presentation': r'presentation|slides|powerpoint',
            'visualize': r'visualize|render|display'
        }
        
        for action, pattern in action_patterns.items():
            if re.search(pattern, text_lower):
                return action
        
        return 'unknown'
    
    def _estimate_step_time(self, action: str) -> int:
        """Estimate time for workflow step in seconds"""
        time_estimates = {
            'substitute': 60,
            'analyze': 30,
            'validate': 45,
            'presentation': 20,
            'visualize': 15,
            'unknown': 10
        }
        
        return time_estimates.get(action, 10)
    
    def execute_workflow(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow based on parsed command
        
        Args:
            command: Parsed command structure
            
        Returns:
            Workflow execution results
        """
        console.print("🚀 [bold blue]Executing AI-Orchestrated Workflow[/bold blue]")
        
        # Display workflow plan
        self._display_workflow_plan(command)
        
        # Execute workflow steps
        results = {
            'command': command,
            'steps': [],
            'success': True,
            'total_time': 0,
            'start_time': time.time()
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                
                # Create progress tasks
                total_steps = len(command['workflow_steps'])
                main_task = progress.add_task("Overall Progress", total=total_steps)
                
                for i, step in enumerate(command['workflow_steps']):
                    step_task = progress.add_task(f"Step {i+1}: {step['action']}", total=100)
                    
                    step_result = self._execute_step(step, command, progress, step_task)
                    results['steps'].append(step_result)
                    
                    if not step_result['success']:
                        results['success'] = False
                        console.print(f"❌ Step {i+1} failed: {step_result.get('error', 'Unknown error')}")
                        break
                    
                    progress.update(main_task, advance=1)
                    progress.update(step_task, completed=100)
            
            results['end_time'] = time.time()
            results['total_time'] = results['end_time'] - results['start_time']
            
            # Display results
            self._display_workflow_results(results)
            
        except Exception as e:
            console.print(f"❌ [red]Workflow execution failed: {e}[/red]")
            results['success'] = False
            results['error'] = str(e)
        
        # Store in history
        self.workflow_history.append(results)
        
        return results
    
    def _display_workflow_plan(self, command: Dict[str, Any]):
        """Display workflow execution plan"""
        table = Table(title="🎯 Workflow Execution Plan")
        table.add_column("Step", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Est. Time", style="yellow")
        
        for i, step in enumerate(command['workflow_steps']):
            table.add_row(
                str(i + 1),
                step['action'],
                step['description'][:50] + "..." if len(step['description']) > 50 else step['description'],
                f"{step['estimated_time']}s"
            )
        
        console.print(table)
    
    def _execute_step(self, step: Dict[str, Any], command: Dict[str, Any], 
                     progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute individual workflow step"""
        step_result = {
            'step': step,
            'success': False,
            'start_time': time.time(),
            'output': None,
            'error': None
        }
        
        try:
            action = step['action']
            
            if action == 'substitute':
                step_result['output'] = self._execute_substitute_step(command, progress, task_id)
            elif action == 'analyze':
                step_result['output'] = self._execute_analyze_step(command, progress, task_id)
            elif action == 'validate':
                step_result['output'] = self._execute_validate_step(command, progress, task_id)
            elif action == 'presentation':
                step_result['output'] = self._execute_presentation_step(command, progress, task_id)
            elif action == 'visualize':
                step_result['output'] = self._execute_visualize_step(command, progress, task_id)
            else:
                step_result['error'] = f"Unknown action: {action}"
                
            step_result['success'] = step_result['output'] is not None
            
        except Exception as e:
            step_result['error'] = str(e)
            
        step_result['end_time'] = time.time()
        step_result['duration'] = step_result['end_time'] - step_result['start_time']
        
        return step_result
    
    def _execute_substitute_step(self, command: Dict[str, Any], 
                               progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute substitution step"""
        progress.update(task_id, advance=25, description="Preparing substitution...")
        
        # Extract parameters
        entities = command['entities']
        parameters = command['parameters']
        
        input_file = entities['files'][0] if entities['files'] else None
        if not input_file:
            raise ValueError("No input file specified")
        
        # Determine what to remove and add
        remove_species = "O2"  # Default, should be parsed better
        add_species = "O"      # Default, should be parsed better
        count = parameters.get('count', 100)
        density = parameters.get('density', 0.18)
        
        progress.update(task_id, advance=25, description="Running PACKMOL...")
        
        # Execute substitution
        packmol = self.tools['packmol']
        result = packmol.gas_substitution_workflow(
            input_structure=input_file,
            remove_species=remove_species,
            add_species=add_species,
            count=count,
            density=density,
            geometry={'gas_box': [23, 23, 23], 'final_box': [24, 140, 80]},
            visual_validation=parameters.get('visual_validation', True)
        )
        
        progress.update(task_id, advance=50, description="Substitution complete")
        
        return result
    
    def _execute_analyze_step(self, command: Dict[str, Any], 
                            progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute analysis step"""
        progress.update(task_id, advance=25, description="Preparing analysis...")
        
        # Use existing sophisticated analysis
        existing_tools = self.tools['existing_probaah']
        entities = command['entities']
        
        trajectory_file = entities['files'][0] if entities['files'] else None
        if not trajectory_file:
            raise ValueError("No trajectory file specified")
        
        progress.update(task_id, advance=25, description="Running trajectory analysis...")
        
        # Execute analysis
        result = existing_tools.analyze_trajectory(
            trajectory_file=trajectory_file,
            **command['parameters'].get('analysis_options', {})
        )
        
        progress.update(task_id, advance=50, description="Analysis complete")
        
        return result
    
    def _execute_validate_step(self, command: Dict[str, Any], 
                             progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute validation step"""
        progress.update(task_id, advance=25, description="Preparing validation...")
        
        viamd = self.tools['viamd']
        entities = command['entities']
        
        structure_file = entities['files'][0] if entities['files'] else None
        if not structure_file:
            raise ValueError("No structure file specified")
        
        progress.update(task_id, advance=25, description="Running validation...")
        
        # Execute validation
        result = viamd.validate_structure(
            structure_file=structure_file,
            interactive=command['parameters'].get('visual_validation', True)
        )
        
        progress.update(task_id, advance=50, description="Validation complete")
        
        return result
    
    def _execute_presentation_step(self, command: Dict[str, Any], 
                                 progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute presentation step"""
        progress.update(task_id, advance=25, description="Preparing presentation...")
        
        # Use existing sophisticated presentation tools
        existing_tools = self.tools['existing_probaah']
        
        progress.update(task_id, advance=25, description="Creating presentation...")
        
        # Execute presentation creation
        result = existing_tools.create_presentation(
            analysis_dir="analysis",
            title=command['parameters'].get('title', 'Research Results')
        )
        
        progress.update(task_id, advance=50, description="Presentation complete")
        
        return result
    
    def _execute_visualize_step(self, command: Dict[str, Any], 
                              progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute visualization step"""
        progress.update(task_id, advance=25, description="Preparing visualization...")
        
        # Basic visualization implementation
        # In production, this would use ASE or other visualization tools
        
        progress.update(task_id, advance=75, description="Visualization complete")
        
        return {"status": "Visualization step completed"}
    
    def _display_workflow_results(self, results: Dict[str, Any]):
        """Display workflow execution results"""
        console.print("\n📊 [bold]Workflow Results[/bold]")
        
        # Success/failure summary
        if results['success']:
            console.print("✅ [bold green]Workflow completed successfully![/bold green]")
        else:
            console.print("❌ [bold red]Workflow failed[/bold red]")
        
        # Time summary
        console.print(f"⏱️  Total time: {results['total_time']:.1f} seconds")
        
        # Step results
        for i, step_result in enumerate(results['steps']):
            status = "✅" if step_result['success'] else "❌"
            console.print(f"{status} Step {i+1}: {step_result['step']['action']} ({step_result['duration']:.1f}s)")
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """
        Process natural language request end-to-end
        
        Args:
            request: Natural language request
            
        Returns:
            Processing results
        """
        console.print(f"🎯 [bold]Processing Request:[/bold] {request}")
        
        # Parse request
        command = self.parse_natural_language_request(request)
        
        # Execute workflow
        results = self.execute_workflow(command)
        
        return results
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of all available tools"""
        status = {}
        
        for tool_name, tool in self.tools.items():
            if hasattr(tool, 'is_available'):
                status[tool_name] = {
                    'available': tool.is_available(),
                    'type': type(tool).__name__
                }
            else:
                status[tool_name] = {
                    'available': True,
                    'type': type(tool).__name__
                }
        
        return status
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        return self.workflow_history
    
    def cleanup(self):
        """Clean up resources"""
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                tool.cleanup()

# CLI helper functions
def process_natural_language_cli(request: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    CLI wrapper for natural language processing
    
    Args:
        request: Natural language request
        config_path: Path to configuration file
        
    Returns:
        Processing results
    """
    orchestrator = ProbaahAIOrchestrator(config_path)
    return orchestrator.process_request(request)