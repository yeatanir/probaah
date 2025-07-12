# FILE: plugins/ai/mdcrow_agent.py
"""
MDCrow Agent with Probaah Tool Integration
LLM agent specialized for molecular dynamics and computational chemistry
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

class MDCrowAgent:
    """
    MDCrow (Molecular Dynamics Computational Research Operations Workflow) Agent
    LLM agent with integrated access to Probaah tools
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MDCrow agent
        
        Args:
            config: Agent configuration
        """
        self.config = config or {}
        self.tools = self._initialize_tools()
        self.conversation_history = []
        self.current_context = {}
        self.available_models = ['gpt-4o', 'llama3-405b', 'claude-3.5-sonnet']
        self.current_model = self.config.get('default_model', 'gpt-4o')
        
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize available tools for the agent"""
        tools = {}
        
        try:
            # Import Probaah tools
            import sys
            current_dir = Path(__file__).parent
            if str(current_dir) not in sys.path:
                sys.path.append(str(current_dir))
            
            from packmol_wrapper import ProbaahPackmol
            from visual_validation import VIAMDIntegration
            from tools.existing_probaah_tools import ExistingProbaahTools
            from tools.molecular_tools import MolecularTools
            
            tools['packmol'] = ProbaahPackmol()
            tools['viamd'] = VIAMDIntegration()
            tools['existing_analysis'] = ExistingProbaahTools()
            tools['molecular_tools'] = MolecularTools()
            
            # Tool descriptions for LLM
            tools['tool_descriptions'] = {
                'packmol': 'Modern wrapper for PACKMOL - gas substitution, molecular packing',
                'viamd': 'Visual validation and structure inspection tool',
                'existing_analysis': 'Enterprise-grade trajectory analysis and presentation tools',
                'molecular_tools': 'Molecular property calculations and structure manipulation'
            }
            
        except ImportError as e:
            console.print(f"⚠️  Tool initialization warning: {e}")
            
        return tools
    
    def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user request with LLM reasoning and tool integration
        
        Args:
            request: User request in natural language
            context: Additional context information
            
        Returns:
            Processing results
        """
        console.print(f"🤖 [bold blue]MDCrow Agent Processing[/bold blue]")
        console.print(f"📝 Request: {request}")
        
        # Update context
        if context:
            self.current_context.update(context)
        
        # Add to conversation history
        self.conversation_history.append({
            'type': 'user_request',
            'content': request,
            'timestamp': time.time(),
            'context': context
        })
        
        # Process request
        response = self._generate_response(request)
        
        # Add response to history
        self.conversation_history.append({
            'type': 'agent_response',
            'content': response,
            'timestamp': time.time()
        })
        
        return response
    
    def _generate_response(self, request: str) -> Dict[str, Any]:
        """
        Generate response using LLM reasoning and tool integration
        
        Args:
            request: User request
            
        Returns:
            Generated response
        """
        # Analyze request intent
        intent = self._analyze_intent(request)
        
        # Plan tool usage
        tool_plan = self._plan_tool_usage(request, intent)
        
        # Execute tools
        tool_results = self._execute_tools(tool_plan)
        
        # Generate final response
        final_response = self._synthesize_response(request, intent, tool_results)
        
        return final_response
    
    def _analyze_intent(self, request: str) -> Dict[str, Any]:
        """
        Analyze user intent from request
        
        Args:
            request: User request
            
        Returns:
            Intent analysis
        """
        request_lower = request.lower()
        
        # Intent categories
        intents = {
            'gas_substitution': ['substitute', 'replace', 'swap', 'remove', 'add'],
            'analysis': ['analyze', 'analysis', 'examine', 'study', 'investigate'],
            'validation': ['validate', 'verify', 'check', 'inspect', 'review'],
            'presentation': ['presentation', 'slides', 'powerpoint', 'report'],
            'visualization': ['visualize', 'render', 'display', 'show', 'plot'],
            'information': ['what', 'how', 'why', 'explain', 'describe'],
            'workflow': ['workflow', 'pipeline', 'process', 'complete', 'end-to-end']
        }
        
        # Calculate intent scores
        intent_scores = {}
        for intent_name, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in request_lower)
            if score > 0:
                intent_scores[intent_name] = score
        
        # Determine primary intent
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else 'general'
        
        return {
            'primary_intent': primary_intent,
            'intent_scores': intent_scores,
            'complexity': self._assess_complexity(request),
            'entities': self._extract_entities(request)
        }
    
    def _assess_complexity(self, request: str) -> str:
        """Assess request complexity"""
        complexity_indicators = {
            'simple': ['show', 'display', 'what', 'how'],
            'moderate': ['analyze', 'calculate', 'validate', 'substitute'],
            'complex': ['workflow', 'pipeline', 'complete', 'end-to-end', 'then', 'and']
        }
        
        request_lower = request.lower()
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                return complexity
        
        return 'simple'
    
    def _extract_entities(self, request: str) -> Dict[str, List[str]]:
        """Extract entities from request"""
        entities = {
            'files': [],
            'molecules': [],
            'numbers': [],
            'tools': []
        }
        
        # File patterns
        import re
        file_patterns = [
            r'(\w+\.(xyz|pdb|bgf|traj|car|mol2))',
            r'(\w+_\w+\.(xyz|pdb|bgf|traj|car|mol2))'
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
            r'\b([A-Z][a-z]?\d*)\b'
        ]
        
        for pattern in molecule_patterns:
            matches = re.findall(pattern, request, re.IGNORECASE)
            entities['molecules'].extend(matches)
        
        # Number patterns
        number_matches = re.findall(r'\d+', request)
        entities['numbers'] = [int(n) for n in number_matches]
        
        # Tool mentions
        for tool_name in self.tools.get('tool_descriptions', {}):
            if tool_name.lower() in request.lower():
                entities['tools'].append(tool_name)
        
        return entities
    
    def _plan_tool_usage(self, request: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Plan which tools to use and in what order
        
        Args:
            request: User request
            intent: Intent analysis
            
        Returns:
            Tool usage plan
        """
        tool_plan = []
        
        primary_intent = intent['primary_intent']
        entities = intent['entities']
        complexity = intent['complexity']
        
        # Plan based on intent
        if primary_intent == 'gas_substitution':
            tool_plan.append({
                'tool': 'packmol',
                'action': 'gas_substitution_workflow',
                'parameters': self._extract_substitution_parameters(request, entities),
                'priority': 1
            })
            
            # Add validation if requested
            if 'validate' in request.lower() or 'check' in request.lower():
                tool_plan.append({
                    'tool': 'viamd',
                    'action': 'validate_structure',
                    'parameters': {'interactive': False},
                    'priority': 2
                })
        
        elif primary_intent == 'analysis':
            tool_plan.append({
                'tool': 'existing_analysis',
                'action': 'analyze_trajectory',
                'parameters': self._extract_analysis_parameters(request, entities),
                'priority': 1
            })
        
        elif primary_intent == 'validation':
            tool_plan.append({
                'tool': 'viamd',
                'action': 'validate_structure',
                'parameters': {'interactive': True},
                'priority': 1
            })
        
        elif primary_intent == 'presentation':
            tool_plan.append({
                'tool': 'existing_analysis',
                'action': 'create_presentation',
                'parameters': self._extract_presentation_parameters(request, entities),
                'priority': 1
            })
        
        elif primary_intent == 'workflow':
            # Multi-step workflow
            tool_plan = self._plan_workflow_steps(request, entities)
        
        return tool_plan
    
    def _extract_substitution_parameters(self, request: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Extract gas substitution parameters"""
        params = {
            'input_structure': entities['files'][0] if entities['files'] else None,
            'remove_species': 'O2',  # Default
            'add_species': 'O',     # Default
            'count': 100,           # Default
            'density': 0.18         # Default
        }
        
        # Extract from request
        import re
        
        # Remove species
        remove_match = re.search(r'remove\s+(\w+)', request, re.IGNORECASE)
        if remove_match:
            params['remove_species'] = remove_match.group(1)
        
        # Add species
        add_match = re.search(r'add\s+(\w+)', request, re.IGNORECASE)
        if add_match:
            params['add_species'] = add_match.group(1)
        
        # Count
        if entities['numbers']:
            params['count'] = entities['numbers'][0]
        
        return params
    
    def _extract_analysis_parameters(self, request: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Extract analysis parameters"""
        params = {
            'trajectory_file': entities['files'][0] if entities['files'] else None,
            'bonds': 'bond' in request.lower(),
            'rdf': 'rdf' in request.lower(),
            'energy': 'energy' in request.lower(),
            'plots': 'plot' in request.lower()
        }
        
        return params
    
    def _extract_presentation_parameters(self, request: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Extract presentation parameters"""
        params = {
            'analysis_dir': 'analysis',
            'title': 'Research Results'
        }
        
        # Extract title
        import re
        title_match = re.search(r'title[:\s]+([^,\n]+)', request, re.IGNORECASE)
        if title_match:
            params['title'] = title_match.group(1).strip()
        
        return params
    
    def _plan_workflow_steps(self, request: str, entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Plan multi-step workflow"""
        steps = []
        
        # Parse workflow from request
        request_lower = request.lower()
        
        if 'substitute' in request_lower:
            steps.append({
                'tool': 'packmol',
                'action': 'gas_substitution_workflow',
                'parameters': self._extract_substitution_parameters(request, entities),
                'priority': 1
            })
        
        if 'validate' in request_lower:
            steps.append({
                'tool': 'viamd',
                'action': 'validate_structure',
                'parameters': {'interactive': False},
                'priority': 2
            })
        
        if 'analyze' in request_lower:
            steps.append({
                'tool': 'existing_analysis',
                'action': 'analyze_trajectory',
                'parameters': self._extract_analysis_parameters(request, entities),
                'priority': 3
            })
        
        if 'presentation' in request_lower:
            steps.append({
                'tool': 'existing_analysis',
                'action': 'create_presentation',
                'parameters': self._extract_presentation_parameters(request, entities),
                'priority': 4
            })
        
        return steps
    
    def _execute_tools(self, tool_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute planned tools
        
        Args:
            tool_plan: List of tool execution plans
            
        Returns:
            Tool execution results
        """
        tool_results = {}
        
        # Sort by priority
        tool_plan.sort(key=lambda x: x.get('priority', 0))
        
        for step in tool_plan:
            tool_name = step['tool']
            action = step['action']
            parameters = step.get('parameters', {})
            
            console.print(f"🔧 Executing: {tool_name}.{action}")
            
            try:
                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    
                    if hasattr(tool, action):
                        method = getattr(tool, action)
                        result = method(**parameters)
                        
                        tool_results[f"{tool_name}_{action}"] = {
                            'success': True,
                            'result': result,
                            'tool': tool_name,
                            'action': action
                        }
                        
                        console.print(f"✅ {tool_name}.{action} completed")
                    else:
                        console.print(f"⚠️  Method {action} not found in {tool_name}")
                        tool_results[f"{tool_name}_{action}"] = {
                            'success': False,
                            'error': f"Method {action} not found",
                            'tool': tool_name,
                            'action': action
                        }
                else:
                    console.print(f"⚠️  Tool {tool_name} not available")
                    tool_results[f"{tool_name}_{action}"] = {
                        'success': False,
                        'error': f"Tool {tool_name} not available",
                        'tool': tool_name,
                        'action': action
                    }
                    
            except Exception as e:
                console.print(f"❌ {tool_name}.{action} failed: {e}")
                tool_results[f"{tool_name}_{action}"] = {
                    'success': False,
                    'error': str(e),
                    'tool': tool_name,
                    'action': action
                }
        
        return tool_results
    
    def _synthesize_response(self, request: str, intent: Dict[str, Any], 
                           tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize final response from tool results
        
        Args:
            request: Original request
            intent: Intent analysis
            tool_results: Tool execution results
            
        Returns:
            Synthesized response
        """
        response = {
            'original_request': request,
            'intent': intent,
            'tool_results': tool_results,
            'success': all(result.get('success', False) for result in tool_results.values()),
            'summary': self._generate_summary(intent, tool_results),
            'recommendations': self._generate_recommendations(intent, tool_results),
            'next_steps': self._suggest_next_steps(intent, tool_results),
            'timestamp': time.time()
        }
        
        return response
    
    def _generate_summary(self, intent: Dict[str, Any], tool_results: Dict[str, Any]) -> str:
        """Generate response summary"""
        primary_intent = intent['primary_intent']
        success_count = sum(1 for result in tool_results.values() if result.get('success', False))
        total_count = len(tool_results)
        
        if success_count == total_count:
            return f"Successfully completed {primary_intent} request using {total_count} tools."
        else:
            return f"Partially completed {primary_intent} request: {success_count}/{total_count} tools succeeded."
    
    def _generate_recommendations(self, intent: Dict[str, Any], tool_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        
        # Check for failures
        for result in tool_results.values():
            if not result.get('success', False):
                tool_name = result.get('tool', 'unknown')
                if tool_name == 'packmol':
                    recommendations.append("Install PACKMOL: conda install -c conda-forge packmol")
                elif tool_name == 'viamd':
                    recommendations.append("Install VIAMD for visual validation")
        
        # General recommendations
        if intent['primary_intent'] == 'gas_substitution':
            recommendations.append("Consider visual validation after substitution")
            recommendations.append("Run trajectory analysis on substituted structure")
        
        return recommendations
    
    def _suggest_next_steps(self, intent: Dict[str, Any], tool_results: Dict[str, Any]) -> List[str]:
        """Suggest next steps"""
        next_steps = []
        
        primary_intent = intent['primary_intent']
        
        if primary_intent == 'gas_substitution':
            next_steps.extend([
                "Run visual validation on substituted structure",
                "Perform trajectory analysis",
                "Create presentation with results"
            ])
        elif primary_intent == 'analysis':
            next_steps.extend([
                "Create presentation from analysis results",
                "Export data for further processing",
                "Consider parameter sensitivity analysis"
            ])
        
        return next_steps
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.current_context = {}
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of available tools"""
        status = {}
        
        for tool_name, tool in self.tools.items():
            if tool_name == 'tool_descriptions':
                continue
                
            if hasattr(tool, 'is_available'):
                status[tool_name] = {
                    'available': tool.is_available(),
                    'description': self.tools['tool_descriptions'].get(tool_name, ''),
                    'type': type(tool).__name__
                }
            else:
                status[tool_name] = {
                    'available': True,
                    'description': self.tools['tool_descriptions'].get(tool_name, ''),
                    'type': type(tool).__name__
                }
        
        return status

# CLI helper functions
def mdcrow_process_cli(request: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    CLI wrapper for MDCrow agent processing
    
    Args:
        request: User request
        config: Agent configuration
        
    Returns:
        Processing results
    """
    agent = MDCrowAgent(config)
    return agent.process_request(request)

def mdcrow_interactive_cli(config: Optional[Dict[str, Any]] = None):
    """
    Interactive CLI for MDCrow agent
    
    Args:
        config: Agent configuration
    """
    agent = MDCrowAgent(config)
    
    console.print("🤖 [bold blue]MDCrow Agent - Interactive Mode[/bold blue]")
    console.print("🧬 Specialized for molecular dynamics and computational chemistry")
    console.print("💬 Type your requests in natural language")
    console.print("🚪 Type 'exit' to quit")
    console.print()
    
    while True:
        try:
            request = input("🤖 MDCrow> ").strip()
            
            if request.lower() in ['exit', 'quit', 'bye']:
                console.print("👋 Goodbye!")
                break
            
            if not request:
                continue
            
            console.print()
            response = agent.process_request(request)
            
            # Display response
            console.print(Panel(
                Text(response['summary'], style="bold green"),
                title="Response Summary",
                border_style="blue"
            ))
            
            if response['recommendations']:
                console.print("\n💡 [bold]Recommendations:[/bold]")
                for rec in response['recommendations']:
                    console.print(f"   • {rec}")
            
            if response['next_steps']:
                console.print("\n🔜 [bold]Next Steps:[/bold]")
                for step in response['next_steps']:
                    console.print(f"   • {step}")
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")
            break
        except Exception as e:
            console.print(f"❌ [red]Error: {e}[/red]")