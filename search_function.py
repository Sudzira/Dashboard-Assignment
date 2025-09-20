"""
Search Function Module using Bokeh
Provides interactive search and pattern exploration functionality
"""

from bokeh.models import (TextInput, Button, Select, Div, Column, Row)
from bokeh.layouts import column, row
from typing import Dict, Any, List, Callable, Optional
from fetch_graph_data import GraphDataFetcher
from graph_plotting import GraphPlotter
import datetime


class GraphSearchInterface:
    def __init__(self, graph_data: Dict[str, Any], graph_plotter: GraphPlotter, 
                 data_fetcher: GraphDataFetcher):
        """
        Initialize the search interface
        
        Args:
            graph_data: Complete graph data
            graph_plotter: GraphPlotter instance
            data_fetcher: GraphDataFetcher instance for pattern searches
        """
        self.graph_data = graph_data
        self.graph_plotter = graph_plotter
        self.data_fetcher = data_fetcher
        self.search_callbacks = []
        
    def create_text_search_controls(self) -> Column:
        """
        Create text-based search controls for nodes
        
        Returns:
            Bokeh Column layout with search controls
        """
        # Create search input
        search_input = TextInput(
            title="Search Nodes:", 
            placeholder="Enter node name...",
            width=300
        )
        
        # Create reset button
        reset_button = Button(
            label="Reset View", 
            button_type="warning",
            width=300
        )
        
        # JavaScript callback for real-time search (works in standalone HTML)
        search_callback = """
        const search_term = cb_obj.value.toLowerCase();
        const graph_renderer = %s;
        const original_colors = %s;
        const nodes_data = graph_renderer.node_renderer.data_source.data;
        const colors = nodes_data['color'];
        const names = nodes_data['name'];
        const properties = nodes_data['properties'];
        
        for (let i = 0; i < names.length; i++) {
            const node_text = (names[i] + ' ' + properties[i]).toLowerCase();
            if (search_term && node_text.includes(search_term)) {
                colors[i] = '#FFD700';  // Gold for matches
            } else {
                colors[i] = original_colors[i];
            }
        }
        
        graph_renderer.node_renderer.data_source.change.emit();
        """ % ("graph_renderer", str(self._get_original_colors()))
        
        # Note: For server-based deployment, use Python callbacks instead
        def search_nodes(attr, old, new):
            """Python callback for search (requires Bokeh server)"""
            matching_nodes = self.graph_plotter.highlight_nodes(new)
            print(f"Found {len(matching_nodes)} matching nodes")
        
        def reset_view():
            """Reset node colors to original state"""
            self.graph_plotter.reset_node_colors()
            search_input.value = ""
        
        # Add callbacks
        search_input.on_change('value', search_nodes)
        reset_button.on_click(reset_view)
        
        # Create layout
        controls = column(
            Div(text="<h3>Text Search</h3>"),
            search_input,
            reset_button,
            width=300
        )
        
        return controls
    
    def create_pattern_search_controls(self) -> Column:
        """
        Create pattern search controls with dropdowns
        
        Returns:
            Bokeh Column layout with pattern search controls
        """
        # Get unique node types and relationship types
        node_types = self._get_node_types()
        rel_types = self._get_relationship_types()
        
        # Create dropdowns
        node_type_a_dropdown = Select(
            title="Node Type A:",
            options=sorted(list(node_types)),
            value=sorted(list(node_types))[0] if node_types else None,
            width=300
        )
        
        relationship_dropdown = Select(
            title="Relationship Type:",
            options=sorted(list(rel_types)),
            value=sorted(list(rel_types))[0] if rel_types else None,
            width=300
        )
        
        node_type_b_dropdown = Select(
            title="Node Type B:",
            options=sorted(list(node_types)),
            value=sorted(list(node_types))[1] if len(node_types) > 1 else (
                sorted(list(node_types))[0] if node_types else None),
            width=300
        )
        
        # Create search button
        search_pattern_button = Button(
            label="Search Pattern", 
            button_type="success",
            width=300
        )
        
        def search_pattern():
            """Handle pattern search"""
            type_a = node_type_a_dropdown.value
            rel_type = relationship_dropdown.value
            type_b = node_type_b_dropdown.value
            
            if not all([type_a, rel_type, type_b]):
                print("Please select values in all dropdowns")
                return
            
            # Get pattern data from database
            pattern_data = self.data_fetcher.get_pattern_data(type_a, rel_type, type_b)
            
            if not pattern_data or not pattern_data["nodes"]:
                print(f"No data found for pattern: {type_a}-[{rel_type}]->{type_b}")
                return
            
            # Create pattern visualization
            self._create_pattern_visualization(pattern_data, type_a, rel_type, type_b)
        
        # Add callback
        search_pattern_button.on_click(search_pattern)
        
        # Create layout
        controls = column(
            Div(text="<h3>Pattern Search</h3>"),
            Div(text="<p>Find relationships between node types</p>"),
            node_type_a_dropdown,
            relationship_dropdown,
            node_type_b_dropdown,
            Div(text="<br>"),
            search_pattern_button,
            width=300
        )
        
        return controls
    
    def create_advanced_search_controls(self) -> Column:
        """
        Create advanced search controls for property-based searches
        
        Returns:
            Bokeh Column layout with advanced search controls
        """
        node_types = self._get_node_types()
        
        # Node type selector
        node_type_select = Select(
            title="Filter by Node Type:",
            options=["All"] + sorted(list(node_types)),
            value="All",
            width=300
        )
        
        # Property search
        property_input = TextInput(
            title="Property Name:",
            placeholder="e.g., IMDB_Rating, Genre",
            width=300
        )
        
        property_value_input = TextInput(
            title="Property Value:",
            placeholder="e.g., > 8.0, Drama",
            width=300
        )
        
        search_properties_button = Button(
            label="Search by Property",
            button_type="primary",
            width=300
        )
        
        def search_by_property():
            """Search nodes by property values"""
            node_type = node_type_select.value if node_type_select.value != "All" else None
            prop_name = property_input.value.strip()
            prop_value = property_value_input.value.strip()
            
            if not prop_name:
                print("Please enter a property name")
                return
            
            # For simple equality search
            if prop_value and not any(op in prop_value for op in ['>', '<', '>=', '<=', '!=']):
                # Try to convert to appropriate type
                try:
                    if prop_value.isdigit():
                        prop_value = int(prop_value)
                    elif prop_value.replace('.', '').isdigit():
                        prop_value = float(prop_value)
                except:
                    pass  # Keep as string
                
                # Search using the data fetcher
                results = self.data_fetcher.search_nodes_by_property(
                    prop_name, prop_value, node_type
                )
                
                if results:
                    print(f"Found {len(results)} nodes with {prop_name}={prop_value}")
                    # Highlight matching nodes (simplified - would need node ID mapping)
                    self._highlight_property_matches(results)
                else:
                    print(f"No nodes found with {prop_name}={prop_value}")
            else:
                print("Advanced property filtering (>, <, etc.) requires custom implementation")
        
        search_properties_button.on_click(search_by_property)
        
        # Create layout
        controls = column(
            Div(text="<h3>Advanced Search</h3>"),
            node_type_select,
            property_input,
            property_value_input,
            search_properties_button,
            width=300
        )
        
        return controls
    
    def _create_pattern_visualization(self, pattern_data: Dict[str, Any], 
                                    type_a: str, rel_type: str, type_b: str):
        """
        Create and save a pattern visualization
        
        Args:
            pattern_data: Graph data for the pattern
            type_a: First node type
            rel_type: Relationship type  
            type_b: Second node type
        """
        from bokeh.io import output_file, save
        from bokeh.layouts import row, column
        
        # Create pattern visualization
        plot, graph_renderer, pattern_G = self.graph_plotter.create_pattern_visualization(
            pattern_data, type_a, rel_type, type_b
        )
        
        # Create statistics
        matching_nodes_a = [n for n in pattern_G.nodes() 
                           if pattern_G.nodes[n].get("type") == type_a]
        matching_nodes_b = [n for n in pattern_G.nodes() 
                           if pattern_G.nodes[n].get("type") == type_b]
        
        stats_text = f"""
        <div style="font-family: Arial; padding: 10px; background: #f0f0f0; border-radius: 5px;">
        <h4>Pattern Statistics</h4>
        <ul>
        <li><strong>{type_a}</strong> nodes: {len(matching_nodes_a)}</li>
        <li><strong>{type_b}</strong> nodes: {len(matching_nodes_b)}</li>
        <li><strong>{rel_type}</strong> relationships: {len(pattern_data["relationships"])}</li>
        <li><strong>Total nodes</strong>: {len(pattern_data["nodes"])}</li>
        </ul>
        </div>
        """
        
        stats_div = Div(text=stats_text, width=400)
        
        # Create property exploration for pattern
        property_controls = PatternPropertyExplorer(pattern_data, pattern_G, graph_renderer)
        property_layout = property_controls.create_controls()
        
        # Create final layout
        final_layout = row(
            column(plot, stats_div),
            property_layout
        )
        
        # Save to HTML
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pattern_search_{type_a}_{rel_type}_{type_b}_{timestamp}.html"
        output_file(filename, title=f"Pattern: {type_a}-[{rel_type}]->{type_b}")
        save(final_layout)
        
        print(f"Pattern visualization saved to {filename}")
    
    def _get_node_types(self) -> set:
        """Get unique node types from graph data"""
        node_types = set()
        for node_info in self.graph_data["nodes"].values():
            node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
            node_types.add(node_type)
        return node_types
    
    def _get_relationship_types(self) -> set:
        """Get unique relationship types from graph data"""
        rel_types = set()
        for rel_info in self.graph_data["relationships"].values():
            rel_types.add(rel_info["type"])
        return rel_types
    
    def _get_original_colors(self) -> List[str]:
        """Get original node colors for JavaScript callback"""
        colors, _ = self.graph_plotter._get_node_styling()
        return colors
    
    def _highlight_property_matches(self, matching_results: List[Dict]):
        """Highlight nodes that match property search"""
        # This would require mapping between search results and visualization
        # Simplified implementation
        print(f"Would highlight {len(matching_results)} nodes")


