from bokeh.io import curdoc

# Required libraries: neo4j, bokeh, pandas
# Install with: pip install neo4j bokeh pandas numpy

from neo4j import GraphDatabase
from bokeh.io import curdoc, output_file, save, show  # Added output_file, save
from bokeh.models import (BoxZoomTool, Circle, ColumnDataSource, CustomJS,
                          HoverTool, MultiLine, NodesAndLinkedEdges, Plot,
                          Range1d, TapTool, Text, WheelZoomTool, 
                          Button, TextInput, Select, Div, Slider, RadioButtonGroup)
from bokeh.models.graphs import NodesOnly
from bokeh.plotting import figure, show, from_networkx  # from_networkx is now in bokeh.plotting
from bokeh.palettes import Category20, Spectral4
from bokeh.layouts import column, row, layout
from bokeh.transform import linear_cmap
import networkx as nx
import pandas as pd
import numpy as np

def connect_to_neo4j(uri, user, password):
    """
    Creates a Neo4j database connection.
    Returns the driver object if successful, None if connection fails.
    """
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        print("Connection successful!")
        return driver
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return None

def execute_query(driver, query, parameters=None):
    """
    Executes a Neo4j query and returns the results.
    """
    if not driver:
        print("No active connection!")
        return None
    
    try:
        with driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]
    except Exception as e:
        print(f"Query failed: {str(e)}")
        return None

# Connection details
uri = "neo4j://127.0.0.1:7687"
user = "neo4j"
password = "vLAhHDOb5PCxsCv9ejXjNO64i5kkT9WVTgpYaJ-fAMA"

# Create connection
neo4j_driver = connect_to_neo4j(uri, user, password)

# Test query
if neo4j_driver:
    test_result = execute_query(neo4j_driver, "RETURN 'Test query successful' as message")
    if test_result:
        print(test_result[0]["message"])

def get_graph_data(driver):
    """
    Retrieves ALL nodes and relationships from Neo4j database with their properties.
    Uses two separate queries to ensure we get both isolated nodes and connected nodes.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dictionary containing nodes and relationships data
    """
    # First query: Get ALL nodes (including isolated ones)
    nodes_query = """
    MATCH (n)
    RETURN collect({
        id: elementId(n),
        labels: labels(n),
        properties: properties(n)
    }) as nodes
    """
    
    # Second query: Get ALL relationships
    relationships_query = """
    MATCH (n)-[r]->(m)
    RETURN collect({
        id: elementId(r),
        type: type(r),
        properties: properties(r),
        start_node: elementId(startNode(r)),
        end_node: elementId(endNode(r))
    }) as relationships
    """
    
    try:
        # Execute nodes query
        nodes_result = execute_query(driver, nodes_query)
        
        # Execute relationships query
        relationships_result = execute_query(driver, relationships_query)
        
        if not nodes_result or not relationships_result:
            print("Error retrieving data from database")
            return None
            
        # Process nodes
        node_data = {}
        for node in nodes_result[0]["nodes"]:
            node_data[node["id"]] = {
                "labels": node["labels"],
                "properties": node["properties"]
            }
            
        # Process relationships
        rel_data = {}
        for rel in relationships_result[0]["relationships"]:  # Fixed: using relationships_result instead of result
            rel_data[rel["id"]] = {
                "type": rel["type"],
                "properties": rel["properties"],
                "start_node": rel["start_node"],
                "end_node": rel["end_node"]
            }
            
        # Print summary
        print(f"Retrieved {len(node_data)} nodes and {len(rel_data)} relationships")
        
        # Print node types and their counts
        node_types = {}
        for node in node_data.values():
            for label in node["labels"]:
                node_types[label] = node_types.get(label, 0) + 1
        
        print("\nNode types:")
        for label, count in node_types.items():
            print(f"- {label}: {count} nodes")
            
        # Print relationship types and their counts
        rel_types = {}
        for rel in rel_data.values():
            rel_types[rel["type"]] = rel_types.get(rel["type"], 0) + 1
            
        print("\nRelationship types:")
        for rel_type, count in rel_types.items():
            print(f"- {rel_type}: {count} relationships")
        
        return {
            "nodes": node_data,
            "relationships": rel_data
        }
        
    except Exception as e:
        print(f"Error retrieving graph data: {str(e)}")
        return None

# Get ALL graph data using the active driver
graph_data = get_graph_data(neo4j_driver)  # Note: no limit parameter anymore as we get all data

