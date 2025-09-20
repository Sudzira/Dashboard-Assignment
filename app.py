"""
Main Application File
Integrates all components for Neo4j Graph Visualization
"""

from bokeh.io import curdoc, show
from bokeh.layouts import column, row, layout
from bokeh.models import Div, Tabs, Panel, Button
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler

import os
import sys
from typing import Optional

# Import custom modules
from connect_to_neo4j import create_neo4j_connection, Neo4jConnection
from fetch_graph_data import create_graph_data_fetcher, GraphDataFetcher
from graph_plotting import GraphPlotter
from search_function import GraphSearchInterface
from filter_function import GraphFilterInterface, AdvancedFilterInterface


class Neo4jGraphApp:
    def __init__(self):
        """Initialize the Neo4j Graph Visualization Application"""
        self.connection: Optional[Neo4jConnection] = None
        self.data_fetcher: Optional[GraphDataFetcher] = None
        self.graph_data: Optional[dict] = None
        self.graph_plotter: Optional[GraphPlotter] = None
        self.search_interface: Optional[GraphSearchInterface] = None
        self.filter_interface: Optional[GraphFilterInterface] = None
        self.advanced_filter: Optional[AdvancedFilterInterface] = None
        
        # UI components
        self.main_plot = None
        self.graph_renderer = None
        
    def initialize_connection(self) -> bool:
        """
        Initialize Neo4j connection using environment variables or defaults
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Get connection parameters from environment or use defaults
            uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
            user = os.getenv('NEO4J_USER', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', '')
            
            if not password:
                print("Warning: No password provided. Set NEO4J_PASSWORD environment variable.")
                return False
            
            self.connection = create_neo4j_connection(uri, user, password)
            
            if not self.connection or not self.connection.driver:
                print("Failed to establish Neo4j connection")
                return False
            
            # Test connection
            if not self.connection.test_connection():
                return False
            
            print("Neo4j connection established successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing connection: {str(e)}")
            return False
    
    def load_data(self, use_limited: bool = False, limit: int = 500) -> bool:
        """
        Load graph data from Neo4j
        
        Args:
            use_limited: Whether to load limited data for testing
            limit: Number of nodes to limit to if use_limited is True
            
        Returns:
            bool: True if data loaded successfully
        """
        try:
            if not self.connection:
                print("No active Neo4j connection")
                return False
            
            self.data_fetcher = create_graph_data_fetcher(self.connection)
            
            if use_limited:
                self.graph_data = self.data_fetcher.get_limited_graph_data(limit)
                print(f"Loaded limited data ({limit} nodes)")
            else:
                self.graph_data = self.data_fetcher.get_all_graph_data()
                print("Loaded all graph data")
            
            if not self.graph_data:
                print("Failed to load graph data")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def create_visualization(self) -> bool:
        """
        Create the main graph visualization
        
        Returns:
            bool: True if visualization created successfully
        """
        try:
            if not self.graph_data:
                print("No graph data available")
                return False
            
            # Create graph plotter
            self.graph_plotter = GraphPlotter(self.graph_data)
            
            # Create main visualization
            self.main_plot, self.graph_renderer = self.graph_plotter.create_visualization(
                width=1000, height=700, title="Neo4j Graph Visualization"
            )
            
            # Create search interface
            self.search_interface = GraphSearchInterface(
                self.graph_data, self.graph_plotter, self.data_fetcher
            )
            
            # Create filter interface
            self.filter_interface = GraphFilterInterface(
                self.graph_data, self.graph_plotter, self.graph_renderer
            )
            
            # Create advanced filter interface
            self.advanced_filter = AdvancedFilterInterface(self.filter_interface)
            
            print("Visualization components created successfully")
            return True
            
        except Exception as e:
            print(f"Error creating visualization: {str(e)}")
            return False
    
    def create_layout(self):
        """
        Create the complete Bokeh layout with tabs
        
        Returns:
            Bokeh layout object
        """
        if not all([self.main_plot, self.search_interface, self.filter_interface]):
            print("Visualization components not initialized")
            return None
        
        # Create header
        header = Div(
            text="""
            <div style="text-align: center; background: #f0f0f0; padding: 20px; margin-bottom: 10px; border-radius: 5px;">
                <h1 style="margin: 0; color: #333;">Neo4j Graph Visualization</h1>
                <p style="margin: 5px 0 0 0; color: #666;">Interactive exploration of graph database</p>
            </div>
            """,
            width=1300,
            height=80
        )
        
        # Create main visualization panel
        main_panel_content = row(
            self.main_plot,
            column(
                self.search_interface.create_text_search_controls(),
                Div(text="<br>"),
                self.search_interface.create_pattern_search_controls(),
                width=320
            )
        )
        
        main_panel = Panel(child=main_panel_content, title="Main Visualization")
        
        # Create filter panel
        filter_controls = row(
            self.main_plot,
            column(
                self.filter_interface.create_node_type_filter(),
                Div(text="<br>"),
                self.filter_interface.create_property_range_filter(),
                width=320
            )
        )
        
        filter_panel = Panel(child=filter_controls, title="Filters")
        
        # Create advanced search panel
        advanced_controls = row(
            self.main_plot,
            column(
                self.search_interface.create_advanced_search_controls(),
                Div(text="<br>"),
                self.filter_interface.create_text_property_filter(),
                width=320
            )
        )
        
        advanced_panel = Panel(child=advanced_controls, title="Advanced Search")
        
        # Create statistics panel
        stats_content = self._create_statistics_panel()
        stats_panel = Panel(child=stats_content, title="Statistics")
        
        # Create tabs
        tabs = Tabs(tabs=[main_panel, filter_panel, advanced_panel, stats_panel])
        
        # Create final layout
        final_layout = column(
            header,
            tabs,
            sizing_mode="scale_width"
        )
        
        return final_layout
    
    def _create_statistics_panel(self):
        """Create a statistics panel showing graph metrics"""
        if not self.graph_plotter:
            return Div(text="<p>No statistics available</p>")
        
        # Get statistics
        stats = self.graph_plotter.get_graph_statistics()
        
        # Format statistics HTML
        stats_html = """
        <div style="padding: 20px;">
            <h2>Graph Statistics</h2>
            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; min-width: 200px;">
                    <h3>Overview</h3>
                    <ul>
                        <li><strong>Total Nodes:</strong> {total_nodes}</li>
                        <li><strong>Total Edges:</strong> {total_edges}</li>
                        <li><strong>Graph Density:</strong> {density:.4f}</li>
                        <li><strong>Connected:</strong> {is_connected}</li>
                    </ul>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; min-width: 200px;">
                    <h3>Node Types</h3>
                    <ul>
        """.format(**stats)
        
        for node_type, count in stats.get('node_types', {}).items():
            stats_html += f"<li><strong>{node_type}:</strong> {count}</li>"
        
        stats_html += """
                    </ul>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; min-width: 200px;">
                    <h3>Relationship Types</h3>
                    <ul>
        """
        
        for edge_type, count in stats.get('edge_types', {}).items():
            stats_html += f"<li><strong>{edge_type}:</strong> {count}</li>"
        
        stats_html += """
                    </ul>
                </div>
            </div>
        </div>
        """
        
        stats_div = Div(text=stats_html, width=1000)
        
        # Add refresh button
        refresh_button = Button(label="Refresh Statistics", button_type="primary")
        
        def refresh_stats():
            updated_stats = self.graph_plotter.get_graph_statistics()
            # Update the stats display (simplified)
            print("Statistics refreshed")
        
        refresh_button.on_click(refresh_stats)
        
        return column(stats_div, refresh_button)
    
    def run_server(self, port: int = 5006, show_browser: bool = True):
        """
        Run the Bokeh server application
        
        Args:
            port: Port to run the server on
            show_browser: Whether to automatically open browser
        """
        def create_app(doc):
            """Create the Bokeh application"""
            if not self.initialize_connection():
                error_div = Div(text="""
                    <div style="color: red; padding: 20px; text-align: center;">
                        <h2>Connection Error</h2>
                        <p>Could not connect to Neo4j database.</p>
                        <p>Please check your connection settings and ensure Neo4j is running.</p>
                    </div>
                """)
                doc.add_root(error_div)
                return
            
            if not self.load_data(use_limited=False):
                error_div = Div(text="""
                    <div style="color: red; padding: 20px; text-align: center;">
                        <h2>Data Loading Error</h2>
                        <p>Could not load data from Neo4j database.</p>
                        <p>Please check your database contains data.</p>
                    </div>
                """)
                doc.add_root(error_div)
                return
            
            if not self.create_visualization():
                error_div = Div(text="""
                    <div style="color: red; padding: 20px; text-align: center;">
                        <h2>Visualization Error</h2>
                        <p>Could not create graph visualization.</p>
                    </div>
                """)
                doc.add_root(error_div)
                return
            
            # Create and add layout
            app_layout = self.create_layout()
            if app_layout:
                doc.add_root(app_layout)
                doc.title = "Neo4j Graph Visualization"
            else:
                error_div = Div(text="<p>Error creating application layout</p>")
                doc.add_root(error_div)
        
        # Create and run server
        app = Application(FunctionHandler(create_app))
        server = Server({'/': app}, port=port)
        
        print(f"Starting Bokeh server on port {port}...")
        server.start()
        
        if show_browser:
            print(f"Opening browser at http://localhost:{port}")
            server.io_loop.add_callback(server.show, "/")
        
        print("Press Ctrl+C to stop the server")
        server.io_loop.start()
    
    def export_static_html(self, filename: str = "neo4j_graph_viz.html"):
        """
        Export a static HTML version of the visualization
        
        Args:
            filename: Output filename
        """
        from bokeh.io import output_file, save
        
        try:
            if not self.initialize_connection():
                print("Could not connect to database")
                return False
            
            if not self.load_data(use_limited=True, limit=200):  # Use limited data for static export
                print("Could not load data")
                return False
            
            if not self.create_visualization():
                print("Could not create visualization")
                return False
            
            # Create simplified layout for static export
            simple_layout = row(
                self.main_plot,
                column(
                    Div(text="<h3>Neo4j Graph Visualization</h3>"),
                    Div(text="<p>Static export - interactive features limited</p>"),
                    width=300
                )
            )
            
            # Save to HTML
            output_file(filename, title="Neo4j Graph Visualization")
            save(simple_layout)
            
            print(f"Static visualization exported to {filename}")
            return True
            
        except Exception as e:
            print(f"Error exporting static HTML: {str(e)}")
            return False
        finally:
            if self.connection:
                self.connection.close()
    
    def cleanup(self):
        """Clean up resources"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")


def main():
    """Main entry point"""
    app = Neo4jGraphApp()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'static':
            # Export static HTML
            filename = sys.argv[2] if len(sys.argv) > 2 else "neo4j_graph_viz.html"
            app.export_static_html(filename)
        elif command == 'server':
            # Run server
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 5006
            try:
                app.run_server(port=port)
            except KeyboardInterrupt:
                print("\nShutting down server...")
            finally:
                app.cleanup()
        else:
            print("Usage: python app.py [static|server] [filename|port]")
    else:
        # Default to running server
        try:
            app.run_server()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            app.cleanup()


if __name__ == "__main__":
    main()
