import xml.etree.ElementTree as ET
from typing import Dict, Any

try:
    import networkx as nx
    GraphBase = nx.MultiDiGraph
except Exception:  # pragma: no cover - networkx not installed
    class GraphBase:
        """Minimal MultiDiGraph replacement when networkx isn't available."""
        def __init__(self):
            self._nodes: Dict[str, Dict[str, Any]] = {}
            self._edges = []  # list of (src, dst, attrs)

        # Node operations
        def add_node(self, node_id: str, **attrs: Any) -> None:
            self._nodes[node_id] = attrs

        def nodes(self, data: bool = False):
            return self._nodes.items() if data else list(self._nodes.keys())

        # Edge operations
        def add_edge(self, src: str, dst: str, **attrs: Any) -> None:
            self._edges.append((src, dst, attrs))

        def edges(self, data: bool = False):
            return list(self._edges)

        # Convenience helpers
        def number_of_nodes(self) -> int:
            return len(self._nodes)

        def number_of_edges(self) -> int:
            return len(self._edges)

        def __len__(self):
            return self.number_of_nodes()


def parse_vl_to_graph(path: str) -> GraphBase:
    """Parse a .vl file into a graph representation.

    Nodes, Pads and ControlPoints become graph nodes. Links become edges
    between the owning nodes of the referenced pins or control points.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    graph = GraphBase()
    pin_to_node: Dict[str, Dict[str, str]] = {}

    # Helper to ensure a node exists
    def ensure_node(node_id: str, **attrs: Any) -> None:
        if node_id not in graph.nodes():
            graph.add_node(node_id, **attrs)

    # Register Nodes and their Pins
    for node in root.iter('Node'):
        node_id = node.get('Id')
        node_name = node.get('Name')
        ensure_node(node_id, type='Node', name=node_name)
        for pin in node.findall('Pin'):
            pin_id = pin.get('Id')
            pin_to_node[pin_id] = {
                'node': node_id,
                'name': pin.get('Name'),
                'kind': pin.get('Kind'),
            }

    # Register Pads
    for pad in root.iter('Pad'):
        pad_id = pad.get('Id')
        ensure_node(pad_id, type='Pad', value=pad.get('Value'))

    # Register ControlPoints
    for cp in root.iter('ControlPoint'):
        cp_id = cp.get('Id')
        ensure_node(cp_id, type='ControlPoint')

    # Links -> edges
    for link in root.iter('Link'):
        link_id = link.get('Id')
        ids = link.get('Ids', '').split(',')
        if len(ids) != 2:
            continue
        src_pin, dst_pin = ids
        src_info = pin_to_node.get(src_pin)
        dst_info = pin_to_node.get(dst_pin)

        src_node = src_info['node'] if src_info else src_pin
        dst_node = dst_info['node'] if dst_info else dst_pin

        # Ensure nodes exist if they were only referenced via pins
        ensure_node(src_node)
        ensure_node(dst_node)

        graph.add_edge(
            src_node,
            dst_node,
            id=link_id,
            src_pin=src_info['name'] if src_info else None,
            dst_pin=dst_info['name'] if dst_info else None,
        )

    return graph


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert VL file into a graph representation')
    parser.add_argument('vl_file', help='Path to the .vl file to convert')
    args = parser.parse_args()

    g = parse_vl_to_graph(args.vl_file)

    try:
        num_nodes = g.number_of_nodes()
        num_edges = g.number_of_edges()
        edges = list(g.edges(data=True))[:10]
    except AttributeError:  # pragma: no cover
        num_nodes = len(g.nodes())
        num_edges = len(g.edges())
        edges = g.edges()[:10]

    print(f'Nodes: {num_nodes}, Edges: {num_edges}')
    for u, v, data in edges:
        print(f'{u} -> {v} | {data}')
