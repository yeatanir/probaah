# FILE: plugins/ai/visual_validation.py
"""
Modern Python wrapper around VIAMD visualization tool
Provides interactive and automated structure validation
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
import yaml

console = Console()

class VIAMDIntegration:
    """
    Modern Python wrapper around VIAMD visualization tool
    Handles interactive and automated structure validation
    """
    
    def __init__(self, viamd_path: Optional[str] = None):
        """
        Initialize VIAMD integration
        
        Args:
            viamd_path: Path to VIAMD executable (auto-detect if None)
        """
        self.viamd_path = self._setup_viamd(viamd_path)
        self.temp_dir = None
        self.validation_results = {}
        
    def _setup_viamd(self, viamd_path: Optional[str] = None) -> Optional[str]:
        """
        Setup VIAMD integration - find executable
        
        Args:
            viamd_path: Explicit path to VIAMD
            
        Returns:
            Path to VIAMD executable or None if not found
        """
        # Try explicit path first
        if viamd_path and Path(viamd_path).exists():
            return viamd_path
            
        # Common VIAMD locations
        common_paths = [
            "~/OneDrive - The Pennsylvania State University/Software/VIAMD/viamd",
            "~/Software/VIAMD/viamd",
            "~/Downloads/VIAMD/viamd",
            "/Applications/VIAMD/viamd",
            "/usr/local/bin/viamd",
            "viamd"  # In PATH
        ]
        
        for path in common_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return str(expanded_path)
                
        # Try to find in common directories
        search_dirs = [
            Path.home() / "OneDrive - The Pennsylvania State University" / "Software",
            Path.home() / "Software",
            Path.home() / "Downloads",
            Path("/Applications"),
            Path("/usr/local/bin")
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for viamd_candidate in search_dir.rglob("viamd*"):
                    if viamd_candidate.is_file() and os.access(viamd_candidate, os.X_OK):
                        return str(viamd_candidate)
        
        return None
    
    def is_available(self) -> bool:
        """Check if VIAMD is available"""
        return self.viamd_path is not None
    
    def get_info(self) -> Dict[str, Any]:
        """Get VIAMD information"""
        return {
            'available': self.is_available(),
            'path': self.viamd_path,
            'version': 'Unknown',  # VIAMD doesn't typically have version command
            'supports_batch': True,
            'supports_interactive': True
        }
    
    def _prepare_structure_for_viamd(self, structure_file: str) -> str:
        """
        Prepare structure file for VIAMD visualization
        
        Args:
            structure_file: Input structure file
            
        Returns:
            Path to VIAMD-compatible structure file
        """
        structure_path = Path(structure_file)
        
        if not structure_path.exists():
            raise FileNotFoundError(f"Structure file not found: {structure_file}")
            
        # Create temporary directory if needed
        if not self.temp_dir:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="probaah_viamd_"))
            
        # VIAMD typically works with XYZ, PDB, and other formats
        # Copy to temp directory for processing
        viamd_file = self.temp_dir / f"viamd_{structure_path.name}"
        shutil.copy2(structure_file, viamd_file)
        
        # Convert format if needed
        if structure_path.suffix.lower() in ['.bgf', '.car']:
            # Convert BGF/CAR to XYZ for VIAMD
            xyz_file = self.temp_dir / f"{structure_path.stem}.xyz"
            self._convert_to_xyz(str(viamd_file), str(xyz_file))
            return str(xyz_file)
        
        return str(viamd_file)
    
    def _convert_to_xyz(self, input_file: str, output_file: str):
        """
        Convert structure file to XYZ format
        
        Args:
            input_file: Input structure file
            output_file: Output XYZ file
        """
        # Basic conversion implementation
        # In production, this would use ASE or other molecular libraries
        try:
            # Try using ASE for conversion
            from ase.io import read, write
            atoms = read(input_file)
            write(output_file, atoms)
        except ImportError:
            # Fallback: basic BGF to XYZ conversion
            self._bgf_to_xyz_basic(input_file, output_file)
    
    def _bgf_to_xyz_basic(self, bgf_file: str, xyz_file: str):
        """Basic BGF to XYZ conversion"""
        atoms = []
        
        with open(bgf_file, 'r') as f:
            for line in f:
                if line.startswith('ATOM'):
                    parts = line.split()
                    if len(parts) >= 6:
                        element = parts[2]
                        x, y, z = parts[3:6]
                        atoms.append(f"{element} {x} {y} {z}")
        
        with open(xyz_file, 'w') as f:
            f.write(f"{len(atoms)}\n")
            f.write("Converted from BGF by Probaah\n")
            for atom in atoms:
                f.write(f"{atom}\n")
    
    def _generate_preview_images(self, structure_file: str) -> List[str]:
        """
        Generate preview images for quick assessment
        
        Args:
            structure_file: Structure file to preview
            
        Returns:
            List of preview image paths
        """
        preview_images = []
        
        try:
            # Try to generate preview using matplotlib/ASE
            from ase.io import read
            from ase.visualize.plot import plot_atoms
            import matplotlib.pyplot as plt
            
            atoms = read(structure_file)
            
            # Generate different views
            views = [
                ('front', (0, 0)),
                ('side', (90, 0)),
                ('top', (0, 90))
            ]
            
            for view_name, rotation in views:
                fig, ax = plt.subplots(figsize=(8, 6))
                plot_atoms(atoms, ax=ax, radii=0.5, rotation=f"{rotation[0]}x,{rotation[1]}y")
                ax.set_title(f"Structure Preview - {view_name.title()} View")
                
                preview_file = self.temp_dir / f"preview_{view_name}.png"
                plt.savefig(preview_file, dpi=150, bbox_inches='tight')
                plt.close()
                
                preview_images.append(str(preview_file))
                
        except ImportError:
            console.print("⚠️  Preview generation requires ASE and matplotlib")
        except Exception as e:
            console.print(f"⚠️  Could not generate preview: {e}")
            
        return preview_images
    
    def _interactive_validation(self, structure_file: str) -> Dict[str, Any]:
        """
        Run interactive validation with VIAMD
        
        Args:
            structure_file: Structure file to validate
            
        Returns:
            Validation results
        """
        console.print("🎯 [bold]Interactive Validation with VIAMD[/bold]")
        
        if not self.is_available():
            console.print("❌ VIAMD not found!")
            console.print("💡 Please install VIAMD or specify path in configuration")
            return {
                'approved': False,
                'method': 'interactive',
                'error': 'VIAMD not available',
                'feedback': 'Could not launch VIAMD'
            }
        
        try:
            # Launch VIAMD
            console.print(f"🚀 Launching VIAMD: {self.viamd_path}")
            console.print(f"📁 Structure file: {structure_file}")
            
            # Start VIAMD process
            process = subprocess.Popen(
                [self.viamd_path, structure_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            console.print("✅ VIAMD launched successfully")
            console.print("🔍 Please inspect the structure in VIAMD")
            console.print("📋 Look for:")
            console.print("   • Overlapping atoms")
            console.print("   • Unrealistic bond lengths")
            console.print("   • Proper molecular geometry")
            console.print("   • Reasonable density distribution")
            
            # Wait for user feedback
            time.sleep(2)  # Give VIAMD time to start
            
            # Get user feedback
            approved = Confirm.ask("📊 Does the structure look correct?")
            
            feedback = ""
            if not approved:
                feedback = Prompt.ask("💭 Please describe any issues you observed")
                
            recommendations = []
            if not approved:
                recommendations.extend([
                    "Consider adjusting PACKMOL tolerance",
                    "Check molecular geometry parameters",
                    "Verify density settings",
                    "Run energy minimization"
                ])
            
            # Try to close VIAMD gracefully
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
            
            return {
                'approved': approved,
                'method': 'interactive',
                'feedback': feedback,
                'recommendations': recommendations,
                'timestamp': time.time()
            }
            
        except Exception as e:
            console.print(f"❌ Interactive validation failed: {e}")
            return {
                'approved': False,
                'method': 'interactive',
                'error': str(e),
                'feedback': 'Interactive validation failed'
            }
    
    def _automated_validation(self, structure_file: str) -> Dict[str, Any]:
        """
        Run automated validation checks
        
        Args:
            structure_file: Structure file to validate
            
        Returns:
            Validation results
        """
        console.print("🤖 [bold]Automated Validation[/bold]")
        
        validation_results = {
            'approved': True,
            'method': 'automated',
            'checks': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Load structure for analysis
            from ase.io import read
            atoms = read(structure_file)
            
            # Check 1: Minimum distances
            min_distances = []
            positions = atoms.get_positions()
            
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    dist = ((positions[i] - positions[j]) ** 2).sum() ** 0.5
                    min_distances.append(dist)
            
            min_dist = min(min_distances) if min_distances else 0
            validation_results['checks']['min_distance'] = min_dist
            
            if min_dist < 0.5:  # Atoms too close
                validation_results['approved'] = False
                validation_results['issues'].append(f"Atoms too close: {min_dist:.2f} Å")
                validation_results['recommendations'].append("Increase PACKMOL tolerance")
            
            # Check 2: Reasonable density
            volume = atoms.get_volume() if hasattr(atoms, 'get_volume') else 1000
            density = len(atoms) / volume
            validation_results['checks']['density'] = density
            
            if density > 10:  # Very high density
                validation_results['issues'].append(f"High density: {density:.2f} atoms/Å³")
                validation_results['recommendations'].append("Check box dimensions")
            
            # Check 3: Structure completeness
            validation_results['checks']['atom_count'] = len(atoms)
            validation_results['checks']['volume'] = volume
            
            console.print(f"✅ Minimum distance: {min_dist:.2f} Å")
            console.print(f"✅ Atom count: {len(atoms)}")
            console.print(f"✅ Volume: {volume:.1f} Å³")
            
            if validation_results['approved']:
                console.print("✅ [green]Automated validation passed[/green]")
            else:
                console.print("⚠️  [yellow]Automated validation found issues[/yellow]")
                for issue in validation_results['issues']:
                    console.print(f"   • {issue}")
                    
        except ImportError:
            console.print("⚠️  Automated validation requires ASE")
            validation_results['approved'] = False
            validation_results['error'] = 'ASE not available'
            
        except Exception as e:
            console.print(f"❌ Automated validation failed: {e}")
            validation_results['approved'] = False
            validation_results['error'] = str(e)
            
        return validation_results
    
    def _save_validation_images(self, preview_images: List[str]) -> List[str]:
        """
        Save validation images to permanent location
        
        Args:
            preview_images: List of preview image paths
            
        Returns:
            List of saved image paths
        """
        saved_images = []
        
        # Create validation directory
        validation_dir = Path.cwd() / "validation_images"
        validation_dir.mkdir(exist_ok=True)
        
        for i, preview_image in enumerate(preview_images):
            if Path(preview_image).exists():
                saved_image = validation_dir / f"validation_{i+1}.png"
                shutil.copy2(preview_image, saved_image)
                saved_images.append(str(saved_image))
                
        return saved_images
    
    def validate_structure(self, structure_file: str, interactive: bool = True,
                         save_images: bool = False) -> Dict[str, Any]:
        """
        Complete structure validation workflow
        
        Args:
            structure_file: Structure file to validate
            interactive: Whether to run interactive validation
            save_images: Whether to save validation images
            
        Returns:
            Validation results
        """
        console.print("🔬 [bold blue]Structure Validation Workflow[/bold blue]")
        
        # Create temporary directory
        if not self.temp_dir:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="probaah_validation_"))
        
        try:
            # Step 1: Prepare structure
            console.print("📋 Step 1: Preparing structure for validation")
            viamd_compatible_file = self._prepare_structure_for_viamd(structure_file)
            
            # Step 2: Generate preview images
            console.print("🎨 Step 2: Generating preview images")
            preview_images = self._generate_preview_images(viamd_compatible_file)
            
            # Step 3: Run validation
            if interactive and self.is_available():
                console.print("🎯 Step 3: Interactive validation")
                validation_result = self._interactive_validation(viamd_compatible_file)
            else:
                console.print("🤖 Step 3: Automated validation")
                validation_result = self._automated_validation(viamd_compatible_file)
            
            # Step 4: Save results
            saved_images = []
            if save_images:
                console.print("💾 Step 4: Saving validation images")
                saved_images = self._save_validation_images(preview_images)
            
            # Compile final results
            final_results = {
                'structure_file': structure_file,
                'validation_result': validation_result,
                'preview_images': preview_images,
                'saved_images': saved_images,
                'temp_dir': str(self.temp_dir),
                'timestamp': time.time()
            }
            
            # Show summary
            if validation_result['approved']:
                console.print("✅ [bold green]Structure validation completed successfully![/bold green]")
            else:
                console.print("⚠️  [bold yellow]Structure validation completed with issues[/bold yellow]")
                if 'issues' in validation_result:
                    for issue in validation_result['issues']:
                        console.print(f"   • {issue}")
            
            return final_results
            
        except Exception as e:
            console.print(f"❌ [red]Validation workflow failed: {e}[/red]")
            return {
                'structure_file': structure_file,
                'validation_result': {
                    'approved': False,
                    'method': 'failed',
                    'error': str(e)
                },
                'preview_images': [],
                'saved_images': [],
                'temp_dir': str(self.temp_dir) if self.temp_dir else None
            }
    
    def batch_validate(self, structure_files: List[str], 
                      interactive: bool = False) -> Dict[str, Any]:
        """
        Batch validation of multiple structures
        
        Args:
            structure_files: List of structure files to validate
            interactive: Whether to run interactive validation
            
        Returns:
            Batch validation results
        """
        console.print(f"🔄 [bold blue]Batch Validation: {len(structure_files)} structures[/bold blue]")
        
        results = {}
        
        for i, structure_file in enumerate(structure_files):
            console.print(f"\n📁 [{i+1}/{len(structure_files)}] Validating: {structure_file}")
            
            result = self.validate_structure(
                structure_file=structure_file,
                interactive=interactive,
                save_images=False
            )
            
            results[structure_file] = result
            
        # Summary
        approved_count = sum(1 for r in results.values() 
                           if r['validation_result']['approved'])
        
        console.print(f"\n📊 [bold]Batch Validation Summary[/bold]")
        console.print(f"✅ Approved: {approved_count}/{len(structure_files)}")
        console.print(f"⚠️  Issues: {len(structure_files) - approved_count}/{len(structure_files)}")
        
        return {
            'total_structures': len(structure_files),
            'approved_count': approved_count,
            'results': results,
            'timestamp': time.time()
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()

# CLI helper functions
def validate_structure_cli(structure_file: str, interactive: bool = True,
                          save_images: bool = False) -> Dict[str, Any]:
    """
    CLI wrapper for structure validation
    
    Args:
        structure_file: Structure file to validate
        interactive: Whether to run interactive validation
        save_images: Whether to save validation images
        
    Returns:
        Validation results
    """
    viamd = VIAMDIntegration()
    return viamd.validate_structure(
        structure_file=structure_file,
        interactive=interactive,
        save_images=save_images
    )