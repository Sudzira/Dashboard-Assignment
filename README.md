# Neo4j Graph Visualization

An interactive web application for visualizing and exploring Neo4j graph databases using Bokeh. This application provides powerful search, filtering, and pattern exploration capabilities with an intuitive web interface.

## Features

- **Interactive Graph Visualization**: Pan, zoom, and explore your Neo4j graph data
- **Advanced Search**: Text search, pattern matching, and property-based queries
- **Dynamic Filtering**: Filter by node types, properties, relationships, and more
- **Pattern Exploration**: Discover relationships between different node types
- **Real-time Updates**: Interactive controls with immediate visual feedback
- **Export Capabilities**: Save visualizations and filtered data
- **Production Ready**: Deployable to Railway cloud platform

## Project Structure

```
neo4j-graph-viz/
├── app.py                    # Main application with Bokeh server
├── connect_to_neo4j.py      # Neo4j database connection handling
├── fetch_graph_data.py      # Backend data fetching and processing
├── graph_plotting.py        # Graph visualization using Bokeh
├── search_function.py       # Search and pattern exploration features
├── filter_function.py       # Advanced filtering capabilities
├── start.py                 # Production startup script
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway deployment configuration
├── railway.toml            # Railway build configuration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Neo4j database (local or cloud instance)
- Git

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd neo4j-graph-viz
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Neo4j credentials
   ```

5. **Run the application:**
   ```bash
   python app.py server
   ```

6. **Access the application:**
   Open your browser to `http://localhost:5006`

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
NEO4J_URI=neo4j://localhost:7687          # Your Neo4j URI
NEO4J_USER=neo4j                          # Neo4j username
NEO4J_PASSWORD=your-password              # Neo4j password

# Optional
PORT=5006                                 # Server port
MAX_NODES=1000                           # Limit nodes for performance
DEBUG=false                              # Debug mode
```

### Neo4j Database Requirements

Your Neo4j database should:
- Be accessible from your application
- Contain nodes and relationships
- Have proper authentication configured

## Usage

### Starting the Application

**Interactive Server (recommended):**
```bash
python app.py server [port]
```

**Static HTML Export:**
```bash
python app.py static [filename.html]
```

### Application Features

#### 1. Main Visualization Tab
- Interactive graph with pan/zoom
- Node search by name/properties
- Basic relationship exploration

#### 2. Filters Tab
- Filter by node types
- Numeric property range filtering
- Text property filtering
- Relationship-based filtering

#### 3. Advanced Search Tab
- Pattern matching (A-[relationship]->B)
- Complex property queries
- Saved filter combinations

#### 4. Statistics Tab
- Graph metrics and statistics
- Node/relationship type counts
- Connectivity information

### Search and Filter Examples

**Text Search:**
- Search for nodes containing "Matrix"
- Case-sensitive/insensitive options

**Pattern Search:**
- Find all `Movie-[ACTED_IN]->Actor` patterns
- Explore `Person-[DIRECTED]->Movie` relationships

**Property Filtering:**
- Movies with rating > 8.0
- Actors born after 1980
- Contains "Action" in genre

## Railway Deployment

### Quick Deploy

1. **Fork this repository** on GitHub

2. **Sign up for Railway** at [railway.app](https://railway.app)

3. **Create new project** from GitHub repo

4. **Set environment variables** in Railway dashboard:
   - `NEO4J_URI`
   - `NEO4J_USER` 
   - `NEO4J_PASSWORD`

5. **Deploy** - Railway will automatically build and deploy

### Detailed Deployment Guide

See the comprehensive [Railway Setup Guide](railway_setup.md) for:
- Step-by-step deployment instructions
- Neo4j Aura Cloud setup
- Environment configuration
- Troubleshooting tips
- Performance optimization
- Security considerations

### Railway CLI Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Set environment variables
railway variables set NEO4J_URI=your-uri
railway variables set NEO4J_USER=neo4j
railway variables set NEO4J_PASSWORD=your-password

# Deploy
railway up
```

## Development

### Code Structure

**connect_to_neo4j.py**: Database connection management
- Connection pooling
- Error handling
- Environment variable integration

**fetch_graph_data.py**: Data fetching backend
- Query optimization
- Data processing
- Statistics generation

**graph_plotting.py**: Visualization engine
- NetworkX integration
- Bokeh plotting
- Interactive features

**search_function.py**: Search capabilities
- Text search
- Pattern matching
- Property exploration

**filter_function.py**: Filtering system
- Multi-criteria filtering
- Visual feedback
- Performance optimization

### Adding New Features

1. **New Node Types**: Update color/size mapping in `graph_plotting.py`
2. **Custom Queries**: Add methods to `fetch_graph_data.py`
3. **UI Components**: Extend layouts in respective modules
4. **Filters**: Add new filter types to `filter_function.py`

### Testing

```bash
# Run with limited data for testing
python app.py server

# Export static version for testing
python app.py static test_viz.html
```

## Performance Optimization

### Large Databases

For databases with >10,000 nodes:

1. **Use data limiting:**
   ```python
   app.load_data(use_limited=True, limit=1000)
   ```

2. **Set MAX_NODES environment variable:**
   ```bash
   export MAX_NODES=1000
   ```

3. **Enable query optimization** in Neo4j

4. **Use focused queries** instead of loading all data

### Memory Management

- Limit concurrent users in production
- Use efficient graph layouts
- Implement data pagination for very large graphs

## Troubleshooting

### Common Issues

**Connection Failed:**
- Check Neo4j is running
- Verify URI format (bolt:// vs neo4j://)
- Test credentials manually

**Port Already in Use:**
```bash
python app.py server 5007  # Use different port
```

**Memory Issues:**
- Reduce MAX_NODES
- Use limited data loading
- Check available RAM

**Railway Deployment Issues:**
- Verify environment variables are set
- Check Railway logs for errors
- Ensure Neo4j allows external connections

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
python app.py server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Format code
black *.py

# Run linting
flake8 *.py

# Run tests
pytest
```

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the railway_setup.md for deployment help

## Changelog

### v1.0.0
- Initial release
- Basic graph visualization
- Search and filter capabilities
- Railway deployment support

### Future Features
- Real-time data updates
- Graph algorithm integration
- Export to various formats
- User authentication
- Multiple graph support

## Acknowledgments

- [Neo4j](https://neo4j.com) for the graph database
- [Bokeh](https://bokeh.org) for interactive visualization
- [NetworkX](https://networkx.org) for graph algorithms
- [Railway](https://railway.app) for deployment platform