class PatternPropertyExplorer:
    """Handles property exploration within pattern search results"""
    
    def __init__(self, pattern_data: Dict[str, Any], pattern_graph, graph_renderer):
        self.pattern_data = pattern_data
        self.pattern_graph = pattern_graph
        self.graph_renderer = graph_renderer
    
    def create_controls(self) -> Column:
        """Create property exploration controls"""
        # Get node types and their properties
        node_types = set()
        node_properties = {}
        
        for node_id in self.pattern_graph.nodes():
            node_info = self.pattern_data["nodes"][node_id]
            node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
            node_types.add(node_type)
            
            if node_type not in node_properties:
                node_properties[node_type] = set()
            
            node_properties[node_type].update(node_info["properties"].keys())
        
        # Create dropdowns
        node_type_dropdown = Select(
            title="Explore Node Type:",
            options=sorted(list(node_types)),
            value=sorted(list(node_types))[0] if node_types else None,
            width=300
        )
        
        initial_properties = sorted(list(node_properties.get(node_type_dropdown.value, [])))
        property_dropdown = Select(
            title="Select Property:",
            options=initial_properties,
            value=initial_properties[0] if initial_properties else None,
            width=300
        )
        
        # Filter input
        filter_input = TextInput(
            title="Filter Value:",
            placeholder="e.g., > 1990, Drama, contains Action",
            width=300
        )
        
        apply_filter_button = Button(
            label="Apply Filter",
            button_type="primary",
            width=300
        )
        
        def update_property_options(attr, old, new):
            if new in node_properties:
                property_dropdown.options = sorted(list(node_properties[new]))
                property_dropdown.value = property_dropdown.options[0] if property_dropdown.options else None
        
        def apply_property_filter():
            selected_type = node_type_dropdown.value
            selected_property = property_dropdown.value
            filter_condition = filter_input.value
            
            if not all([selected_type, selected_property]):
                print("Please select node type and property")
                return
            
            # Apply filter logic (simplified)
            self._apply_filter(selected_type, selected_property, filter_condition)
        
        # Add callbacks
        node_type_dropdown.on_change('value', update_property_options)
        apply_filter_button.on_click(apply_property_filter)
        
        # Create layout
        controls = column(
            Div(text="<h3>Explore Properties</h3>"),
            node_type_dropdown,
            property_dropdown,
            filter_input,
            apply_filter_button,
            width=300
        )
        
        return controls
    
    def _apply_filter(self, node_type: str, property_name: str, filter_condition: str):
        """Apply property-based filter to visualization"""
        # Simplified filter implementation
        print(f"Applying filter: {node_type}.{property_name} {filter_condition}")
        
        # Update node colors based on filter
        matching_count = 0
        node_colors = []
        
        for node in self.pattern_graph.nodes():
            node_info = self.pattern_data["nodes"][node]
            current_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
            property_value = node_info["properties"].get(property_name)
            
            matches = (current_type == node_type and 
                      property_value is not None and
                      self._evaluate_filter(property_value, filter_condition))
            
            if matches:
                node_colors.append("#FFD700")  # Gold for matches
                matching_count += 1
            else:
                node_colors.append("#CCCCCC")  # Gray for non-matches
        
        # Update visualization
        if self.graph_renderer:
            self.graph_renderer.node_renderer.data_source.data['color'] = node_colors
        
        print(f"Filter applied: {matching_count} nodes match the condition")
    
    def _evaluate_filter(self, value, filter_condition: str) -> bool:
        """Evaluate a simple filter condition"""
        if not filter_condition:
            return True
        
        filter_condition = filter_condition.strip().lower()
        
        # String contains
        if "contains" in filter_condition:
            search_term = filter_condition.split("contains")[1].strip().strip("'\"")
            return isinstance(value, str) and search_term.lower() in str(value).lower()
        
        # Equality
        if filter_condition.startswith("==") or "=" in filter_condition:
            compare_value = filter_condition.replace("==", "").replace("=", "").strip().strip("'\"")
            try:
                if compare_value.isdigit():
                    return float(value) == float(compare_value)
                return str(value).lower() == compare_value.lower()
            except:
                return False
        
        # Numeric comparisons
        try:
            numeric_value = float(value)
            if filter_condition.startswith(">"):
                threshold = float(filter_condition[1:].strip())
                return numeric_value > threshold
            elif filter_condition.startswith("<"):
                threshold = float(filter_condition[1:].strip())
                return numeric_value < threshold
        except:
            return False
        
        return True
