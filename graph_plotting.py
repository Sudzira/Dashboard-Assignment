"""
Graph Plotting Module using Bokeh
Creates interactive network visualizations from Neo4j graph data
"""

import networkx as nx
from bokeh.models import (Circle, ColumnDataSource, HoverTool, MultiLine, 
                          Range1d, TapTool, Plot)
from bokeh.plotting import figure, from_networkx
from bokeh.palettes import Category20, Spectral4
from bokeh.transform import linear_cmap
from typing import Dict, Any, Tuple, List
import numpy as np


class GraphPlotter:
    def __init__(self, graph_data: Dict[str, Any]):
        """
        Initialize the graph plotter with graph data
        
        Args:
            graph_data: Dictionary containing nodes and relationships
        """
        self.graph_data = graph_data
        self.G = None
        self.plot = None
        self.graph_renderer = None
        self._create_networkx_graph()
    
    def _create_networkx_graph(self):
        """Create NetworkX graph from Neo4j data"""
        self.G = nx.DiGraph()
        
        # Add nodes with their properties
        for node_id, node_info in self.graph_data["nodes"].items():
            node_props = {
                "label": node_info["labels"][0] if node_info["labels"] else "Unknown",
                "type": node_info["labels"][0] if node_info["labels"] else "Unknown"
            }
            # Add other properties from the node
            node_props.update(node_info["properties"])
            # Add node to graph
            self.G.add_node(node_id, **node_props)
        
        # Add relationships
        for rel_id, rel_info in self.graph_data["relationships"].items():
            self.G.add_edge(rel_info["start_node"], 
                          rel_info["end_node"], 
                          type=rel_info["type"],
                          **rel_info.get("properties", {}))
    
    def create_visualization(self, width: int = 1200, height: int = 800, 
                           title: str = "Neo4j Graph Visualization") -> Tuple[Any, Any]:
        """
        Creates an interactive graph visualization using Bokeh.
        
        Args:
            width: Plot width in pixels
            height: Plot height in pixels
            title: Plot title
            
        Returns:
            Tuple of (plot, graph_renderer)
        """
        # Create Bokeh plot
        self.plot = figure(
            width=width, 
            height=height, 
            title=title,
            tools="pan,wheel_zoom,box_zoom,reset,save,tap",
            active_scroll='wheel_zoom'
        )
        
        # Create layout with much more spread and prevent overlap
        layout = nx.spring_layout(self.G, k=5, iterations=100, scale=4)
        
        # Create NetworkX graph renderer
        self.graph_renderer = from_networkx(self.G, layout)
        
        # Configure node appearance
        node_colors, node_sizes = self._get_node_styling()
        
        # Update node renderer with data
        node_data = {
            'index': list(self.G.nodes()),
            'color': node_colors,
            'radius': node_sizes,
            'type': [self.G.nodes[node].get("type", "Unknown") for node in self.G.nodes()],
            'name': [self._get_node_name(node) for node in self.G.nodes()],
            'properties': [self._format_node_properties(node) for node in self.G.nodes()]
        }
        self.graph_renderer.node_renderer.data_source.data.update(node_data)
        
        # Style nodes
        self.graph_renderer.node_renderer.glyph = Circle(
            radius='radius',
            fill_color='color',
            fill_alpha=0.8,
            line_color='black',
            line_width=1
        )
        
        # Style edges
        self.graph_renderer.edge_renderer.glyph = MultiLine(
            line_color="#CCCCCC",
            line_alpha=0.5,
            line_width=1
        )
        
        # Add hover tooltips
        node_hover = HoverTool(tooltips=[
            ("Type", "@type"),
            ("Name", "@name"),
            ("Properties", "@properties")
        ], renderers=[self.graph_renderer.node_renderer])
        
        self.plot.add_tools(node_hover)
        
        # Add graph to plot
        self.plot.renderers.append(self.graph_renderer)
        
        # Style the plot
        self.plot.axis.visible = False
        self.plot.grid.visible = False
        self.plot.outline_line_color = None
        
        return self.plot, self.graph_renderer
    
    def create_pattern_visualization(self, pattern_data: Dict[str, Any], 
                                   node_type_a: str, relationship_type: str, 
                                   node_type_b: str,
                                   width: int = 800, height: int = 600) -> Tuple[Any, Any, Any]:
        """
        Create a visualization for a specific pattern.
        
        Args:
            pattern_data: Graph data for the pattern
            node_type_a: First node type in pattern
            relationship_type: Relationship type
            node_type_b: Second node type in pattern
            width: Plot width
            height: Plot height
            
        Returns:
            Tuple of (plot, graph_renderer, pattern_graph)
        """
        # Create pattern graph
        pattern_G = nx.DiGraph()
        
        # Add nodes to pattern graph
        for node_id, node_info in pattern_data["nodes"].items():
            node_props = {
                "label": node_info["labels"][0] if node_info["labels"] else "Unknown",
                "type": node_info["labels"][0] if node_info["labels"] else "Unknown"
            }
            node_props.update(node_info["properties"])
            pattern_G.add_node(node_id, **node_props)
        
        # Add relationships
        for rel_id, rel_info in pattern_data["relationships"].items():
            pattern_G.add_edge(rel_info["start_node"], rel_info["end_node"], 
                             type=rel_info["type"],
                             **rel_info.get("properties", {}))
        
        # Create visualization for pattern
        plot = figure(
            width=width, 
            height=height, 
            title=f"Pattern: {node_type_a}-[{relationship_type}]->{node_type_b}",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            active_scroll='wheel_zoom'
        )
        
        # Create layout with more spread
        layout = nx.spring_layout(pattern_G, k=2, iterations=100)
        graph_renderer = from_networkx(pattern_G, layout)
        
        # Configure node appearance for pattern
        node_colors = []
        node_sizes = []
        for node in pattern_G.nodes():
            node_type = pattern_G.nodes[node]["type"]
            if node_type == node_type_a:
                node_colors.append("#FFD700")  # Gold for type A
                node_sizes.append(15)
            elif node_type == node_type_b:
                node_colors.append("#FF6B6B")  # Coral for type B
                node_sizes.append(15)
            else:
                node_colors.append("#CCCCCC")
                node_sizes.append(10)
        
        # Update node renderer
        node_data = {
            'index': list(pattern_G.nodes()),
            'color': node_colors,
            'radius': node_sizes,
            'type': [pattern_G.nodes[node]["type"] for node in pattern_G.nodes()],
            'name': [self._get_node_name(node, pattern_G) for node in pattern_G.nodes()],
            'properties': [self._format_node_properties(node, pattern_G) for node in pattern_G.nodes()]
        }
        graph_renderer.node_renderer.data_source.data.update(node_data)
        
        # Style nodes and edges
        graph_renderer.node_renderer.glyph = Circle(
            radius='radius',
            fill_color='color',
            fill_alpha=0.8,
            line_color='black',
            line_width=1
        )
        graph_renderer.edge_renderer.glyph = MultiLine(
            line_color="#FF1493",  # Deep pink for relationships
            line_alpha=0.8,
            line_width=2
        )
        
        # Add hover tooltips
        node_hover = HoverTool(tooltips=[
            ("Type", "@type"),
            ("Name", "@name"),
            ("Properties", "@properties")
        ], renderers=[graph_renderer.node_renderer])
        plot.add_tools(node_hover)
        
        # Add graph and style plot
        plot.renderers.append(graph_renderer)
        plot.axis.visible = False
        plot.grid.visible = False
        plot.outline_line_color = None
        
        return plot, graph_renderer, pattern_G
    
    def _get_node_styling(self) -> Tuple[List[str], List[int]]:
        """Get node colors and sizes based on node types"""
        node_colors = []
        node_sizes = []
        
        for node in self.G.nodes():
            node_type = self.G.nodes[node].get("type", "Unknown")
            # Color and size nodes by type
            if node_type == "Movie":
                node_colors.append("#3182bd")  # Blue
                node_sizes.append(10)
            elif node_type == "Person":
                node_colors.append("#31a354")  # Green
                node_sizes.append(8)
            elif node_type == "Actor_1" or node_type.startswith("Actor"):
                node_colors.append("#31a354")  # Green for actors
                node_sizes.append(8)
            elif node_type == "Director":
                node_colors.append("#e6550d")  # Orange
                node_sizes.append(12)
            elif node_type == "Genre":
                node_colors.append("#e6550d")  # Orange
                node_sizes.append(6)
            else:
                node_colors.append("#756bb1")  # Purple
                node_sizes.append(5)
        
        return node_colors, node_sizes
    
    def _get_node_name(self, node_id: str, graph: nx.Graph = None) -> str:
        """Extract a display name for a node"""
        if graph is None:
            graph = self.G
            
        node_data = graph.nodes[node_id]
        
        # Try common name fields
        for name_field in ['name', 'title', 'Series_Title', 'Name']:
            if name_field in node_data and node_data[name_field]:
                return str(node_data[name_field])
        
        # If no name found, use node type and truncated ID
        node_type = node_data.get("type", "Unknown")
        short_id = node_id.split(":")[-1][:8] if ":" in node_id else node_id[:8]
        return f"{node_type}_{short_id}"
    
    def _format_node_properties(self, node_id: str, graph: nx.Graph = None) -> str:
        """Format node properties for display"""
        if graph is None:
            graph = self.G
            
        node_data = graph.nodes[node_id]
        excluded_keys = {'type', 'label', 'name', 'title', 'Series_Title', 'Name'}
        
        relevant_props = {
            k: v for k, v in node_data.items() 
            if k not in excluded_keys and not k.startswith('_')
        }
        
        if not relevant_props:
            return "No additional properties"
            
        # Format properties nicely, limiting length
        formatted_props = []
        for k, v in list(relevant_props.items())[:5]:  # Limit to 5 properties
            if isinstance(v, str) and len(str(v)) > 50:
                v = str(v)[:50] + "..."
            formatted_props.append(f"{k}: {v}")
        
        result = "; ".join(formatted_props)
        if len(relevant_props) > 5:
            result += f" ... (+{len(relevant_props) - 5} more)"
            
        return result
    
    def highlight_nodes(self, search_term: str) -> List[str]:
        """
        Highlight nodes matching a search term and return their IDs
        
        Args:
            search_term: Term to search for in node properties
            
        Returns:
            List of matching node IDs
        """
        if not self.graph_renderer:
            return []
            
        search_term = search_term.lower()
        matching_nodes = []
        node_colors = []
        original_colors, _ = self._get_node_styling()
        
        for i, node in enumerate(self.G.nodes()):
            node_data = self.G.nodes[node]
            # Search in all node properties
            found = any(
                str(value).lower().find(search_term) >= 0 
                for value in node_data.values() 
                if isinstance(value, (str, int, float))
            )
            
            if found:
                node_colors.append("#FFD700")  # Gold color for matches
                matching_nodes.append(node)
            else:
                node_colors.append(original_colors[i])
        
        # Update the visualization
        self.graph_renderer.node_renderer.data_source.data['color'] = node_colors
        
        return matching_nodes
    
    def reset_node_colors(self):
        """Reset node colors to their original state based on type"""
        if not self.graph_renderer:
            return
            
        node_colors, _ = self._get_node_styling()
        self.graph_renderer.node_renderer.data_source.data['color'] = node_colors
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current graph"""
        if not self.G:
            return {}
            
        node_types = {}
        for node in self.G.nodes():
            node_type = self.G.nodes[node].get("type", "Unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        edge_types = {}
        for edge in self.G.edges(data=True):
            edge_type = edge[2].get("type", "Unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": node_types,
            "edge_types": edge_types,
            "is_connected": nx.is_connected(self.G.to_undirected()),
            "density": nx.density(self.G)
        }