# Example of how to access specific node or relationship data
if graph_data:
    # Get first node as an example
    if graph_data["nodes"]:
        first_node_id = list(graph_data["nodes"].keys())[0]
        first_node = graph_data["nodes"][first_node_id]
        print("\nExample node:")
        print(f"Labels: {first_node['labels']}")
        print(f"Properties: {first_node['properties']}")
    
    # Get first relationship as an example
    if graph_data["relationships"]:
        first_rel_id = list(graph_data["relationships"].keys())[0]
        first_rel = graph_data["relationships"][first_rel_id]
        print("\nExample relationship:")
        print(f"Type: {first_rel['type']}")
        print(f"Properties: {first_rel['properties']}")
        print(f"From node {first_rel['start_node']} to node {first_rel['end_node']}")

def create_graph_visualization(graph_data):
    """
    Creates an interactive graph visualization using Bokeh.
    """
    # Create NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes with their properties
    for node_id, node_info in graph_data["nodes"].items():
        # Create a properties dictionary with the label
        node_props = {
            "label": node_info["labels"][0] if node_info["labels"] else "Unknown",
            "type": node_info["labels"][0] if node_info["labels"] else "Unknown"
        }
        # Add other properties from the node
        node_props.update(node_info["properties"])
        # Add node to graph
        G.add_node(node_id, **node_props)
    
    # Add relationships
    for rel_id, rel_info in graph_data["relationships"].items():
        G.add_edge(rel_info["start_node"], 
                  rel_info["end_node"], 
                  type=rel_info["type"],
                  **rel_info.get("properties", {}))
    
    # Create Bokeh plot
    plot = figure(width=1200, height=800, 
                 title="Neo4j Graph Visualization",
                 tools="pan,wheel_zoom,box_zoom,reset,save,tap",
                 active_scroll='wheel_zoom')
    
    # Create layout with much more spread and prevent overlap
    layout = nx.spring_layout(G, k=5, iterations=100, scale=4)
    
    # Create NetworkX graph renderer
    graph_renderer = from_networkx(G, layout)
    
    # Configure node appearance
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        node_type = G.nodes[node].get("type", "Unknown")
        # Color and size nodes by type
        if node_type == "Movie":
            node_colors.append("#3182bd")  # Blue
            node_sizes.append(10)
        elif node_type == "Person":
            node_colors.append("#31a354")  # Green
            node_sizes.append(8)
        elif node_type == "Genre":
            node_colors.append("#e6550d")  # Orange
            node_sizes.append(6)
        else:
            node_colors.append("#756bb1")  # Purple
            node_sizes.append(5)
    
    # Update node renderer with data
    node_data = {
        'index': list(G.nodes()),
        'color': node_colors,
        'radius': node_sizes,  # Changed from 'size' to 'radius'
        'type': [G.nodes[node].get("type", "Unknown") for node in G.nodes()],
        'name': [G.nodes[node].get("name", "Unnamed") for node in G.nodes()],
        'properties': [str({k:v for k,v in G.nodes[node].items() if k not in ['type', 'name']}) 
                      for node in G.nodes()]
    }
    graph_renderer.node_renderer.data_source.data.update(node_data)
    
    # Style nodes - using 'radius' instead of 'size'
    graph_renderer.node_renderer.glyph = Circle(
        radius='radius',  # Changed from 'size' to 'radius'
        fill_color='color',
        fill_alpha=0.8,
        line_color='black',
        line_width=1
    )
    
    # Style edges
    graph_renderer.edge_renderer.glyph = MultiLine(
        line_color="#CCCCCC",
        line_alpha=0.5,
        line_width=1
    )
    
    # Add hover tooltips
    node_hover = HoverTool(tooltips=[
        ("Type", "@type"),
        ("Name", "@name"),
        ("Properties", "@properties")
    ], renderers=[graph_renderer.node_renderer])
    
    plot.add_tools(node_hover)
    
    # Add graph to plot
    plot.renderers.append(graph_renderer)
    
    # Style the plot
    plot.axis.visible = False
    plot.grid.visible = False
    plot.outline_line_color = None
    
    return plot, G, graph_renderer

