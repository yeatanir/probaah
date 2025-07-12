# FILE: plugins/ai/workflows/gas_substitution.py
"""
Complete Gas Substitution Workflow
Orchestrates PACKMOL, VIAMD, and analysis tools for gas substitution
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

class GasSubstitutionWorkflow:
    """
    Complete workflow for gas substitution operations
    Integrates PACKMOL, VIAMD, and analysis tools
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize gas substitution workflow
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.workflow_results = {}
        self.temp_files = []
        
    def execute_complete_workflow(self, input_structure: str, remove_species: str,
                                add_species: str, count: int, density: float = 0.18,
                                geometry: Optional[Dict[str, Any]] = None,
                                visual_validation: bool = True,
                                run_analysis: bool = True,
                                create_presentation: bool = True,
                                output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute complete gas substitution workflow
        
        Args:
            input_structure: Input structure file
            remove_species: Species to remove
            add_species: Species to add
            count: Number of molecules to add
            density: Target density
            geometry: Geometry specification
            visual_validation: Whether to run visual validation
            run_analysis: Whether to run trajectory analysis
            create_presentation: Whether to create presentation
            output_dir: Output directory
            
        Returns:
            Complete workflow results
        """
        console.print("🚀 [bold blue]Complete Gas Substitution Workflow[/bold blue]")
        console.print(f"📁 Input: {input_structure}")
        console.print(f"🔄 {remove_species} → {add_species} ({count} molecules)")
        
        # Setup output directory
        if not output_dir:
            output_dir = Path(input_structure).parent / "gas_substitution_results"
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        workflow_results = {
            'input_structure': input_structure,
            'parameters': {
                'remove_species': remove_species,
                'add_species': add_species,
                'count': count,
                'density': density,
                'geometry': geometry
            },
            'steps': {},
            'output_directory': str(output_path),
            'success': False,
            'start_time': time.time()
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                
                # Step 1: Gas Substitution
                console.print("\n🧪 Step 1: Gas Substitution with PACKMOL")
                task1 = progress.add_task("Running PACKMOL...", total=100)
                
                substitution_result = self._execute_gas_substitution(
                    input_structure, remove_species, add_species, count, 
                    density, geometry, output_path, progress, task1
                )
                workflow_results['steps']['substitution'] = substitution_result
                
                if not substitution_result['success']:
                    raise RuntimeError("Gas substitution failed")
                
                progress.update(task1, completed=100)
                
                # Step 2: Visual Validation
                if visual_validation:
                    console.print("\n🔍 Step 2: Visual Validation with VIAMD")
                    task2 = progress.add_task("Running validation...", total=100)
                    
                    validation_result = self._execute_visual_validation(
                        substitution_result['output_structure'], 
                        output_path, progress, task2
                    )
                    workflow_results['steps']['validation'] = validation_result
                    
                    progress.update(task2, completed=100)
                
                # Step 3: Analysis
                if run_analysis:
                    console.print("\n📊 Step 3: Trajectory Analysis")
                    task3 = progress.add_task("Running analysis...", total=100)
                    
                    analysis_result = self._execute_analysis(
                        substitution_result['output_structure'],
                        output_path, progress, task3
                    )
                    workflow_results['steps']['analysis'] = analysis_result
                    
                    progress.update(task3, completed=100)
                
                # Step 4: Presentation
                if create_presentation:
                    console.print("\n🎨 Step 4: Presentation Creation")
                    task4 = progress.add_task("Creating presentation...", total=100)
                    
                    presentation_result = self._execute_presentation(
                        output_path, workflow_results, progress, task4
                    )
                    workflow_results['steps']['presentation'] = presentation_result
                    
                    progress.update(task4, completed=100)
            
            workflow_results['success'] = True
            workflow_results['end_time'] = time.time()
            workflow_results['total_time'] = workflow_results['end_time'] - workflow_results['start_time']
            
            # Display results
            self._display_workflow_summary(workflow_results)
            
        except Exception as e:
            console.print(f"❌ [red]Workflow failed: {e}[/red]")
            workflow_results['success'] = False
            workflow_results['error'] = str(e)
        
        return workflow_results
    
    def _execute_gas_substitution(self, input_structure: str, remove_species: str,
                                add_species: str, count: int, density: float,
                                geometry: Optional[Dict[str, Any]], output_path: Path,
                                progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute gas substitution step"""
        try:
            # Import PACKMOL wrapper
            import sys
            current_dir = Path(__file__).parent.parent
            if str(current_dir) not in sys.path:
                sys.path.append(str(current_dir))
            
            from packmol_wrapper import ProbaahPackmol
            
            progress.update(task_id, advance=25, description="Initializing PACKMOL...")
            
            # Setup geometry
            if not geometry:
                geometry = {
                    'gas_box': [23, 23, 23],
                    'final_box': [24, 140, 80]
                }
            
            progress.update(task_id, advance=25, description="Running substitution...")
            
            # Execute substitution
            packmol = ProbaahPackmol()
            result = packmol.gas_substitution_workflow(
                input_structure=input_structure,
                remove_species=remove_species,
                add_species=add_species,
                count=count,
                density=density,
                geometry=geometry,
                visual_validation=False,  # We'll do this separately
                output_file=str(output_path / "substituted_structure.xyz")
            )
            
            progress.update(task_id, advance=50, description="Substitution complete")
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'gas_substitution'
            }
    
    def _execute_visual_validation(self, structure_file: str, output_path: Path,
                                 progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute visual validation step"""
        try:
            # Import VIAMD wrapper
            import sys
            current_dir = Path(__file__).parent.parent
            if str(current_dir) not in sys.path:
                sys.path.append(str(current_dir))
            
            from visual_validation import VIAMDIntegration
            
            progress.update(task_id, advance=25, description="Initializing VIAMD...")
            
            # Execute validation
            viamd = VIAMDIntegration()
            result = viamd.validate_structure(
                structure_file=structure_file,
                interactive=False,  # Use automated validation in workflow
                save_images=True
            )
            
            progress.update(task_id, advance=75, description="Validation complete")
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'visual_validation'
            }
    
    def _execute_analysis(self, structure_file: str, output_path: Path,
                        progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute analysis step"""
        try:
            # Import existing analysis tools
            import sys
            current_dir = Path(__file__).parent.parent.parent
            plugins_dir = current_dir / "plugins"
            if str(plugins_dir) not in sys.path:
                sys.path.append(str(plugins_dir))
            
            from analysis.ase_tools.trajectory_analyzer import ProbaahTrajectoryAnalyzer
            
            progress.update(task_id, advance=25, description="Initializing analysis...")
            
            # Execute analysis
            analyzer = ProbaahTrajectoryAnalyzer(structure_file, str(output_path / "analysis"))
            
            progress.update(task_id, advance=50, description="Running analysis...")
            
            result = analyzer.full_analysis()
            
            progress.update(task_id, advance=75, description="Analysis complete")
            
            return {
                'success': True,
                'results': result,
                'step': 'analysis'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'analysis'
            }
    
    def _execute_presentation(self, output_path: Path, workflow_results: Dict[str, Any],
                            progress: Progress, task_id: Any) -> Dict[str, Any]:
        """Execute presentation creation step"""
        try:
            # Import existing presentation tools
            import sys
            current_dir = Path(__file__).parent.parent.parent
            plugins_dir = current_dir / "plugins"
            if str(plugins_dir) not in sys.path:
                sys.path.append(str(plugins_dir))
            
            from analysis.ase_tools.research_slides import create_weekly_update_presentation
            
            progress.update(task_id, advance=25, description="Preparing presentation...")
            
            # Create presentation
            title = f"Gas Substitution Results - {workflow_results['parameters']['remove_species']} to {workflow_results['parameters']['add_species']}"
            output_file = str(output_path / "gas_substitution_presentation.pptx")
            
            progress.update(task_id, advance=50, description="Creating slides...")
            
            result = create_weekly_update_presentation(
                analysis_dir=str(output_path / "analysis"),
                output_file=output_file,
                title=title
            )
            
            progress.update(task_id, advance=75, description="Presentation complete")
            
            return {
                'success': True,
                'presentation_file': result,
                'step': 'presentation'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': 'presentation'
            }
    
    def _display_workflow_summary(self, workflow_results: Dict[str, Any]):
        """Display workflow summary"""
        console.print("\n📊 [bold]Gas Substitution Workflow Summary[/bold]")
        
        if workflow_results['success']:
            console.print("✅ [bold green]Workflow completed successfully![/bold green]")
        else:
            console.print("❌ [bold red]Workflow failed[/bold red]")
            if 'error' in workflow_results:
                console.print(f"Error: {workflow_results['error']}")
        
        console.print(f"⏱️  Total time: {workflow_results.get('total_time', 0):.1f} seconds")
        console.print(f"📁 Output directory: {workflow_results['output_directory']}")
        
        # Step summary
        console.print("\n📋 [bold]Step Results:[/bold]")
        for step_name, step_result in workflow_results['steps'].items():
            if isinstance(step_result, dict):
                status = "✅" if step_result.get('success', False) else "❌"
                console.print(f"{status} {step_name.title()}")
                if not step_result.get('success', False) and 'error' in step_result:
                    console.print(f"   Error: {step_result['error']}")
        
        # Files created
        console.print("\n📁 [bold]Files Created:[/bold]")
        output_path = Path(workflow_results['output_directory'])
        if output_path.exists():
            for file in output_path.iterdir():
                if file.is_file():
                    console.print(f"   • {file.name}")
    
    def quick_substitution(self, input_structure: str, remove_species: str,
                         add_species: str, count: int) -> Dict[str, Any]:
        """
        Quick gas substitution with minimal validation
        
        Args:
            input_structure: Input structure file
            remove_species: Species to remove
            add_species: Species to add
            count: Number of molecules to add
            
        Returns:
            Quick substitution results
        """
        console.print("⚡ [bold blue]Quick Gas Substitution[/bold blue]")
        
        return self.execute_complete_workflow(
            input_structure=input_structure,
            remove_species=remove_species,
            add_species=add_species,
            count=count,
            visual_validation=False,
            run_analysis=False,
            create_presentation=False
        )
    
    def batch_substitution(self, input_structures: List[str], 
                         substitution_params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch gas substitution for multiple structures
        
        Args:
            input_structures: List of input structure files
            substitution_params: List of substitution parameters
            
        Returns:
            Batch substitution results
        """
        console.print(f"🔄 [bold blue]Batch Gas Substitution: {len(input_structures)} structures[/bold blue]")
        
        batch_results = {
            'total_structures': len(input_structures),
            'completed': 0,
            'failed': 0,
            'results': {}
        }
        
        for i, (structure, params) in enumerate(zip(input_structures, substitution_params)):
            console.print(f"\n[{i+1}/{len(input_structures)}] Processing: {structure}")
            
            try:
                result = self.execute_complete_workflow(
                    input_structure=structure,
                    **params
                )
                
                batch_results['results'][structure] = result
                
                if result['success']:
                    batch_results['completed'] += 1
                else:
                    batch_results['failed'] += 1
                    
            except Exception as e:
                console.print(f"❌ Failed to process {structure}: {e}")
                batch_results['failed'] += 1
                batch_results['results'][structure] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Summary
        console.print(f"\n📊 [bold]Batch Results:[/bold]")
        console.print(f"✅ Completed: {batch_results['completed']}")
        console.print(f"❌ Failed: {batch_results['failed']}")
        
        return batch_results

# CLI helper functions
def gas_substitution_workflow_cli(input_structure: str, remove_species: str,
                                add_species: str, count: int,
                                **kwargs) -> Dict[str, Any]:
    """
    CLI wrapper for gas substitution workflow
    
    Args:
        input_structure: Input structure file
        remove_species: Species to remove
        add_species: Species to add
        count: Number of molecules to add
        **kwargs: Additional workflow parameters
        
    Returns:
        Workflow results
    """
    workflow = GasSubstitutionWorkflow()
    return workflow.execute_complete_workflow(
        input_structure=input_structure,
        remove_species=remove_species,
        add_species=add_species,
        count=count,
        **kwargs
    )

def quick_substitution_cli(input_structure: str, remove_species: str,
                         add_species: str, count: int) -> Dict[str, Any]:
    """
    CLI wrapper for quick gas substitution
    
    Args:
        input_structure: Input structure file
        remove_species: Species to remove
        add_species: Species to add
        count: Number of molecules to add
        
    Returns:
        Quick substitution results
    """
    workflow = GasSubstitutionWorkflow()
    return workflow.quick_substitution(
        input_structure=input_structure,
        remove_species=remove_species,
        add_species=add_species,
        count=count
    )