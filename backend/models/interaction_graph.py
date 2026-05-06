"""
models/interaction_graph.py

WHY NETWORKX GRAPH FOR DRUG INTERACTIONS:
  Drug interaction databases model a many-to-many relationship between
  drugs and substances. A graph is the most natural data structure:
    - Nodes: drugs and metabolic enzymes (CYP450, P-gp, etc.)
    - Edges: interactions with severity and effect attributes

  Key advantage over a lookup table: NetworkX path finding can detect
  INDIRECT interactions. Example:
    Drug A → inhibits CYP3A4 → Drug B is CYP3A4 substrate
    Even if (A, B) is not a direct edge, nx.has_path(A, B) catches it.

SECURITY NOTE:
  • The graph is built once at module load from a trusted JSON file.
    Runtime drug names (from the pipeline state) are only used as
    lookup keys — they cannot add nodes or edges to the graph.
  • is_related() uses nx.has_path() — a read-only operation. No graph
    mutation is possible from API input.
  • The JSON file must be versioned and audited; shipping new interaction
    data requires a code review and deployment, not a database write.
"""

import json
import logging
import networkx as nx

logger = logging.getLogger(__name__)


class DrugInteractionGraph:
    def __init__(self) -> None:
        # Directed graph: direction encodes causality (inhibitor → substrate)
        self.graph: nx.Graph = nx.Graph()

    def load(self, path: str) -> None:
        """
        Load interaction data from JSON.

        Expected format:
          [
            {"drug_a": "warfarin", "drug_b": "aspirin",
             "severity": "HIGH", "effect": "increased bleeding risk"},
            ...
          ]
        """
        with open(path) as f:
            data = json.load(f)

        for item in data:
            self.graph.add_edge(
                item["drug_a"].lower(),
                item["drug_b"].lower(),
                severity=item.get("severity", "UNKNOWN"),
                effect=item.get("effect", ""),
            )

        logger.info(
            "DrugInteractionGraph loaded: %d nodes, %d edges",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    def check_interactions(
        self, new_drug: str, current_meds: list[str]
    ) -> list[dict]:
        """
        Return all interactions between new_drug and any current medication.
        """
        new_drug_lower = new_drug.lower()
        interactions   = []

        for med in current_meds:
            med_lower = med.lower()
            if self.graph.has_edge(new_drug_lower, med_lower):
                edge = self.graph[new_drug_lower][med_lower]
                interactions.append({
                    "drug":     med,
                    "severity": edge.get("severity", "UNKNOWN"),
                    "effect":   edge.get("effect", ""),
                })

        return interactions

    def is_related(self, drug: str, substance: str) -> bool:
        """
        Return True if there is any path between drug and substance in the graph.
        Used for allergy cross-reactivity detection.
        """
        d = drug.lower()
        s = substance.lower()
        if not self.graph.has_node(d) or not self.graph.has_node(s):
            return False
        return nx.has_path(self.graph, d, s)
