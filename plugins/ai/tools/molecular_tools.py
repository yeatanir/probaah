# FILE: plugins/ai/tools/molecular_tools.py
"""
Molecular tools integration for Probaah AI
Provides unified interface to molecular computation tools
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console

console = Console()

class MolecularTools:
    """
    Unified interface to molecular computation tools
    Provides abstractions for common molecular operations
    """
    
    def __init__(self):
        """Initialize molecular tools"""
        self.available_tools = self._check_available_tools()
    
    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which molecular tools are available"""
        available = {}
        
        # Check ASE
        try:
            import ase
            available['ase'] = True
        except ImportError:
            available['ase'] = False
        
        # Check RDKit
        try:
            import rdkit
            available['rdkit'] = True
        except ImportError:
            available['rdkit'] = False
        
        # Check OpenEye
        try:
            import openeye
            available['openeye'] = True
        except ImportError:
            available['openeye'] = False
        
        # Check external tools
        available['packmol'] = self._check_executable('packmol')
        available['vmd'] = self._check_executable('vmd')
        available['gaussian'] = self._check_executable('g16') or self._check_executable('g09')
        available['jaguar'] = self._check_executable('jaguar')
        
        return available
    
    def _check_executable(self, executable: str) -> bool:
        """Check if executable is available in PATH"""
        try:
            subprocess.run([executable, '--help'], 
                         capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def read_structure(self, structure_file: str) -> Dict[str, Any]:
        """
        Read molecular structure from file
        
        Args:
            structure_file: Path to structure file
            
        Returns:
            Structure information
        """
        structure_path = Path(structure_file)
        
        if not structure_path.exists():
            raise FileNotFoundError(f"Structure file not found: {structure_file}")
        
        structure_info = {
            'path': str(structure_path),
            'format': structure_path.suffix.lower(),
            'atoms': 0,
            'species': {},
            'coordinates': [],
            'bonds': []
        }
        
        if self.available_tools.get('ase', False):
            try:
                from ase.io import read
                atoms = read(structure_file)
                
                structure_info['atoms'] = len(atoms)
                structure_info['coordinates'] = atoms.get_positions().tolist()
                
                # Count species
                for symbol in atoms.get_chemical_symbols():
                    structure_info['species'][symbol] = structure_info['species'].get(symbol, 0) + 1
                
                return structure_info
            except Exception as e:
                console.print(f"⚠️  ASE read failed: {e}")
        
        # Fallback to basic parsing
        return self._parse_structure_basic(structure_file)
    
    def _parse_structure_basic(self, structure_file: str) -> Dict[str, Any]:
        """Basic structure parsing for common formats"""
        structure_path = Path(structure_file)
        
        structure_info = {
            'path': str(structure_path),
            'format': structure_path.suffix.lower(),
            'atoms': 0,
            'species': {},
            'coordinates': []
        }
        
        try:
            if structure_info['format'] == '.xyz':
                with open(structure_path, 'r') as f:
                    lines = f.readlines()
                    structure_info['atoms'] = int(lines[0].strip())
                    
                    for i in range(2, 2 + structure_info['atoms']):
                        if i < len(lines):
                            parts = lines[i].strip().split()
                            if len(parts) >= 4:
                                element = parts[0]
                                coords = [float(x) for x in parts[1:4]]
                                structure_info['coordinates'].append(coords)
                                structure_info['species'][element] = structure_info['species'].get(element, 0) + 1
                                
        except Exception as e:
            console.print(f"⚠️  Basic parsing failed: {e}")
        
        return structure_info
    
    def write_structure(self, structure_info: Dict[str, Any], 
                       output_file: str, format: Optional[str] = None) -> bool:
        """
        Write molecular structure to file
        
        Args:
            structure_info: Structure information
            output_file: Output file path
            format: Output format (inferred from extension if None)
            
        Returns:
            Success status
        """
        output_path = Path(output_file)
        
        if not format:
            format = output_path.suffix.lower()
        
        try:
            if self.available_tools.get('ase', False):
                from ase import Atoms
                from ase.io import write
                
                # Create ASE atoms object
                symbols = []
                positions = []
                
                for element, count in structure_info['species'].items():
                    symbols.extend([element] * count)
                
                if 'coordinates' in structure_info:
                    positions = structure_info['coordinates']
                
                atoms = Atoms(symbols=symbols, positions=positions)
                write(output_file, atoms)
                
                return True
            else:
                # Basic XYZ writing
                if format == '.xyz':
                    return self._write_xyz_basic(structure_info, output_file)
                    
        except Exception as e:
            console.print(f"❌ Structure write failed: {e}")
            
        return False
    
    def _write_xyz_basic(self, structure_info: Dict[str, Any], output_file: str) -> bool:
        """Basic XYZ file writing"""
        try:
            with open(output_file, 'w') as f:
                f.write(f"{structure_info['atoms']}\n")
                f.write("Generated by Probaah\n")
                
                for i, coords in enumerate(structure_info['coordinates']):
                    # Need to map coordinates to elements
                    element = "C"  # Placeholder
                    f.write(f"{element} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}\n")
                    
            return True
        except Exception as e:
            console.print(f"❌ XYZ write failed: {e}")
            return False
    
    def calculate_molecular_properties(self, structure_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate molecular properties
        
        Args:
            structure_info: Structure information
            
        Returns:
            Molecular properties
        """
        properties = {
            'molecular_weight': 0.0,
            'formula': '',
            'atom_count': structure_info['atoms'],
            'species_count': len(structure_info['species']),
            'center_of_mass': [0.0, 0.0, 0.0],
            'bonds': []
        }
        
        try:
            if self.available_tools.get('ase', False):
                from ase.data import atomic_masses, atomic_numbers
                
                # Calculate molecular weight
                total_mass = 0.0
                for element, count in structure_info['species'].items():
                    if element in atomic_numbers:
                        mass = atomic_masses[atomic_numbers[element]]
                        total_mass += mass * count
                
                properties['molecular_weight'] = total_mass
                
                # Generate molecular formula
                formula_parts = []
                for element, count in sorted(structure_info['species'].items()):
                    if count == 1:
                        formula_parts.append(element)
                    else:
                        formula_parts.append(f"{element}{count}")
                
                properties['formula'] = ''.join(formula_parts)
                
        except Exception as e:
            console.print(f"⚠️  Property calculation failed: {e}")
        
        return properties
    
    def identify_molecules(self, structure_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify individual molecules in structure
        
        Args:
            structure_info: Structure information
            
        Returns:
            List of identified molecules
        """
        molecules = []
        
        try:
            if self.available_tools.get('ase', False):
                # Use ASE for molecule identification
                molecules = self._identify_molecules_ase(structure_info)
            else:
                # Basic molecule identification
                molecules = self._identify_molecules_basic(structure_info)
                
        except Exception as e:
            console.print(f"⚠️  Molecule identification failed: {e}")
        
        return molecules
    
    def _identify_molecules_ase(self, structure_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify molecules using ASE"""
        molecules = []
        
        # This would use ASE's connectivity analysis
        # For now, return basic molecule info
        for element, count in structure_info['species'].items():
            if element in ['O', 'N', 'C']:
                if count >= 2:
                    molecules.append({
                        'formula': f"{element}2",
                        'count': count // 2,
                        'type': 'diatomic'
                    })
        
        return molecules
    
    def _identify_molecules_basic(self, structure_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic molecule identification"""
        molecules = []
        
        # Simple heuristics for common molecules
        species = structure_info['species']
        
        # Oxygen molecules
        if 'O' in species and species['O'] >= 2:
            molecules.append({
                'formula': 'O2',
                'count': species['O'] // 2,
                'type': 'diatomic'
            })
        
        # Nitrogen molecules
        if 'N' in species and species['N'] >= 2:
            molecules.append({
                'formula': 'N2',
                'count': species['N'] // 2,
                'type': 'diatomic'
            })
        
        # Water molecules
        if 'H' in species and 'O' in species:
            water_count = min(species.get('H', 0) // 2, species.get('O', 0))
            if water_count > 0:
                molecules.append({
                    'formula': 'H2O',
                    'count': water_count,
                    'type': 'molecular'
                })
        
        return molecules
    
    def remove_molecules(self, structure_info: Dict[str, Any], 
                        molecule_formula: str) -> Dict[str, Any]:
        """
        Remove molecules from structure
        
        Args:
            structure_info: Structure information
            molecule_formula: Formula of molecules to remove
            
        Returns:
            Modified structure information
        """
        modified_structure = structure_info.copy()
        
        console.print(f"🧹 Removing {molecule_formula} molecules")
        
        # This would implement proper molecular recognition and removal
        # For now, implement basic element removal
        if molecule_formula == 'O2':
            # Remove oxygen atoms (simplified)
            if 'O' in modified_structure['species']:
                removed_count = modified_structure['species']['O']
                modified_structure['species']['O'] = 0
                modified_structure['atoms'] -= removed_count
                console.print(f"   Removed {removed_count} oxygen atoms")
        
        return modified_structure
    
    def add_molecules(self, structure_info: Dict[str, Any], 
                     molecule_formula: str, count: int) -> Dict[str, Any]:
        """
        Add molecules to structure
        
        Args:
            structure_info: Structure information
            molecule_formula: Formula of molecules to add
            count: Number of molecules to add
            
        Returns:
            Modified structure information
        """
        modified_structure = structure_info.copy()
        
        console.print(f"⚛️  Adding {count} {molecule_formula} molecules")
        
        # This would implement proper molecular addition
        # For now, implement basic element addition
        if molecule_formula == 'O':
            # Add oxygen atoms
            if 'O' not in modified_structure['species']:
                modified_structure['species']['O'] = 0
            
            modified_structure['species']['O'] += count
            modified_structure['atoms'] += count
            console.print(f"   Added {count} oxygen atoms")
        
        return modified_structure
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of molecular tools"""
        return {
            'available_tools': self.available_tools,
            'capabilities': {
                'structure_io': self.available_tools.get('ase', False),
                'molecular_recognition': self.available_tools.get('rdkit', False),
                'quantum_chemistry': self.available_tools.get('gaussian', False) or self.available_tools.get('jaguar', False),
                'visualization': self.available_tools.get('vmd', False),
                'packing': self.available_tools.get('packmol', False)
            }
        }
    
    def is_available(self) -> bool:
        """Check if any molecular tools are available"""
        return any(self.available_tools.values())

# CLI helper functions
def read_structure_cli(structure_file: str) -> Dict[str, Any]:
    """CLI wrapper for structure reading"""
    tools = MolecularTools()
    return tools.read_structure(structure_file)

def identify_molecules_cli(structure_file: str) -> List[Dict[str, Any]]:
    """CLI wrapper for molecule identification"""
    tools = MolecularTools()
    structure_info = tools.read_structure(structure_file)
    return tools.identify_molecules(structure_info)