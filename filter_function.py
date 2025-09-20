"""
Filter Function Module using Bokeh
Provides advanced filtering and property-based analysis functionality
"""

from bokeh.models import (TextInput, Button, Select, Div, Slider, RadioButtonGroup,
                          MultiSelect, CheckboxGroup, Column, Row, DataTable, TableColumn)
from bokeh.layouts import column, row
from typing import Dict, Any, List, Tuple, Optional, Union
import networkx as nx
import re


class GraphFilterInterface:
    def __init__(self, graph_data: Dict[str, Any], graph_plotter, graph_renderer):
        """
        Initialize the filter interface
        
        Args:
            graph_data: Complete graph data
            graph_plotter: GraphPlotter instance
            graph_renderer: Bokeh graph renderer
        """
        self.graph_data = graph_data
        self.graph_plotter = graph_plotter
        self.graph_renderer = graph_renderer
        self.original_colors, self.original_sizes = graph_plotter._get_node_styling()
        self.active_filters = {}
        
    def create_node_type_filter(self) -> Column:
        """
        Create node type filtering controls
        
        Returns:
            Bokeh Column with node type filter controls
        """
        # Get all node types
        node_types = self._get_all_node_types()
        
        # Create multi-select for node types
        node_type_multiselect = MultiSelect(
            title="Show Node Types:",
            value=list(node_types),
            options=list(node_types),
            height=150,
            width=300
        )
        
        # Create toggle buttons for quick selection
        toggle_buttons = RadioButtonGroup(
            labels=["Show All", "Hide All", "Movies Only", "Actors Only"],
            active=0,
            width=300
        )
        
        def update_node_type_filter(attr, old, new):
            """Update visualization based on selected node types"""
            selected_types = set(new)
            self._apply_node_type_filter(selected_types)
            self.active_filters['node_types'] = selected_types
        
        def toggle_node_types(active):
            """Handle toggle button clicks"""
            all_types = list(node_types)
            if active == 0:  # Show All
                node_type_multiselect.value = all_types
            elif active == 1:  # Hide All
                node_type_multiselect.value = []
            elif active == 2:  # Movies Only
                movie_types = [t for t in all_types if 'movie' in t.lower()]
                node_type_multiselect.value = movie_types
            elif active == 3:  # Actors Only
                actor_types = [t for t in all_types if 'actor' in t.lower() or 'person' in t.lower()]
                node_type_multiselect.value = actor_types
        
        # Add callbacks
        node_type_multiselect.on_change('value', update_node_type_filter)
        toggle_buttons.on_click(toggle_node_types)
        
        # Create layout
        controls = column(
            Div(text="<h3>Filter by Node Type</h3>"),
            toggle_buttons,
            node_type_multiselect,
            width=300
        )
        
        return controls
    
    def create_property_range_filter(self) -> Column:
        """
        Create numeric property range filtering controls
        
        Returns:
            Bokeh Column with property range filter controls
        """
        # Get numeric properties
        numeric_properties = self._get_numeric_properties()
        
        property_select = Select(
            title="Select Numeric Property:",
            options=list(numeric_properties.keys()),
            value=list(numeric_properties.keys())[0] if numeric_properties else None,
            width=300
        )
        
        # Initialize with first property if available
        initial_prop = list(numeric_properties.keys())[0] if numeric_properties else None
        initial_range = numeric_properties.get(initial_prop, (0, 100)) if initial_prop else (0, 100)
        
        range_slider = Slider(
            title="Value Range:",
            start=initial_range[0],
            end=initial_range[1],
            value=initial_range[0],
            step=(initial_range[1] - initial_range[0]) / 100 if initial_range[1] > initial_range[0] else 1,
            width=300
        )
        
        max_slider = Slider(
            title="Maximum Value:",
            start=initial_range[0],
            end=initial_range[1],
            value=initial_range[1],
            step=(initial_range[1] - initial_range[0]) / 100 if initial_range[1] > initial_range[0] else 1,
            width=300
        )
        
        apply_range_button = Button(
            label="Apply Range Filter",
            button_type="primary",
            width=300
        )
        
        def update_range_sliders(attr, old, new):
            """Update slider ranges when property changes"""
            if new in numeric_properties:
                min_val, max_val = numeric_properties[new]
                step_val = (max_val - min_val) / 100 if max_val > min_val else 1
                
                range_slider.start = min_val
                range_slider.end = max_val
                range_slider.value = min_val
                range_slider.step = step_val
                
                max_slider.start = min_val
                max_slider.end = max_val
                max_slider.value = max_val
                max_slider.step = step_val
        
        def apply_range_filter():
            """Apply numeric range filter"""
            property_name = property_select.value
            min_value = range_slider.value
            max_value = max_slider.value
            
            if not property_name:
                print("Please select a property")
                return
            
            self._apply_numeric_range_filter(property_name, min_value, max_value)
            self.active_filters[f'range_{property_name}'] = (min_value, max_value)
        
        # Add callbacks
        property_select.on_change('value', update_range_sliders)
        apply_range_button.on_click(apply_range_filter)
        
        # Create layout
        controls = column(
            Div(text="<h3>Filter by Numeric Range</h3>"),
            property_select,
            range_slider,
            max_slider,
            apply_range_button,
            width=300
        )
        
        return controls
    
    def create_text_property_filter(self) -> Column:
        """
        Create text property filtering controls
        
        Returns:
            Bokeh Column with text property filter controls
        """
        # Get text properties
        text_properties = self._get_text_properties()
        
        property_select = Select(
            title="Select Text Property:",
            options=list(text_properties.keys()),
            value=list(text_properties.keys())[0] if text_properties else None,
            width=300
        )
        
        filter_mode = RadioButtonGroup(
            labels=["Contains", "Equals", "Starts With", "Regex"],
            active=0,
            width=300
        )
        
        text_input = TextInput(
            title="Filter Text:",
            placeholder="Enter text to filter...",
            width=300
        )
        
        case_sensitive_checkbox = CheckboxGroup(
            labels=["Case Sensitive"],
            active=[],
            width=300
        )
        
        apply_text_button = Button(
            label="Apply Text Filter",
            button_type="primary",
            width=300
        )
        
        def apply_text_filter():
            """Apply text-based filter"""
            property_name = property_select.value
            filter_text = text_input.value
            mode = filter_mode.active
            case_sensitive = 0 in case_sensitive_checkbox.active
            
            if not property_name or not filter_text:
                print("Please select a property and enter filter text")
                return
            
            self._apply_text_filter(property_name, filter_text, mode, case_sensitive)
            self.active_filters[f'text_{property_name}'] = {
                'text': filter_text,
                'mode': mode,
                'case_sensitive': case_sensitive
            }
        
        apply_text_button.on_click(apply_text_filter)
        
        # Create layout
        controls = column(
            Div(text="<h3>Filter by Text Property</h3>"),
            property_select,
            filter_mode,
            text_input,
            case_sensitive_checkbox,
            apply_text_button,
            width=300
        )
        
        return controls
    
    def create_relationship_filter(self) -> Column:
        """
        Create relationship-based filtering controls
        
        Returns:
            Bokeh Column with relationship filter controls
        """
        # Get relationship types
        rel_types = self._get_relationship_types()
        
        rel_type_multiselect = MultiSelect(
            title="Show Relationship Types:",
            value=list(rel_types),
            options=list(rel_types),
            height=120,
            width=300
        )
        
        # Degree filtering
        min_degree_slider = Slider(
            title="Minimum Node Degree:",
            start=0,
            end=self._get_max_degree(),
            value=0,
            step=1,
            width=300
        )
        
        max_degree_slider = Slider(
            title="Maximum Node Degree:",
            start=0,
            end=self._get_max_degree(),
            value=self._get_max_degree(),
            step=1,
            width=300
        )
        
        apply_rel_button = Button(
            label="Apply Relationship Filter",
            button_type="primary",
            width=300
        )
        
        def apply_relationship_filter():
            """Apply relationship-based filter"""
            selected_rel_types = set(rel_type_multiselect.value)
            min_degree = int(min_degree_slider.value)
            max_degree = int(max_degree_slider.value)
            
            self._apply_relationship_filter(selected_rel_types, min_degree, max_degree)
            self.active_filters['relationships'] = {
                'types': selected_rel_types,
                'min_degree': min_degree,
                'max_degree': max_degree
            }
        
        apply_rel_button.on_click(apply_relationship_filter)
        
        # Create layout
        controls = column(
            Div(text="<h3>Filter by Relationships</h3>"),
            rel_type_multiselect,
            min_degree_slider,
            max_degree_slider,
            apply_rel_button,
            width=300
        )
        
        return controls
    
    def create_filter_summary(self) -> Column:
        """
        Create a summary of active filters with clear options
        
        Returns:
            Bokeh Column showing active filters
        """
        summary_div = Div(
            text="<h3>Active Filters</h3><p>No filters applied</p>",
            width=300,
            height=150
        )
        
        clear_all_button = Button(
            label="Clear All Filters",
            button_type="warning",
            width=300
        )
        
        export_filtered_button = Button(
            label="Export Filtered Data",
            button_type="success",
            width=300
        )
        
        def clear_all_filters():
            """Clear all active filters"""
            self.active_filters.clear()
            self._reset_visualization()
            self._update_filter_summary(summary_div)
        
        def export_filtered_data():
            """Export currently visible/filtered data"""
            visible_nodes = self._get_visible_nodes()
            print(f"Would export {len(visible_nodes)} filtered nodes")
            # Implementation would depend on desired export format
        
        clear_all_button.on_click(clear_all_filters)
        export_filtered_button.on_click(export_filtered_data)
        
        # Initialize summary
        self._update_filter_summary(summary_div)
        
        # Create layout
        controls = column(
            summary_div,
            clear_all_button,
            export_filtered_button,
            width=300
        )
        
        return controls
    
    def _apply_node_type_filter(self, selected_types: set):
        """Apply node type filter to visualization"""
        if not self.graph_renderer:
            return
        
        node_colors = []
        node_sizes = []
        
        for i, node in enumerate(self.graph_plotter.G.nodes()):
            node_type