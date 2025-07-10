# FILE: plugins/analysis/ase_tools/trajectory_analyzer.py
"""
ASE-Powered Trajectory Analysis for Probaah
Analyzes molecular dynamics trajectories with publication-quality output
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

from ase.io import read, write
from ase import Atoms
from ase.geometry import get_distances
from ase.neighborlist import NeighborList
from ase.data import covalent_radii, atomic_numbers
from ase.visualize.plot import plot_atoms

class ProbaahTrajectoryAnalyzer:
    """
    Comprehensive trajectory analysis using ASE
    Perfect for ReaxFF and other MD simulations
    """
    
    def __init__(self, trajectory_file: str, output_dir: Optional[str] = None):
        """
        Initialize trajectory analyzer
        
        Args:
            trajectory_file: Path to trajectory (.xyz, .traj, etc.)
            output_dir: Directory for output files
        """
        self.trajectory_file = Path(trajectory_file)
        self.output_dir = Path(output_dir) if output_dir else self.trajectory_file.parent / "analysis"
        self.output_dir.mkdir(exist_ok=True)
        
        # Load trajectory
        print(f"🔍 Loading trajectory: {self.trajectory_file}")
        self.trajectory = read(str(self.trajectory_file), index=':')
        self.n_frames = len(self.trajectory)
        self.n_atoms = len(self.trajectory[0])
        
        print(f"✅ Loaded {self.n_frames} frames with {self.n_atoms} atoms each")
        
        # Analysis results storage
        self.results = {}
        
    def analyze_bonds(self, cutoff_factor: float = 1.2, 
                     elements: Optional[List[str]] = None) -> Dict:
        """
        Analyze bond formation/breaking throughout trajectory
        
        Args:
            cutoff_factor: Multiplier for covalent radii to define bonds
            elements: Specific elements to analyze (default: all)
            
        Returns:
            Dictionary with bond analysis results
        """
        print("🔗 Analyzing bonds...")
        
        bond_counts = []
        bond_lengths = []
        
        for frame_idx, atoms in enumerate(self.trajectory):
            # Create neighbor list
            cutoffs = []
            for atom in atoms:
                radius = covalent_radii[atom.number] * cutoff_factor
                cutoffs.append(radius)
            
            nl = NeighborList(cutoffs, self_interaction=False, bothways=True)
            nl.update(atoms)
            
            frame_bonds = 0
            frame_lengths = []
            
            for i in range(len(atoms)):
                indices, offsets = nl.get_neighbors(i)
                for j in indices:
                    if i < j:  # Count each bond only once
                        distance = atoms.get_distance(i, j)
                        frame_bonds += 1
                        frame_lengths.append(distance)
            
            bond_counts.append(frame_bonds)
            bond_lengths.append(frame_lengths)
            
            if frame_idx % 100 == 0:
                print(f"  Processed frame {frame_idx}/{self.n_frames}")
        
        # Store results
        self.results['bonds'] = {
            'counts': bond_counts,
            'lengths': bond_lengths,
            'avg_count': np.mean(bond_counts),
            'avg_length': np.mean([np.mean(lengths) for lengths in bond_lengths if lengths])
        }
        
        print(f"✅ Bond analysis complete. Average bonds: {self.results['bonds']['avg_count']:.1f}")
        return self.results['bonds']
    
    def calculate_rdf(self, rmax: float = 10.0, nbins: int = 200, 
                     elements: Optional[Tuple[str, str]] = None) -> Dict:
        """
        Calculate radial distribution function
        
        Args:
            rmax: Maximum distance for RDF
            nbins: Number of bins
            elements: Pair of elements to analyze (e.g., ('C', 'O'))
            
        Returns:
            Dictionary with RDF data
        """
        print("📊 Calculating radial distribution function...")
        
        r_bins = np.linspace(0, rmax, nbins)
        dr = r_bins[1] - r_bins[0]
        
        rdf_sum = np.zeros(nbins - 1)
        n_frames_used = 0
        
        for frame_idx, atoms in enumerate(self.trajectory[::10]):  # Sample every 10th frame
            distances = []
            
            if elements:
                # Filter for specific element pairs
                elem1_indices = [i for i, atom in enumerate(atoms) if atom.symbol == elements[0]]
                elem2_indices = [i for i, atom in enumerate(atoms) if atom.symbol == elements[1]]
                
                for i in elem1_indices:
                    for j in elem2_indices:
                        if i != j:
                            dist = atoms.get_distance(i, j)
                            if dist < rmax:
                                distances.append(dist)
            else:
                # All pairs
                for i in range(len(atoms)):
                    for j in range(i + 1, len(atoms)):
                        dist = atoms.get_distance(i, j)
                        if dist < rmax:
                            distances.append(dist)
            
            if distances:
                hist, _ = np.histogram(distances, bins=r_bins)
                rdf_sum += hist
                n_frames_used += 1
            
            if frame_idx % 50 == 0:
                print(f"  Processed frame {frame_idx * 10}/{self.n_frames}")
        
        # Normalize RDF
        r_centers = (r_bins[:-1] + r_bins[1:]) / 2
        shell_volumes = 4 * np.pi * r_centers**2 * dr
        
        if n_frames_used > 0:
            rdf = rdf_sum / (n_frames_used * shell_volumes * (self.n_atoms / atoms.get_volume()))
        else:
            rdf = np.zeros_like(r_centers)
        
        self.results['rdf'] = {
            'r': r_centers,
            'g_r': rdf,
            'elements': elements,
            'frames_analyzed': n_frames_used
        }
        
        print(f"✅ RDF calculation complete. Analyzed {n_frames_used} frames.")
        return self.results['rdf']
    
    def analyze_energy(self) -> Dict:
        """
        Analyze energy evolution (if available in trajectory)
        """
        print("⚡ Analyzing energy evolution...")
        
        energies = []
        for atoms in self.trajectory:
            try:
                energy = atoms.get_potential_energy()
                energies.append(energy)
            except:
                # Energy not available in this frame
                energies.append(None)
        
        if all(e is None for e in energies):
            print("⚠️  No energy data found in trajectory")
            return {}
        
        # Filter out None values
        valid_energies = [e for e in energies if e is not None]
        
        self.results['energy'] = {
            'values': energies,
            'mean': np.mean(valid_energies),
            'std': np.std(valid_energies),
            'min': np.min(valid_energies),
            'max': np.max(valid_energies)
        }
        
        print(f"✅ Energy analysis complete. Mean energy: {self.results['energy']['mean']:.2f}")
        return self.results['energy']
    
    def create_plots(self, style: str = 'publication') -> Dict[str, str]:
        """
        Generate publication-quality plots
        
        Args:
            style: Plot style ('publication', 'presentation', 'quick')
            
        Returns:
            Dictionary mapping plot types to file paths
        """
        print("📈 Creating plots...")
        
        # Set style
        if style == 'publication':
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.rcParams.update({
                'font.size': 12,
                'axes.linewidth': 1.5,
                'lines.linewidth': 2,
                'figure.dpi': 300
            })
        
        plot_files = {}
        
        # Bond count evolution
        if 'bonds' in self.results:
            fig, ax = plt.subplots(figsize=(10, 6))
            frames = range(len(self.results['bonds']['counts']))
            ax.plot(frames, self.results['bonds']['counts'], 'b-', alpha=0.7)
            ax.set_xlabel('Frame')
            ax.set_ylabel('Number of Bonds')
            ax.set_title('Bond Count Evolution')
            ax.grid(True, alpha=0.3)
            
            plot_file = self.output_dir / 'bond_evolution.png'
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            plot_files['bond_evolution'] = str(plot_file)
            print(f"  📊 Saved: {plot_file}")
        
        # RDF plot
        if 'rdf' in self.results:
            fig, ax = plt.subplots(figsize=(10, 6))
            rdf_data = self.results['rdf']
            ax.plot(rdf_data['r'], rdf_data['g_r'], 'r-', linewidth=2)
            ax.set_xlabel('Distance (Å)')
            ax.set_ylabel('g(r)')
            title = 'Radial Distribution Function'
            if rdf_data['elements']:
                title += f" ({rdf_data['elements'][0]}-{rdf_data['elements'][1]})"
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(bottom=0)
            
            plot_file = self.output_dir / 'rdf.png'
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            plot_files['rdf'] = str(plot_file)
            print(f"  📊 Saved: {plot_file}")
        
        # Energy evolution
        if 'energy' in self.results and self.results['energy']:
            energies = self.results['energy']['values']
            valid_energies = [e for e in energies if e is not None]
            if valid_energies:
                fig, ax = plt.subplots(figsize=(10, 6))
                frames = [i for i, e in enumerate(energies) if e is not None]
                ax.plot(frames, valid_energies, 'g-', alpha=0.8)
                ax.set_xlabel('Frame')
                ax.set_ylabel('Energy (eV)')
                ax.set_title('Energy Evolution')
                ax.grid(True, alpha=0.3)
                
                plot_file = self.output_dir / 'energy_evolution.png'
                plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                plt.close()
                plot_files['energy_evolution'] = str(plot_file)
                print(f"  📊 Saved: {plot_file}")
        
        print(f"✅ Created {len(plot_files)} plots in {self.output_dir}")
        return plot_files
    
    def save_results(self, filename: str = 'analysis_results.json') -> str:
        """
        Save analysis results to JSON file
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_file = self.output_dir / filename
        
        # Convert numpy arrays to lists for JSON serialization
        json_results = {}
        for key, value in self.results.items():
            if isinstance(value, dict):
                json_results[key] = {}
                for k, v in value.items():
                    if isinstance(v, np.ndarray):
                        json_results[key][k] = v.tolist()
                    elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], list):
                        # Handle nested lists (like bond_lengths)
                        json_results[key][k] = [sublist for sublist in v]
                    else:
                        json_results[key][k] = v
            else:
                json_results[key] = value
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"💾 Saved results to: {output_file}")
        return str(output_file)
    
    def create_summary_report(self) -> str:
        """
        Create a text summary of analysis results
        
        Returns:
            Path to summary report
        """
        report_file = self.output_dir / 'analysis_summary.txt'
        
        with open(report_file, 'w') as f:
            f.write("🌊 PROBAAH TRAJECTORY ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Trajectory File: {self.trajectory_file}\n")
            f.write(f"Number of Frames: {self.n_frames}\n")
            f.write(f"Number of Atoms: {self.n_atoms}\n")
            f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if 'bonds' in self.results:
                bonds = self.results['bonds']
                f.write("BOND ANALYSIS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Average Bond Count: {bonds['avg_count']:.1f}\n")
                f.write(f"Average Bond Length: {bonds['avg_length']:.3f} Å\n")
                f.write(f"Bond Count Range: {min(bonds['counts'])} - {max(bonds['counts'])}\n\n")
            
            if 'rdf' in self.results:
                rdf = self.results['rdf']
                f.write("RADIAL DISTRIBUTION FUNCTION\n")
                f.write("-" * 30 + "\n")
                f.write(f"Frames Analyzed: {rdf['frames_analyzed']}\n")
                if rdf['elements']:
                    f.write(f"Element Pair: {rdf['elements'][0]}-{rdf['elements'][1]}\n")
                f.write(f"First Peak Position: {rdf['r'][np.argmax(rdf['g_r'])]:.3f} Å\n")
                f.write(f"First Peak Height: {np.max(rdf['g_r']):.3f}\n\n")
            
            if 'energy' in self.results and self.results['energy']:
                energy = self.results['energy']
                f.write("ENERGY ANALYSIS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Mean Energy: {energy['mean']:.3f} eV\n")
                f.write(f"Energy Range: {energy['min']:.3f} - {energy['max']:.3f} eV\n")
                f.write(f"Standard Deviation: {energy['std']:.3f} eV\n\n")
        
        print(f"📄 Created summary report: {report_file}")
        return str(report_file)