# Create visualization
if graph_data:
    plot, G, graph_renderer = create_graph_visualization(graph_data)
    
    # Create interactive components
    search_input = TextInput(title="Search Nodes:", placeholder="Enter node name...")
    reset_button = Button(label="Reset View", button_type="warning")
    
    def search_nodes(attr, old, new):
        search_term = search_input.value.lower()
        if not search_term:
            return
            
        node_colors = graph_renderer.node_renderer.data_source.data['color']
        original_colors = node_colors.copy()
        
        for i, node in enumerate(G.nodes()):
            node_data = G.nodes[node]
            # Search in all node properties
            found = any(
                str(value).lower().find(search_term) >= 0 
                for value in node_data.values() 
                if isinstance(value, (str, int, float))
            )
            
            if found:
                node_colors[i] = "#FFD700"  # Gold color for matches
            else:
                node_colors[i] = original_colors[i]
                
        graph_renderer.node_renderer.data_source.data['color'] = node_colors
    
    search_input.on_change('value', search_nodes)
    
    def reset_view():
        # Reset node colors based on type
        node_colors = []
        for node in G.nodes():
            node_type = G.nodes[node].get("type", "Unknown")
            if node_type == "Movie":
                node_colors.append("#3182bd")
            elif node_type == "Person":
                node_colors.append("#31a354")
            elif node_type == "Genre":
                node_colors.append("#e6550d")
            else:
                node_colors.append("#756bb1")
        graph_renderer.node_renderer.data_source.data['color'] = node_colors
    
    reset_button.on_click(reset_view)
    
    # Create layout
    controls = column(
        search_input,
        reset_button,
        width=300
    )
    final_layout = row(plot, controls)
    
    # Save to HTML
    output_file("neo4j_graph_viz.html", title="Neo4j Graph Visualization")
    save(final_layout)
else:
    print("No graph data available to visualize")

