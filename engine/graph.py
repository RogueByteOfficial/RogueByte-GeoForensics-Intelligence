"""
RogueByte GeoForensics Intelligence - Identity and Relationship Graph
====================================================================
Builds an evidence graph linking accounts, devices, phone numbers, IP addresses,
sessions, calls, evidence files, and geographic observations.
Every relationship includes provenance source and edge strength.
Never conflates account ownership with physical device operation.
"""

from typing import Dict, Any, List, Optional
import json


class GraphNode:
    def __init__(self, node_id: str, node_type: str, label: str, metadata: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.node_type = node_type  # e.g., 'ACCOUNT', 'DEVICE', 'PHONE_NUMBER', 'IP_ADDRESS', 'CALL', 'EVIDENCE_FILE', 'GEO_OBSERVATION'
        self.label = label
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "label": self.label,
            "metadata": self.metadata
        }


class GraphEdge:
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        strength: float,  # 0.0 to 1.0
        confidence_category: str,  # 'DIRECT_HARDWARE', 'LOGGED_SESSION', 'RECORDED_EVENT', 'CORRELATED'
        evidence_reference: str,
        notes: str = ""
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship = relationship
        self.strength = min(1.0, max(0.0, float(strength)))
        self.confidence_category = confidence_category
        self.evidence_reference = evidence_reference
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relationship": self.relationship,
            "strength": self.strength,
            "confidence_category": self.confidence_category,
            "evidence_reference": self.evidence_reference,
            "notes": self.notes
        }


class ForensicsIdentityGraph:
    """Manages forensic network graph with audit tracking."""
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_node(self, node_id: str, node_type: str, label: str, metadata: Optional[Dict[str, Any]] = None) -> GraphNode:
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(node_id, node_type, label, metadata)
        return self.nodes[node_id]

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        strength: float,
        confidence_category: str,
        evidence_reference: str,
        notes: str = ""
    ) -> GraphEdge:
        edge = GraphEdge(source_id, target_id, relationship, strength, confidence_category, evidence_reference, notes)
        self.edges.append(edge)
        return edge

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges]
        }

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