def analyze_trajectory_cli(trajectory_file: str, output_dir: str = None, 
                          bonds: bool = True, rdf: bool = True, 
                          energy: bool = True, plots: bool = True) -> Dict:
    """
    Command-line interface for trajectory analysis
    
    Args:
        trajectory_file: Path to trajectory file
        output_dir: Output directory
        bonds: Perform bond analysis
        rdf: Calculate RDF
        energy: Analyze energy
        plots: Create plots
        
    Returns:
        Analysis results dictionary
    """
    analyzer = ProbaahTrajectoryAnalyzer(trajectory_file, output_dir)
    
    if bonds:
        analyzer.analyze_bonds()
    
    if rdf:
        analyzer.calculate_rdf()
    
    if energy:
        analyzer.analyze_energy()
    
    if plots:
        analyzer.create_plots()
    
    # Save results
    analyzer.save_results()
    analyzer.create_summary_report()
    
    return analyzer.results

# Example usage
if __name__ == "__main__":
    # Test with a sample trajectory
    # analyzer = ProbaahTrajectoryAnalyzer("trajectory.xyz")
    # analyzer.analyze_bonds()
    # analyzer.calculate_rdf()
    # analyzer.create_plots()
    print("🌊 ASE Trajectory Analyzer ready for Probaah!")