# Create and handle pattern search functionality
def create_pattern_search(graph_data):
    """
    Creates a complete pattern search interface with dropdowns and search button.
    Includes relationship exploration and pattern visualization functionality.
    """
    # Get unique node types and relationship types
    node_types = set()
    rel_types = set()
    
    # Process nodes and relationships to get types
    for node_info in graph_data["nodes"].values():
        node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
        node_types.add(node_type)
    
    for rel_info in graph_data["relationships"].values():
        rel_types.add(rel_info["type"])
    
    # Create dropdowns
    dropdown_A = Select(
        title="Node Type A:",
        options=sorted(list(node_types)),
        value=sorted(list(node_types))[0] if node_types else None
    )
    
    dropdown_B = Select(
        title="Relationship Type:",
        options=sorted(list(rel_types)),
        value=sorted(list(rel_types))[0] if rel_types else None
    )
    
    dropdown_C = Select(
        title="Node Type B:",
        options=sorted(list(node_types)),
        value=sorted(list(node_types))[0] if node_types else None
    )
    
    # Create search button
    search_button = Button(label="Search Pattern", button_type="success")
    
    def create_pattern_visualization(type_a, rel_type, type_b):
        """Create a new visualization for the selected pattern"""
        # Create a subgraph with matching pattern
        pattern_G = nx.DiGraph()
        
        # Find matching nodes and relationships
        matching_nodes_a = []
        matching_nodes_b = []
        matching_relationships = []
        
        # Find matching nodes
        for node_id, node_info in graph_data["nodes"].items():
            node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
            if node_type == type_a:
                matching_nodes_a.append(node_id)
            elif node_type == type_b:
                matching_nodes_b.append(node_id)
        
        # Find matching relationships
        for rel_id, rel_info in graph_data["relationships"].items():
            if rel_info["type"] == rel_type:
                start_node = rel_info["start_node"]
                end_node = rel_info["end_node"]
                if start_node in matching_nodes_a and end_node in matching_nodes_b:
                    matching_relationships.append((start_node, end_node, rel_info))
        
        # Add nodes to pattern graph
        for node_id in set(matching_nodes_a + matching_nodes_b):
            node_info = graph_data["nodes"][node_id]
            node_props = {
                "label": node_info["labels"][0] if node_info["labels"] else "Unknown",
                "type": node_info["labels"][0] if node_info["labels"] else "Unknown"
            }
            node_props.update(node_info["properties"])
            pattern_G.add_node(node_id, **node_props)
        
        # Add relationships
        for start_node, end_node, rel_info in matching_relationships:
            pattern_G.add_edge(start_node, end_node, 
                             type=rel_info["type"],
                             **rel_info.get("properties", {}))
        
        return pattern_G, matching_nodes_a, matching_nodes_b, matching_relationships
    
    def create_visualization_plot(pattern_G, type_a, type_b):
        """Create the Bokeh plot for the pattern graph"""
        plot = figure(width=800, height=600, 
                     title=f"Pattern: {type_a}-[{dropdown_B.value}]->{type_b}",
                     tools="pan,wheel_zoom,box_zoom,reset,save",
                     active_scroll='wheel_zoom')
        
        # Create layout with more spread
        layout = nx.spring_layout(pattern_G, k=2, iterations=100)
        graph_renderer = from_networkx(pattern_G, layout)
        
        # Configure node appearance
        node_colors = ["#FFD700" if pattern_G.nodes[node]["type"] == type_a else 
                      "#FF6B6B" if pattern_G.nodes[node]["type"] == type_b else "#CCCCCC" 
                      for node in pattern_G.nodes()]
        node_sizes = [15 if pattern_G.nodes[node]["type"] in [type_a, type_b] else 10 
                     for node in pattern_G.nodes()]
        
        # Update node renderer
        node_data = {
            'index': list(pattern_G.nodes()),
            'color': node_colors,
            'radius': node_sizes,
            'type': [pattern_G.nodes[node]["type"] for node in pattern_G.nodes()],
            'name': [pattern_G.nodes[node].get("name", "Unnamed") for node in pattern_G.nodes()],
            'properties': [str({k:v for k,v in pattern_G.nodes[node].items() 
                              if k not in ['type', 'name']}) for node in pattern_G.nodes()]
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
            line_color="#FF1493",
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
        
        return plot, graph_renderer
    
    def search_pattern():
        """Handle pattern search button click"""
        # Get selected values
        type_a = dropdown_A.value
        rel_type = dropdown_B.value
        type_b = dropdown_C.value
        
        if not all([type_a, rel_type, type_b]):
            print("Please select values in all dropdowns")
            return
        
        # Create pattern graph and get statistics
        pattern_G, matching_nodes_a, matching_nodes_b, matching_relationships = \
            create_pattern_visualization(type_a, rel_type, type_b)
        
        # Create visualization
        plot, graph_renderer = create_visualization_plot(pattern_G, type_a, type_b)
        
        # Create stats text
        stats_text = f"""
        Pattern Statistics:
        - {type_a} nodes: {len(matching_nodes_a)}
        - {type_b} nodes: {len(matching_nodes_b)}
        - {rel_type} relationships: {len(matching_relationships)}
        """
        stats_div = Div(text=f"<pre>{stats_text}</pre>", width=400)
        
        # Add property exploration and filter controls
        property_controls = create_property_exploration_dropdowns(graph_data, pattern_G)
        filter_controls = create_property_filter(graph_data, pattern_G, property_controls)
        
        # Create complete layout
        final_layout = row(
            column(plot, stats_div),
            column(
                property_controls,
                Div(text="<br>"),
                filter_controls
            )
        )
        
        # Save to HTML
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file(f"pattern_search_{timestamp}.html", 
                   title=f"Pattern: {type_a}-[{rel_type}]->{type_b}")
        save(final_layout)
        
        print(f"Pattern visualization saved to pattern_search_{timestamp}.html")
    
    # Add click handler to search button
    search_button.on_click(search_pattern)
    
    # Create layout for pattern search controls
    pattern_controls = column(
        Div(text="<h3>Explore Relationships</h3>"),
        dropdown_A,
        dropdown_B,
        dropdown_C,
        Div(text="<br>"),
        search_button,
        width=300
    )
    
    return pattern_controls, search_button

# Create visualization and controls
if graph_data:
    # Create a new document
    from bokeh.document import Document
    doc = Document()
    
    # Create main visualization
    plot, G, graph_renderer = create_graph_visualization(graph_data)
    
    # Create search components
    search_input = TextInput(title="Search Nodes:", placeholder="Enter node name...")
    reset_button = Button(label="Reset View", button_type="warning")
    
    def search_nodes(attr, old, new):
        search_term = search_input.value.lower()
        if not search_term:
            return
        
        node_colors = []
        for node in G.nodes():
            node_data = G.nodes[node]
            found = any(
                str(value).lower().find(search_term) >= 0 
                for value in node_data.values() 
                if isinstance(value, (str, int, float))
            )
            node_type = node_data.get("type", "Unknown")
            if found:
                node_colors.append("#FFD700")
            else:
                if node_type == "Movie":
                    node_colors.append("#3182bd")
                elif node_type == "Person":
                    node_colors.append("#31a354")
                elif node_type == "Genre":
                    node_colors.append("#e6550d")
                else:
                    node_colors.append("#756bb1")
        
        graph_renderer.node_renderer.data_source.data['color'] = node_colors
    
    search_input.on_change('value', search_nodes)
    
    def reset_view():
        node_colors = []
        for node in G.nodes():
            node_type = G.nodes[node].get("type", "Unknown")
            if node_type == "Movie":
                node_colors.append("#3182bd")
            elif node_type == "Person":
                node_colors.append("#31a354")
            elif node_type == "Genre":
                node_colors.append("#e6550d")
            else:
                node_colors.append("#756bb1")
        graph_renderer.node_renderer.data_source.data['color'] = node_colors
    
    reset_button.on_click(reset_view)
    
    # Create pattern search controls
    pattern_controls, pattern_search_button = create_pattern_search(graph_data)
    
    # Create main layout
    controls = column(
        search_input,
        Div(text="<br>"),
        pattern_controls,
        Div(text="<br>"),
        reset_button,
        width=300
    )
    
    final_layout = row(plot, controls)
    
    # Add layout to document and save
    doc.add_root(final_layout)
    output_file("neo4j_graph_viz.html", title="Neo4j Graph Visualization")
    save(doc)

# Create property exploration and filtering functionality
def create_property_controls(graph_data, pattern_G):
    """
    Creates an integrated interface for exploring and filtering node properties
    Combines property exploration dropdowns with filtering capabilities
    """
    # Get unique node types and their properties
    node_types = set()
    node_properties = {}
    
    # Process nodes to get types and their properties
    for node_id in pattern_G.nodes():
        node_info = graph_data["nodes"][node_id]
        node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
        node_types.add(node_type)
        
        # Initialize properties set for this node type
        if node_type not in node_properties:
            node_properties[node_type] = set()
        
        # Add all properties from this node
        node_properties[node_type].update(node_info["properties"].keys())
    
    # Create dropdowns
    node_type_dropdown = Select(
        title="Select Node Type:",
        options=sorted(list(node_types)),
        value=sorted(list(node_types))[0] if node_types else None,
        width=300
    )
    
    initial_properties = sorted(list(node_properties[node_type_dropdown.value])) if node_types else []
    property_dropdown = Select(
        title="Select Property:",
        options=initial_properties,
        value=initial_properties[0] if initial_properties else None,
        width=300
    )
    
    # Create filter components
    filter_input = TextInput(
        title="Filter Condition:",
        placeholder="E.g.: > 1990 or == 'Drama' or contains 'Action'",
        width=300
    )
    
    filter_button = Button(label="Apply Filter", button_type="primary", width=300)
    
    def update_property_options(attr, old, new):
        """Update property dropdown when node type changes"""
        if new in node_properties:
            property_dropdown.options = sorted(list(node_properties[new]))
            property_dropdown.value = property_dropdown.options[0] if property_dropdown.options else None
    
    def parse_filter_condition(value_str, filter_str):
        """Parse and evaluate filter conditions"""
        filter_str = filter_str.strip().lower()
        
        # String contains
        if "contains" in filter_str:
            search_term = filter_str.split("contains")[1].strip().strip("'\"")
            return isinstance(value_str, str) and search_term.lower() in str(value_str).lower()
        
        # Equality
        if "==" in filter_str:
            compare_value = filter_str.split("==")[1].strip().strip("'\"")
            try:
                if compare_value.isdigit():
                    return float(value_str) == float(compare_value)
                return str(value_str).lower() == compare_value.lower()
            except:
                return False
        
        # Numeric comparisons
        try:
            value = float(value_str)
            if ">" in filter_str:
                return value > float(filter_str.split(">")[1].strip())
            elif "<" in filter_str:
                return value < float(filter_str.split("<")[1].strip())
            elif ">=" in filter_str:
                return value >= float(filter_str.split(">=")[1].strip())
            elif "<=" in filter_str:
                return value <= float(filter_str.split("<=")[1].strip())
        except:
            return False
        
        return True
    
    def apply_filter():
        """Apply property filter to visualization"""
        selected_type = node_type_dropdown.value
        selected_property = property_dropdown.value
        filter_condition = filter_input.value
        
        if not all([selected_type, selected_property, filter_condition]):
            print("Please select a node type, property, and enter a filter condition")
            return
        
        # Track nodes and update visualization
        matching_nodes = set()
        node_colors = []
        node_sizes = []
        properties_list = []
        
        # Process nodes
        for node in pattern_G.nodes():
            node_info = graph_data["nodes"][node]
            node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
            property_value = node_info["properties"].get(selected_property, None)
            
            # Determine if node matches filter
            matches_filter = (
                node_type == selected_type and 
                property_value is not None and 
                parse_filter_condition(property_value, filter_condition)
            )
            
            if matches_filter:
                node_colors.append("#FFD700")  # Gold for matches
                node_sizes.append(20)
                matching_nodes.add(node)
            else:
                node_colors.append("#CCCCCC")  # Gray for non-matches
                node_sizes.append(10)
            
            # Add property value to tooltip
            properties_list.append(
                f"{selected_property}: {property_value}" if property_value is not None else ""
            )
        
        # Update edges based on matching nodes
        edge_colors = []
        edge_widths = []
        
        for edge in pattern_G.edges():
            if edge[0] in matching_nodes and edge[1] in matching_nodes:
                edge_colors.append("#FF1493")  # Pink for connected matches
                edge_widths.append(2)
            else:
                edge_colors.append("#CCCCCC")  # Gray for others
                edge_widths.append(1)
        
        # Update visualization
        graph_renderer.node_renderer.data_source.data.update({
            'color': node_colors,
            'radius': node_sizes,
            'property_value': properties_list
        })
        
        graph_renderer.edge_renderer.glyph = MultiLine(
            line_color=edge_colors,
            line_alpha=0.8,
            line_width=edge_widths
        )
        
        # Print summary
        print(f"Filter applied: {len(matching_nodes)} out of {len(pattern_G.nodes())} nodes match the condition")
    
    # Add callbacks
    node_type_dropdown.on_change('value', update_property_options)
    filter_button.on_click(apply_filter)
    
    # Create layout
    controls = column(
        Div(text="<h3>Explore and Filter Properties</h3>"),
        node_type_dropdown,
        property_dropdown,
        Div(text="<br>"),
        Div(text="<strong>Filter nodes by property value:</strong>"),
        filter_input,
        filter_button,
        width=300
    )
    
    return controls

# Update the pattern search to use the combined property controls
def update_pattern_visualization():
    # ... (previous pattern search code) ...
    
    # Replace separate property controls with combined version
    property_controls = create_property_controls(graph_data, pattern_G)
    
    # Create layout
    final_layout = row(
        column(plot, stats_div),
        property_controls
    )
    
    # ... (rest of visualization code) ...

# Update the pattern search function to include property filters
def update_pattern_search():
    # Create the search button
    search_button = Button(label="Search Pattern", button_type="success")
    
    def search_pattern():
        # Get selected values
        type_a = dropdown_A.value
        rel_type = dropdown_B.value
        type_b = dropdown_C.value
        
        if not all([type_a, rel_type, type_b]):
            print("Please select values in all dropdowns")
            return
        
        # Create a new document for pattern visualization
        from bokeh.document import Document
        pattern_doc = Document()
        
        # Create a subgraph with matching pattern
        pattern_G = nx.DiGraph()
        
        # Find nodes and relationships matching the pattern
        matching_nodes_a = []
        matching_nodes_b = []
        matching_relationships = []
        
        # Find matching nodes of type A and B
        for node_id, node_info in graph_data["nodes"].items():
            node_type = node_info["labels"][0] if node_info["labels"] else "Unknown"
            if node_type == type_a:
                matching_nodes_a.append(node_id)
            elif node_type == type_b:
                matching_nodes_b.append(node_id)
        
        # Find relationships between matching nodes
        for rel_id, rel_info in graph_data["relationships"].items():
            if rel_info["type"] == rel_type:
                start_node = rel_info["start_node"]
                end_node = rel_info["end_node"]
                if start_node in matching_nodes_a and end_node in matching_nodes_b:
                    matching_relationships.append((start_node, end_node, rel_info))
        
        # Add matching nodes and relationships to the pattern graph
        for node_id in set(matching_nodes_a + matching_nodes_b):
            node_info = graph_data["nodes"][node_id]
            node_props = {
                "label": node_info["labels"][0] if node_info["labels"] else "Unknown",
                "type": node_info["labels"][0] if node_info["labels"] else "Unknown"
            }
            node_props.update(node_info["properties"])
            pattern_G.add_node(node_id, **node_props)
        
        # Add relationships
        for start_node, end_node, rel_info in matching_relationships:
            pattern_G.add_edge(start_node, end_node, 
                             type=rel_info["type"],
                             **rel_info.get("properties", {}))
        
        # Create visualization for pattern
        plot = figure(width=800, height=600, 
                     title=f"Pattern: {type_a}-[{rel_type}]->{type_b}",
                     tools="pan,wheel_zoom,box_zoom,reset,save",
                     active_scroll='wheel_zoom')
        
        # Create layout with more spread
        layout = nx.spring_layout(pattern_G, k=2, iterations=100)
        
        # Create NetworkX graph renderer
        graph_renderer = from_networkx(pattern_G, layout)
        
        # Configure node appearance
        node_colors = []
        node_sizes = []
        for node in pattern_G.nodes():
            node_type = pattern_G.nodes[node].get("type", "Unknown")
            if node_type == type_a:
                node_colors.append("#FFD700")  # Gold for type A
                node_sizes.append(15)
            elif node_type == type_b:
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
            'type': [pattern_G.nodes[node].get("type", "Unknown") for node in pattern_G.nodes()],
            'name': [pattern_G.nodes[node].get("name", "Unnamed") for node in pattern_G.nodes()],
            'properties': [str({k:v for k,v in pattern_G.nodes[node].items() if k not in ['type', 'name']}) 
                         for node in pattern_G.nodes()]
        }
        graph_renderer.node_renderer.data_source.data.update(node_data)
        
        # Style nodes
        graph_renderer.node_renderer.glyph = Circle(
            radius='radius',
            fill_color='color',
            fill_alpha=0.8,
            line_color='black',
            line_width=1
        )
        
        # Style edges
        graph_renderer.edge_renderer.glyph = MultiLine(
            line_color="#FF1493",  # Deep pink for relationships
            line_alpha=0.8,
            line_width=2
        )
        
        # Create stats text
        stats_text = f"""
        Pattern Statistics:
        - {type_a} nodes: {len(matching_nodes_a)}
        - {type_b} nodes: {len(matching_nodes_b)}
        - {rel_type} relationships: {len(matching_relationships)}
        """
        stats_div = Div(text=f"<pre>{stats_text}</pre>", width=400)
        
        # Add property exploration dropdowns
        property_controls = create_property_exploration_dropdowns(graph_data, pattern_G)
        
        # Add property filter controls
        filter_controls = create_property_filter(graph_data, pattern_G, property_controls)
        
        # Update hover tooltips to include property value
        node_hover = HoverTool(tooltips=[
            ("Type", "@type"),
            ("Name", "@name"),
            ("Selected Property", "@property_value"),
            ("All Properties", "@properties")
        ], renderers=[graph_renderer.node_renderer])
        
        # Add hover tool to plot
        plot.add_tools(node_hover)
        
        # Add graph to plot
        plot.renderers.append(graph_renderer)
        
        # Style the plot
        plot.axis.visible = False
        plot.grid.visible = False
        plot.outline_line_color = None
        
        # Create complete layout with property exploration and filtering
        controls_layout = column(
            property_controls,
            Div(text="<br>"),
            filter_controls
        )
        
        final_layout = row(
            column(plot, stats_div),
            controls_layout
        )
        
        # Save to HTML
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file(f"pattern_search_{timestamp}.html", 
                   title=f"Pattern: {type_a}-[{rel_type}]->{type_b}")
        save(final_layout)
        
        print(f"Pattern visualization saved to pattern_search_{timestamp}.html")
        
    # Add click handler to pattern search button
    search_button.on_click(search_pattern)
    
    return search_button

# Update the pattern search button creation
if graph_data:
    pattern_search_button = update_pattern_search()
    
    # Update the main visualization layout
    controls = column(
        search_input,
        Div(text="<br>"),
        relationship_dropdowns,
        pattern_search_button,
        Div(text="<br>"),
        reset_button,
        width=300
    )
    
    # Create final layout
    final_layout = row(plot, controls)
    
    # Add layout to document
    doc.add_root(final_layout)
    
    # Save to HTML
    output_file("neo4j_graph_viz.html", title="Neo4j Graph Visualization")
    save(doc)

    curdoc().add_root(final_layout)
