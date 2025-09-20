"""
Neo4j Database Connection Module
Handles connection and query execution for Neo4j database
"""

from neo4j import GraphDatabase
import os
from typing import Optional, List, Dict, Any


class Neo4jConnection:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j connection with credentials
        
        Args:
            uri: Neo4j database URI
            user: Database username
            password: Database password
        """
        # Use environment variables if not provided
        self.uri = uri or os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'vLAhHDOb5PCxsCv9ejXjNO64i5kkT9WVTgpYaJ-fAMA')
        
        self.driver = None
        self.connect()
    
    def connect(self) -> bool:
        """
        Creates a Neo4j database connection.
        Returns True if successful, False if connection fails.
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("Neo4j connection successful!")
            return True
        except Exception as e:
            print(f"Neo4j connection failed: {str(e)}")
            self.driver = None
            return False
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> Optional[List[Dict]]:
        """
        Executes a Neo4j query and returns the results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of record dictionaries or None if error
        """
        if not self.driver:
            print("No active Neo4j connection!")
            return None
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"Query execution failed: {str(e)}")
            return None
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")
    
    def test_connection(self) -> bool:
        """Test if the connection is working"""
        test_result = self.execute_query("RETURN 'Connection test successful' as message")
        if test_result:
            print(test_result[0]["message"])
            return True
        return False

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Factory function for easy connection creation
def create_neo4j_connection(uri: str = None, user: str = None, password: str = None) -> Neo4jConnection:
    """
    Factory function to create and return a Neo4j connection
    
    Args:
        uri: Neo4j database URI
        user: Database username  
        password: Database password
        
    Returns:
        Neo4jConnection instance
    """
    return Neo4jConnection(uri, user, password)


if __name__ == "__main__":
    # Test the connection
    conn = create_neo4j_connection()
    if conn.driver:
        conn.test_connection()
    conn.close()
