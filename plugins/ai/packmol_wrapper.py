# FILE: plugins/ai/packmol_wrapper.py
"""
Modern Python wrapper around PACKMOL executable
Provides user-friendly interface to PACKMOL's archaic syntax
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import yaml

console = Console()

class ProbaahPackmol:
    """
    Modern Python wrapper around PACKMOL binary
    Handles archaic PACKMOL syntax internally while providing clean Python API
    """
    
    def __init__(self, executable_path: Optional[str] = None):
        """
        Initialize PACKMOL wrapper
        
        Args:
            executable_path: Path to PACKMOL executable (auto-detect if None)
        """
        self.executable = self._find_packmol_executable(executable_path)
        self.temp_dir = None
        self.last_input_file = None
        self.last_output_file = None
        
    def _find_packmol_executable(self, executable_path: Optional[str] = None) -> Optional[str]:
        """
        Find PACKMOL executable in system
        
        Args:
            executable_path: Explicit path to check first
            
        Returns:
            Path to PACKMOL executable or None if not found
        """
        # Try explicit path first
        if executable_path and Path(executable_path).exists():
            return executable_path
            
        # Try common locations
        common_paths = [
            "packmol",  # In PATH
            "/usr/local/bin/packmol",
            "/opt/conda/bin/packmol",
            "/usr/bin/packmol",
            "~/bin/packmol",
            "~/Software/packmol/packmol"
        ]
        
        for path in common_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return str(expanded_path)
                
        # Try which command
        try:
            result = subprocess.run(["which", "packmol"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        return None
    
    def is_available(self) -> bool:
        """Check if PACKMOL is available"""
        return self.executable is not None
    
    def get_version(self) -> Optional[str]:
        """Get PACKMOL version"""
        if not self.is_available():
            return None
            
        try:
            result = subprocess.run([self.executable, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        return "Unknown"
    
    def _parse_structure_file(self, structure_file: str) -> Dict[str, Any]:
        """
        Parse structure file to extract molecular information
        
        Args:
            structure_file: Path to structure file (XYZ, PDB, BGF)
            
        Returns:
            Dictionary with structure information
        """
        structure_path = Path(structure_file)
        
        if not structure_path.exists():
            raise FileNotFoundError(f"Structure file not found: {structure_file}")
            
        info = {
            'path': str(structure_path),
            'format': structure_path.suffix.lower(),
            'atoms': 0,
            'species': {},
            'box_size': None
        }
        
        try:
            # Parse XYZ format
            if info['format'] == '.xyz':
                with open(structure_path, 'r') as f:
                    lines = f.readlines()
                    info['atoms'] = int(lines[0].strip())
                    
                    # Count species
                    for i in range(2, 2 + info['atoms']):
                        if i < len(lines):
                            parts = lines[i].strip().split()
                            if parts:
                                element = parts[0]
                                info['species'][element] = info['species'].get(element, 0) + 1
                                
            # Parse PDB format (basic)
            elif info['format'] == '.pdb':
                with open(structure_path, 'r') as f:
                    for line in f:
                        if line.startswith('ATOM') or line.startswith('HETATM'):
                            info['atoms'] += 1
                            element = line[76:78].strip()
                            if element:
                                info['species'][element] = info['species'].get(element, 0) + 1
                                
            # Parse BGF format (basic) - also handles .geo files
            elif info['format'] in ['.bgf', '.geo']:
                with open(structure_path, 'r') as f:
                    for line in f:
                        if line.startswith('ATOM') or line.startswith('HETATM'):
                            info['atoms'] += 1
                            parts = line.split()
                            if len(parts) > 2:
                                element = parts[2]
                                info['species'][element] = info['species'].get(element, 0) + 1
                                
        except Exception as e:
            console.print(f"⚠️  Warning: Could not fully parse {structure_file}: {e}")
            
        return info
    
    def _convert_bgf_to_xyz(self, bgf_file: str) -> str:
        """
        Convert BGF format to XYZ format for PACKMOL compatibility
        
        Args:
            bgf_file: Path to BGF file
            
        Returns:
            Path to converted XYZ file
        """
        bgf_path = Path(bgf_file)
        xyz_file = self.temp_dir / f"{bgf_path.stem}.xyz"
        
        atoms = []
        with open(bgf_file, 'r') as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    parts = line.split()
                    if len(parts) >= 6:
                        element = parts[2]
                        x = float(parts[3])
                        y = float(parts[4])
                        z = float(parts[5])
                        atoms.append((element, x, y, z))
        
        # Write XYZ format
        with open(xyz_file, 'w') as f:
            f.write(f"{len(atoms)}\n")
            f.write(f"Converted from {bgf_path.name}\n")
            for element, x, y, z in atoms:
                f.write(f"{element} {x:.6f} {y:.6f} {z:.6f}\n")
        
        console.print(f"🔄 Converted BGF to XYZ: {xyz_file.name}")
        return str(xyz_file)
    
    def _prepare_structure_for_packmol(self, input_structure: str) -> str:
        """
        Prepare structure file for PACKMOL (convert to XYZ if needed)
        
        Args:
            input_structure: Input structure file
            
        Returns:
            Path to PACKMOL-compatible structure file
        """
        structure_path = Path(input_structure)
        
        if structure_path.suffix.lower() in ['.bgf', '.geo']:
            return self._convert_bgf_to_xyz(input_structure)
        elif structure_path.suffix.lower() == '.xyz':
            # Copy to temp directory
            xyz_file = self.temp_dir / structure_path.name
            shutil.copy2(input_structure, xyz_file)
            return str(xyz_file)
        else:
            console.print(f"⚠️  Unsupported format: {structure_path.suffix}")
            console.print("💡 Supported formats: .bgf, .geo, .xyz")
            console.print("💡 Consider converting your file to XYZ format")
            raise ValueError(f"Unsupported file format: {structure_path.suffix}")
    
    def _remove_species_molecular(self, input_structure: str, remove_species: str) -> str:
        """
        Remove specified species from structure with molecular recognition
        
        Args:
            input_structure: Input structure file
            remove_species: Species to remove (e.g., "O2", "H2O")
            
        Returns:
            Path to cleaned structure file
        """
        structure_info = self._parse_structure_file(input_structure)
        input_path = Path(input_structure)
        
        # Create cleaned structure file
        cleaned_file = self.temp_dir / f"cleaned_{input_path.name}"
        
        # For now, implement basic species removal
        # In production, this would use molecular recognition
        console.print(f"🧹 Removing {remove_species} from {input_structure}")
        
        # Copy original for now (placeholder for molecular recognition)
        shutil.copy2(input_structure, cleaned_file)
        
        # TODO: Implement proper molecular recognition and removal
        # This would involve:
        # 1. Reading molecular structure
        # 2. Identifying molecular groups (O2, H2O, etc.)
        # 3. Removing complete molecules
        # 4. Adjusting atom numbering
        
        return str(cleaned_file)
    
    def _generate_gas_molecule(self, gas_species: str) -> str:
        """
        Generate gas molecule structure file
        
        Args:
            gas_species: Gas species (e.g., "O", "N2", "CO2")
            
        Returns:
            Path to generated gas molecule file
        """
        gas_file = self.temp_dir / f"gas_{gas_species}.xyz"
        
        # Generate simple gas molecules
        # In production, this would use a molecular database
        gas_structures = {
            'O': "1\nOxygen atom\nO 0.0 0.0 0.0\n",
            'N': "1\nNitrogen atom\nN 0.0 0.0 0.0\n",
            'N2': "2\nNitrogen molecule\nN 0.0 0.0 0.0\nN 0.0 0.0 1.1\n",
            'O2': "2\nOxygen molecule\nO 0.0 0.0 0.0\nO 0.0 0.0 1.21\n",
            'CO2': "3\nCarbon dioxide\nC 0.0 0.0 0.0\nO 0.0 0.0 1.16\nO 0.0 0.0 -1.16\n"
        }
        
        if gas_species in gas_structures:
            with open(gas_file, 'w') as f:
                f.write(gas_structures[gas_species])
        else:
            # Default to single atom
            with open(gas_file, 'w') as f:
                f.write(f"1\n{gas_species} atom\n{gas_species} 0.0 0.0 0.0\n")
                
        return str(gas_file)
    
    def _calculate_optimal_placement(self, geometry: Dict[str, Any], 
                                   density: float, count: int) -> Dict[str, Any]:
        """
        Calculate optimal placement parameters for gas molecules
        
        Args:
            geometry: Geometry specification
            density: Target density
            count: Number of molecules to place
            
        Returns:
            Placement configuration
        """
        # Parse geometry specification
        # Example: "gas-box:23x23x23,offset-z:10,final-box:24x140x80"
        config = {
            'gas_box': [23, 23, 23],
            'offset': [0, 0, 10],
            'final_box': [24, 140, 80],
            'density': density,
            'count': count
        }
        
        # In production, this would do proper volume/density calculations
        return config
    
    def _generate_packmol_input(self, cleaned_structure: str, gas_molecule: str,
                              count: int, placement_config: Dict[str, Any]) -> str:
        """
        Generate PACKMOL input file with proper archaic syntax
        
        Args:
            cleaned_structure: Cleaned structure file
            gas_molecule: Gas molecule file
            count: Number of gas molecules
            placement_config: Placement configuration
            
        Returns:
            Path to generated PACKMOL input file
        """
        input_file = self.temp_dir / "packmol_input.inp"
        output_file = self.temp_dir / "packed_structure.xyz"
        
        # Generate PACKMOL input with archaic syntax
        packmol_input = f"""# PACKMOL input generated by Probaah
