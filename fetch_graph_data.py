"""
Graph Data Fetching Module
Backend functionality to retrieve and process graph data from Neo4j
"""

from typing import Dict, List, Any, Optional
from connect_to_neo4j import Neo4jConnection


class GraphDataFetcher:
    def __init__(self, neo4j_connection: Neo4jConnection):
        """
        Initialize with Neo4j connection
        
        Args:
            neo4j_connection: Active Neo4j connection instance
        """
        self.connection = neo4j_connection
    
    def get_all_graph_data(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves ALL nodes and relationships from Neo4j database with their properties.
        Uses two separate queries to ensure we get both isolated nodes and connected nodes.
        
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
            nodes_result = self.connection.execute_query(nodes_query)
            
            # Execute relationships query
            relationships_result = self.connection.execute_query(relationships_query)
            
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
            for rel in relationships_result[0]["relationships"]:
                rel_data[rel["id"]] = {
                    "type": rel["type"],
                    "properties": rel["properties"],
                    "start_node": rel["start_node"],
                    "end_node": rel["end_node"]
                }
                
            # Print summary
            print(f"Retrieved {len(node_data)} nodes and {len(rel_data)} relationships")
            
            # Print node types and their counts
            node_types = self._get_node_type_counts(node_data)
            print("\nNode types:")
            for label, count in node_types.items():
                print(f"- {label}: {count} nodes")
                
            # Print relationship types and their counts
            rel_types = self._get_relationship_type_counts(rel_data)
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
    
    def get_limited_graph_data(self, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Retrieves a limited sample of nodes and relationships for testing/preview.
        
        Args:
            limit: Maximum number of nodes to retrieve
            
        Returns:
            Dictionary containing limited nodes and relationships data
        """
        # Query for limited nodes and their relationships
        limited_query = f"""
        MATCH (n)
        WITH n LIMIT {limit}
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN 
            collect(DISTINCT {{
                id: elementId(n),
                labels: labels(n),
                properties: properties(n)
            }}) as nodes,
            collect(DISTINCT {{
                id: elementId(r),
                type: type(r),
                properties: properties(r),
                start_node: elementId(startNode(r)),
                end_node: elementId(endNode(r))
            }}) as relationships
        """
        
        try:
            result = self.connection.execute_query(limited_query)
            if not result:
                return None
                
            # Process the combined result
            nodes_data = {}
            for node in result[0]["nodes"]:
                if node["id"]:  # Filter out null entries
                    nodes_data[node["id"]] = {
                        "labels": node["labels"],
                        "properties": node["properties"]
                    }
            
            rel_data = {}
            for rel in result[0]["relationships"]:
                if rel["id"]:  # Filter out null entries
                    rel_data[rel["id"]] = {
                        "type": rel["type"],
                        "properties": rel["properties"],
                        "start_node": rel["start_node"],
                        "end_node": rel["end_node"]
                    }
            
            print(f"Retrieved {len(nodes_data)} nodes and {len(rel_data)} relationships (limited)")
            
            return {
                "nodes": nodes_data,
                "relationships": rel_data
            }
            
        except Exception as e:
            print(f"Error retrieving limited graph data: {str(e)}")
            return None
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics about the graph without loading all data.
        
        Returns:
            Dictionary containing graph statistics
        """
        stats_query = """
        MATCH (n)
        WITH labels(n) as nodeLabels
        UNWIND nodeLabels as label
        WITH label, count(*) as nodeCount
        WITH collect({label: label, count: nodeCount}) as nodeStats
        
        MATCH ()-[r]->()
        WITH nodeStats, type(r) as relType
        WITH nodeStats, relType, count(*) as relCount
        WITH nodeStats, collect({type: relType, count: relCount}) as relStats
        
        RETURN nodeStats, relStats
        """
        
        try:
            result = self.connection.execute_query(stats_query)
            if result:
                return {
                    "node_statistics": result[0]["nodeStats"],
                    "relationship_statistics": result[0]["relStats"]
                }
            return {}
        except Exception as e:
            print(f"Error retrieving graph statistics: {str(e)}")
            return {}
    
    def search_nodes_by_property(self, property_name: str, property_value: Any, 
                                node_label: str = None) -> List[Dict[str, Any]]:
        """
        Search for nodes by a specific property value.
        
        Args:
            property_name: Name of the property to search
            property_value: Value to search for
            node_label: Optional node label to filter by
            
        Returns:
            List of matching nodes
        """
        if node_label:
            query = f"""
            MATCH (n:{node_label})
            WHERE n.{property_name} = $value
            RETURN elementId(n) as id, labels(n) as labels, properties(n) as properties
            LIMIT 100
            """
        else:
            query = f"""
            MATCH (n)
            WHERE n.{property_name} = $value
            RETURN elementId(n) as id, labels(n) as labels, properties(n) as properties
            LIMIT 100
            """
        
        try:
            result = self.connection.execute_query(query, {"value": property_value})
            return result if result else []
        except Exception as e:
            print(f"Error searching nodes: {str(e)}")
            return []
    
    def get_pattern_data(self, node_type_a: str, relationship_type: str, 
                        node_type_b: str) -> Optional[Dict[str, Any]]:
        """
        Get nodes and relationships matching a specific pattern.
        
        Args:
            node_type_a: Label of the first node type
            relationship_type: Type of relationship
            node_type_b: Label of the second node type
            
        Returns:
            Dictionary containing matching nodes and relationships
        """
        pattern_query = f"""
        MATCH (a:{node_type_a})-[r:{relationship_type}]->(b:{node_type_b})
        RETURN 
            collect(DISTINCT {{
                id: elementId(a),
                labels: labels(a),
                properties: properties(a)
            }}) + collect(DISTINCT {{
                id: elementId(b),
                labels: labels(b),
                properties: properties(b)
            }}) as nodes,
            collect({{
                id: elementId(r),
                type: type(r),
                properties: properties(r),
                start_node: elementId(startNode(r)),
                end_node: elementId(endNode(r))
            }}) as relationships
        """
        
        try:
            result = self.connection.execute_query(pattern_query)
            if not result:
                return None
                
            # Process nodes
            nodes_data = {}
            for node in result[0]["nodes"]:
                nodes_data[node["id"]] = {
                    "labels": node["labels"],
                    "properties": node["properties"]
                }
            
            # Process relationships
            rel_data = {}
            for rel in result[0]["relationships"]:
                rel_data[rel["id"]] = {
                    "type": rel["type"],
                    "properties": rel["properties"],
                    "start_node": rel["start_node"],
                    "end_node": rel["end_node"]
                }
            
            return {
                "nodes": nodes_data,
                "relationships": rel_data
            }
            
        except Exception as e:
            print(f"Error retrieving pattern data: {str(e)}")
            return None
    
    def _get_node_type_counts(self, node_data: Dict[str, Any]) -> Dict[str, int]:
        """Helper method to count node types"""
        node_types = {}
        for node in node_data.values():
            for label in node["labels"]:
                node_types[label] = node_types.get(label, 0) + 1
        return node_types
    
    def _get_relationship_type_counts(self, rel_data: Dict[str, Any]) -> Dict[str, int]:
        """Helper method to count relationship types"""
        rel_types = {}
        for rel in rel_data.values():
            rel_types[rel["type"]] = rel_types.get(rel["type"], 0) + 1
        return rel_types


# Factory function
def create_graph_data_fetcher(neo4j_connection: Neo4jConnection) -> GraphDataFetcher:
    """
    Factory function to create a GraphDataFetcher instance
    
    Args:
        neo4j_connection: Active Neo4j connection
        
    Returns:
        GraphDataFetcher instance
    """
    return GraphDataFetcher(neo4j_connection)


if __name__ == "__main__":
    # Test the graph data fetcher
    from connect_to_neo4j import create_neo4j_connection
    
    conn = create_neo4j_connection()
    if conn.driver:
        fetcher = create_graph_data_fetcher(conn)
        
        # Test getting statistics
        stats = fetcher.get_graph_statistics()
        print("Graph Statistics:", stats)
        
        # Test getting limited data
        limited_data = fetcher.get_limited_graph_data(10)
        if limited_data:
            print(f"Limited data retrieved successfully")
    
    conn.close()
