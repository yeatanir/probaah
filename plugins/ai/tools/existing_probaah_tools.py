# FILE: plugins/ai/tools/existing_probaah_tools.py
"""
Wrapper for existing sophisticated Probaah functionality
Provides AI integration with existing enterprise-grade tools
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()

class ExistingProbaahTools:
    """
    Wrapper for existing sophisticated Probaah functionality
    Preserves all existing enterprise-grade analysis and presentation tools
    """
    
    def __init__(self):
        """Initialize existing tools integration"""
        self.setup_paths()
        self.available_tools = self._check_available_tools()
    
    def setup_paths(self):
        """Setup paths for existing plugins"""
        # Add plugins to Python path
        current_dir = Path(__file__).parent.parent.parent
        plugins_dir = current_dir / "plugins"
        
        if str(plugins_dir) not in sys.path:
            sys.path.append(str(plugins_dir))
    
    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which existing tools are available"""
        available = {}
        
        try:
            # Check trajectory analyzer
            from analysis.ase_tools.trajectory_analyzer import ProbaahTrajectoryAnalyzer
            available['trajectory_analyzer'] = True
        except ImportError:
            available['trajectory_analyzer'] = False
            
        try:
            # Check presentation generator
            from analysis.ase_tools.research_slides import ProbaahPresentationGenerator
            available['presentation_generator'] = True
        except ImportError:
            available['presentation_generator'] = False
            
        return available
    
    def analyze_trajectory(self, trajectory_file: str, output_dir: Optional[str] = None,
                         bonds: bool = True, rdf: bool = True, 
                         energy: bool = True, plots: bool = True) -> Dict[str, Any]:
        """
        Use existing enterprise-grade trajectory analysis
        
        Args:
            trajectory_file: Path to trajectory file
            output_dir: Output directory for results
            bonds: Whether to analyze bonds
            rdf: Whether to calculate RDF
            energy: Whether to analyze energy
            plots: Whether to generate plots
            
        Returns:
            Analysis results
        """
        if not self.available_tools.get('trajectory_analyzer', False):
            raise ImportError("Trajectory analyzer not available. Please install ASE and matplotlib.")
        
        try:
            from analysis.ase_tools.trajectory_analyzer import ProbaahTrajectoryAnalyzer
            
            console.print(f"🔬 [bold]Running enterprise-grade trajectory analysis[/bold]")
            console.print(f"📁 Input: {trajectory_file}")
            
            # Use existing sophisticated analyzer
            analyzer = ProbaahTrajectoryAnalyzer(trajectory_file, output_dir)
            
            # Run full analysis using existing methods
            results = {}
            
            if bonds:
                console.print("🔗 Analyzing bonds...")
                results['bonds'] = analyzer.analyze_bonds()
                
            if rdf:
                console.print("📊 Calculating RDF...")
                results['rdf'] = analyzer.calculate_rdf()
                
            if energy:
                console.print("⚡ Analyzing energy...")
                results['energy'] = analyzer.analyze_energy()
                
            if plots:
                console.print("📈 Generating plots...")
                results['plots'] = analyzer.create_plots()
            
            # Get summary statistics
            results['summary'] = analyzer.get_summary_stats()
            
            console.print("✅ [bold green]Analysis completed successfully![/bold green]")
            
            return results
            
        except Exception as e:
            console.print(f"❌ [red]Analysis failed: {e}[/red]")
            raise
    
    def create_presentation(self, analysis_dir: str, title: str = "Research Results",
                          output_file: Optional[str] = None, 
                          style: str = "weekly") -> str:
        """
        Use existing conference-ready presentation generation
        
        Args:
            analysis_dir: Directory containing analysis results
            title: Presentation title
            output_file: Output PowerPoint file
            style: Presentation style
            
        Returns:
            Path to created presentation
        """
        if not self.available_tools.get('presentation_generator', False):
            raise ImportError("Presentation generator not available. Please install python-pptx.")
        
        try:
            from analysis.ase_tools.research_slides import create_weekly_update_presentation
            
            console.print(f"🎨 [bold]Creating conference-ready presentation[/bold]")
            console.print(f"📊 Analysis data: {analysis_dir}")
            console.print(f"📋 Title: {title}")
            
            # Use existing sophisticated presentation generator
            if not output_file:
                output_file = f"{title.replace(' ', '_')}_presentation.pptx"
            
            result = create_weekly_update_presentation(
                analysis_dir=analysis_dir,
                output_file=output_file,
                title=title
            )
            
            console.print(f"✅ [bold green]Presentation created: {result}[/bold green]")
            
            return result
            
        except Exception as e:
            console.print(f"❌ [red]Presentation creation failed: {e}[/red]")
            raise
    
    def analyze_bonds_only(self, trajectory_file: str, cutoff: float = 1.2,
                          output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Quick bond analysis using existing tools
        
        Args:
            trajectory_file: Path to trajectory file
            cutoff: Bond cutoff factor
            output_file: Output plot file
            
        Returns:
            Bond analysis results
        """
        if not self.available_tools.get('trajectory_analyzer', False):
            raise ImportError("Trajectory analyzer not available.")
        
        try:
            from analysis.ase_tools.trajectory_analyzer import ProbaahTrajectoryAnalyzer
            
            console.print(f"🔗 [bold]Quick bond analysis[/bold]")
            
            analyzer = ProbaahTrajectoryAnalyzer(trajectory_file)
            results = analyzer.analyze_bonds(cutoff_factor=cutoff)
            
            if output_file:
                plots = analyzer.create_plots()
                console.print(f"📊 Plot saved: {output_file}")
            
            return results
            
        except Exception as e:
            console.print(f"❌ [red]Bond analysis failed: {e}[/red]")
            raise
    
    def create_weekly_update(self, project_dir: str = ".", 
                           title: Optional[str] = None) -> str:
        """
        Create weekly update presentation from current project
        
        Args:
            project_dir: Project directory
            title: Custom title
            
        Returns:
            Path to created presentation
        """
        try:
            from datetime import datetime
            
            console.print(f"📅 [bold]Creating weekly update presentation[/bold]")
            
            # Check if we're in a Probaah project
            config_file = Path(project_dir) / ".probaah-config.yaml"
            if not config_file.exists():
                console.print("❌ [red]Not in a Probaah project directory[/red]")
                raise ValueError("Not in a Probaah project directory")
            
            # Look for analysis directory
            analysis_dirs = [
                Path(project_dir) / "analysis",
                Path(project_dir) / "trajectories" / "processed",
                Path(project_dir)
            ]
            
            analysis_dir = None
            for d in analysis_dirs:
                if (d / "analysis_results.json").exists():
                    analysis_dir = str(d)
                    break
            
            if not analysis_dir:
                console.print("❌ [red]No analysis results found[/red]")
                raise ValueError("No analysis results found - run trajectory analysis first")
            
            # Generate presentation
            if not title:
                project_name = Path(project_dir).name
                title = f"{project_name} - Weekly Update"
            
            date_str = datetime.now().strftime("%Y%m%d")
            output_file = f"weekly_update_{date_str}.pptx"
            
            result = self.create_presentation(
                analysis_dir=analysis_dir,
                title=title,
                output_file=output_file
            )
            
            return result
            
        except Exception as e:
            console.print(f"❌ [red]Weekly update creation failed: {e}[/red]")
            raise
    
    def run_complete_workflow(self, trajectory_file: str, 
                            title: str = "Analysis Results") -> Dict[str, Any]:
        """
        Run complete analysis + presentation workflow
        
        Args:
            trajectory_file: Path to trajectory file
            title: Presentation title
            
        Returns:
            Complete workflow results
        """
        console.print("🚀 [bold blue]Running complete Probaah workflow[/bold blue]")
        
        workflow_results = {
            'analysis': None,
            'presentation': None,
            'success': False
        }
        
        try:
            # Step 1: Analysis
            console.print("\n📊 Step 1: Trajectory Analysis")
            analysis_results = self.analyze_trajectory(
                trajectory_file=trajectory_file,
                bonds=True,
                rdf=True, 
                energy=True,
                plots=True
            )
            workflow_results['analysis'] = analysis_results
            
            # Step 2: Presentation
            console.print("\n🎨 Step 2: Presentation Generation")
            analysis_dir = Path(trajectory_file).parent / "analysis"
            presentation_file = self.create_presentation(
                analysis_dir=str(analysis_dir),
                title=title
            )
            workflow_results['presentation'] = presentation_file
            
            workflow_results['success'] = True
            console.print(f"\n🎉 [bold green]Complete workflow finished![/bold green]")
            console.print(f"📁 Analysis: {analysis_dir}")
            console.print(f"📊 Presentation: {presentation_file}")
            
        except Exception as e:
            console.print(f"❌ [red]Workflow failed: {e}[/red]")
            workflow_results['error'] = str(e)
        
        return workflow_results
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of existing tools"""
        status = {
            'available_tools': self.available_tools,
            'trajectory_analyzer': {
                'available': self.available_tools.get('trajectory_analyzer', False),
                'features': ['bonds', 'rdf', 'energy', 'plots'],
                'enterprise_grade': True
            },
            'presentation_generator': {
                'available': self.available_tools.get('presentation_generator', False),
                'features': ['weekly_updates', 'conference_ready', 'automated'],
                'enterprise_grade': True
            }
        }
        
        return status
    
    def is_available(self) -> bool:
        """Check if any existing tools are available"""
        return any(self.available_tools.values())

# CLI helper functions
def analyze_trajectory_cli(trajectory_file: str, **kwargs) -> Dict[str, Any]:
    """CLI wrapper for trajectory analysis"""
    tools = ExistingProbaahTools()
    return tools.analyze_trajectory(trajectory_file, **kwargs)

def create_presentation_cli(analysis_dir: str, **kwargs) -> str:
    """CLI wrapper for presentation creation"""
    tools = ExistingProbaahTools()
    return tools.create_presentation(analysis_dir, **kwargs)

def complete_workflow_cli(trajectory_file: str, title: str = "Analysis Results") -> Dict[str, Any]:
    """CLI wrapper for complete workflow"""
    tools = ExistingProbaahTools()
    return tools.run_complete_workflow(trajectory_file, title)