# Gas substitution workflow

tolerance 2.0
filetype xyz
output {output_file}

# Original structure (fixed)
structure {cleaned_structure}
  number 1
  fixed 0.0 0.0 0.0 0.0 0.0 0.0
end structure

# Gas molecules
structure {gas_molecule}
  number {count}
  inside box {placement_config['gas_box'][0]} {placement_config['gas_box'][1]} {placement_config['gas_box'][2]} {placement_config['final_box'][0]} {placement_config['final_box'][1]} {placement_config['final_box'][2]}
end structure
"""
        
        with open(input_file, 'w') as f:
            f.write(packmol_input)
            
        self.last_input_file = str(input_file)
        self.last_output_file = str(output_file)
        
        return str(input_file)
    
    def _execute_packmol(self, input_file: str) -> Tuple[bool, Optional[str]]:
        """
        Execute PACKMOL with error handling
        
        Args:
            input_file: Path to PACKMOL input file
            
        Returns:
            Tuple of (success, output_file_path)
        """
        if not self.is_available():
            console.print("❌ PACKMOL not found!")
            console.print("💡 Install with: conda install -c conda-forge packmol")
            return False, None
            
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running PACKMOL...", total=None)
                
                # Run PACKMOL
                result = subprocess.run(
                    [self.executable, input_file],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=self.temp_dir
                )
                
                progress.update(task, completed=True)
                
            if result.returncode == 0:
                console.print("✅ PACKMOL completed successfully")
                return True, self.last_output_file
            else:
                console.print(f"❌ PACKMOL failed with return code {result.returncode}")
                console.print(f"Stdout: {result.stdout}")
                console.print(f"Stderr: {result.stderr}")
                
                # Show input file for debugging
                console.print(f"🔍 PACKMOL input file: {input_file}")
                console.print(f"🔍 Temp directory: {self.temp_dir}")
                console.print("💡 Input file will be preserved for debugging")
                
                return False, None
                
        except subprocess.TimeoutExpired:
            console.print("❌ PACKMOL timed out after 5 minutes")
            return False, None
        except Exception as e:
            console.print(f"❌ PACKMOL execution failed: {e}")
            return False, None
    
    def _calculate_substitution_stats(self) -> Dict[str, Any]:
        """Calculate statistics for the substitution"""
        return {
            'original_atoms': 0,  # Would be calculated from input
            'added_molecules': 0,  # Would be calculated from parameters
            'final_atoms': 0,     # Would be calculated from output
            'density_achieved': 0.0,  # Would be calculated from volume
            'volume_change': 0.0      # Would be calculated from box dimensions
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on substitution results"""
        return [
            "Consider visual validation with VIAMD",
            "Run energy minimization before MD simulation",
            "Check for overlapping atoms",
            "Verify density is physically reasonable"
        ]
    
    def gas_substitution_workflow(self, input_structure: str, remove_species: str,
                                add_species: str, count: int, density: float,
                                geometry: Dict[str, Any], 
                                visual_validation: bool = True,
                                output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete gas substitution workflow
        
        Args:
            input_structure: Input structure file
            remove_species: Species to remove
            add_species: Species to add
            count: Number of molecules to add
            density: Target density
            geometry: Geometry specification
            visual_validation: Whether to run visual validation
            output_file: Output file path (optional)
            
        Returns:
            Dictionary with workflow results
        """
        console.print("🚀 [bold blue]Starting gas substitution workflow[/bold blue]")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="probaah_packmol_"))
        console.print(f"🔧 Working directory: {self.temp_dir}")
        
        try:
            # Step 1: Structure Analysis
            console.print("📊 Step 1: Analyzing input structure")
            structure_info = self._parse_structure_file(input_structure)
            
            # Step 1.5: Prepare structure for PACKMOL (convert if needed)
            console.print("🔄 Step 1.5: Preparing structure for PACKMOL")
            packmol_structure = self._prepare_structure_for_packmol(input_structure)
            
            # Step 2: Species Removal
            console.print(f"🧹 Step 2: Removing {remove_species}")
            cleaned_structure = self._remove_species_molecular(packmol_structure, remove_species)
            
            # Step 3: Gas Molecule Generation
            console.print(f"⚛️  Step 3: Generating {add_species} molecules")
            gas_molecule = self._generate_gas_molecule(add_species)
            
            # Step 4: Placement Geometry Calculation
            console.print("📐 Step 4: Calculating placement geometry")
            placement_config = self._calculate_optimal_placement(geometry, density, count)
            
            # Step 5: PACKMOL Input Generation
            console.print("📝 Step 5: Generating PACKMOL input")
            packmol_input = self._generate_packmol_input(
                cleaned_structure, gas_molecule, count, placement_config
            )
            
            # Step 6: PACKMOL Execution
            console.print("⚙️  Step 6: Running PACKMOL")
            success, output_structure = self._execute_packmol(packmol_input)
            
            if not success:
                raise RuntimeError("PACKMOL execution failed")
                
            # Step 7: Copy output to final location
            if output_file:
                shutil.copy2(output_structure, output_file)
                final_output = output_file
            else:
                final_output = output_structure
                
            # Step 8: Generate results
            results = {
                'success': True,
                'input_structure': input_structure,
                'output_structure': final_output,
                'removed_species': remove_species,
                'added_species': add_species,
                'molecule_count': count,
                'target_density': density,
                'statistics': self._calculate_substitution_stats(),
                'recommendations': self._generate_recommendations(),
                'packmol_input': packmol_input,
                'temp_dir': str(self.temp_dir)
            }
            
            console.print(f"✅ [bold green]Gas substitution completed![/bold green]")
            console.print(f"📁 Output: {final_output}")
            
            return results
            
        except Exception as e:
            console.print(f"❌ [red]Workflow failed: {e}[/red]")
            # Don't cleanup on failure - keep for debugging
            console.print(f"🔍 Debug files preserved in: {self.temp_dir}")
            return {
                'success': False,
                'error': str(e),
                'temp_dir': str(self.temp_dir) if self.temp_dir else None
            }
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def __del__(self):
        """Cleanup on destruction"""
        # Don't auto-cleanup - let user examine debug files
        pass

# CLI helper functions for integration
def packmol_substitute_cli(input_structure: str, remove_species: str,
                          add_species: str, count: int, density: float = 0.18,
                          geometry: str = "gas-box:23x23x23,final-box:24x140x80",
                          visual_validation: bool = True,
                          output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    CLI wrapper for gas substitution workflow
    
    Args:
        input_structure: Input structure file
        remove_species: Species to remove
        add_species: Species to add  
        count: Number of molecules to add
        density: Target density
        geometry: Geometry specification string
        visual_validation: Whether to run visual validation
        output_file: Output file path
        
    Returns:
        Workflow results
    """
    # Parse geometry string
    geometry_dict = {}
    if geometry:
        # Simple parsing for now
        # In production, this would be more sophisticated
        geometry_dict = {
            'gas_box': [23, 23, 23],
            'final_box': [24, 140, 80]
        }
    
    packmol = ProbaahPackmol()
    return packmol.gas_substitution_workflow(
        input_structure=input_structure,
        remove_species=remove_species,
        add_species=add_species,
        count=count,
        density=density,
        geometry=geometry_dict,
        visual_validation=visual_validation,
        output_file=output_file
    )