"""Generate graph-browser display annotations from ontology instances.

Reads cfr.ttl + all instances/*.ttl, produces a single
generated-display.ttl with gb:Node and gb:EdgeAssertion triples
for every instance-level resource (constraint assessments, obligations,
trust relationships, redeemer actions, guards, tensions, invariants).

The hand-written display.ttl covers the framework-level nodes.
This script covers everything else.
"""

import glob
import re
import sys
from rdflib import Graph, Namespace, RDF, RDFS, Literal, BNode, URIRef

CFR = Namespace("https://lambdasistemi.github.io/cardano-for-regulators/ontology#")
GB = Namespace("https://lambdasistemi.github.io/graph-browser/vocab/terms#")
GBK = Namespace("https://lambdasistemi.github.io/graph-browser/vocab/kinds#")
GBG = Namespace("https://lambdasistemi.github.io/graph-browser/vocab/groups#")

import argparse

ONTOLOGY = "ontology/cfr.ttl"
INSTANCES_GLOB = "ontology/instances/*.ttl"
DEFAULT_OUTPUT = "ontology/generated-display.ttl"

# Map cfr: types to graph-browser kinds
KIND_MAP = {
    CFR.ConstraintAssessment: "assessment",
    CFR.TrustRelationship: "trust",
    CFR.RedeemerAction: "action",
    CFR.Guard: "guard",
    CFR.FormalInvariant: "invariant",
    CFR.ComplianceRecord: "record",
}

# Properties to use as label, falling back in order
LABEL_PROPS = [
    RDFS.label,
    CFR.actionLabel,
    CFR.obligationLabel,
    CFR.tensionLabel,
    CFR.guardDescription,
    CFR.invariantStatement,
    CFR.penaltyDescription,
    CFR.assessmentResult,
]

# Properties to use as description
DESC_PROPS = [
    RDFS.comment,
    CFR.assessmentJustification,
    CFR.guardDescription,
    CFR.invariantStatement,
    CFR.architectureResponse,
    CFR.blockchainMitigates,
    CFR.trustRisk,
]


def safe_id(uri):
    """Make a kebab-case node ID from a URI."""
    local = str(uri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
    return re.sub(r'[^a-zA-Z0-9-]', '-', local).lower().strip('-')


def get_literal(g, subj, props):
    """Get the first literal value from a list of properties."""
    for prop in props:
        for o in g.objects(subj, prop):
            if isinstance(o, Literal):
                val = str(o).replace("\n", " ").strip()
                return re.sub(r'\s+', ' ', val)
    return ""


def get_group(g, subj):
    """Determine the group from the regulation this resource belongs to."""
    # Check if this resource is referenced by a regulation
    for reg in g.subjects(None, subj):
        for t in g.objects(reg, RDF.type):
            if t in (CFR.EURegulation, CFR.ISOStandard, CFR.IndustryCertification):
                label = get_literal(g, reg, [RDFS.label])
                return safe_id(label) if label else "unknown"
    return "framework"


def already_annotated(display_g, subj):
    """Check if this subject already has a gb:Node annotation in display.ttl."""
    return (subj, RDF.type, GB.Node) in display_g


def main():
    # Load everything
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")
    for f in sorted(glob.glob(INSTANCES_GLOB)):
        g.parse(f, format="turtle")

    # Load existing display.ttl to avoid duplicates
    display_g = Graph()
    try:
        display_g.parse("ontology/display.ttl", format="turtle")
    except Exception:
        pass

    out = Graph()
    out.bind("gb", GB)
    out.bind("gbk", GBK)
    out.bind("gbg", GBG)
    out.bind("rdfs", RDFS)

    edge_counter = [1000]  # start high to avoid collisions with display.ttl

    def add_node(subj, kind, label, desc, group):
        if already_annotated(display_g, subj):
            return
        if not label:
            return
        out.add((subj, RDF.type, GB.Node))
        out.add((subj, RDF.type, GBK[kind]))
        out.add((subj, GB.nodeId, Literal(safe_id(subj))))
        out.add((subj, RDFS.label, Literal(label)))
        out.add((subj, GB.description, Literal(desc or label)))
        out.add((subj, GB.group, GBG[group]))

    def add_edge(source, target, label, desc=""):
        if already_annotated(display_g, source) is False and (source, RDF.type, GB.Node) not in out:
            return
        if already_annotated(display_g, target) is False and (target, RDF.type, GB.Node) not in out:
            return
        edge = BNode(f"ge{edge_counter[0]}")
        edge_counter[0] += 1
        out.add((edge, RDF.type, GB.EdgeAssertion))
        out.add((edge, GB["from"], source))
        out.add((edge, GB.to, target))
        out.add((edge, RDFS.label, Literal(label)))
        if desc:
            out.add((edge, GB.description, Literal(desc)))

    # --- Constraint assessments ---
    for ca in g.subjects(RDF.type, CFR.ConstraintAssessment):
        result = get_literal(g, ca, [CFR.assessmentResult])
        constraint = list(g.objects(ca, CFR.assessesConstraint))
        justification = get_literal(g, ca, [CFR.assessmentJustification])
        if constraint:
            c_label = get_literal(g, constraint[0], [RDFS.label])
            label = f"{c_label}: {result}"
            add_node(ca, "assessment", label, justification, get_group(g, ca))
            # Edge: assessment → constraint
            add_edge(ca, constraint[0], result, justification)

    # --- Trust relationships ---
    for tr in g.subjects(RDF.type, CFR.TrustRelationship):
        pa = list(g.objects(tr, CFR.trustPartyA))
        pb = list(g.objects(tr, CFR.trustPartyB))
        risk = get_literal(g, tr, [CFR.trustRisk])
        mitigation = get_literal(g, tr, [CFR.blockchainMitigates])
        level = list(g.objects(tr, CFR.hasTrustLevel))
        level_label = get_literal(g, level[0], [RDFS.label]) if level else "?"
        if pa and pb and risk:
            label = f"{level_label}: {risk[:60]}"
            add_node(tr, "trust", label, f"Risk: {risk}. Mitigation: {mitigation}", get_group(g, tr))
            add_edge(pa[0], tr, "trust risk")
            add_edge(tr, pb[0], "affects")

    # --- Redeemer actions (only if not already in display.ttl) ---
    for action in g.subjects(RDF.type, CFR.RedeemerAction):
        a_label = get_literal(g, action, [CFR.actionLabel, RDFS.label])
        if not a_label:
            continue
        add_node(action, "action", a_label,
                 get_literal(g, action, DESC_PROPS) or a_label,
                 get_group(g, action))

    # --- Guards ---
    for guard in g.subjects(RDF.type, CFR.Guard):
        desc = get_literal(g, guard, [CFR.guardDescription])
        if not desc:
            continue
        universal = any(
            str(o).lower() == "true"
            for o in g.objects(guard, CFR.isUniversalGuard)
        )
        label = f"{'✓ ' if universal else ''}{desc[:80]}"
        add_node(guard, "guard", label, desc, get_group(g, guard))

    # --- Edges: action → guard ---
    for action in g.subjects(RDF.type, CFR.RedeemerAction):
        for guard in g.objects(action, CFR.hasGuard):
            add_edge(action, guard, "checks")

    # --- Edges: regulation → redeemer action ---
    for reg_type in [CFR.EURegulation, CFR.ISOStandard, CFR.IndustryCertification]:
        for reg in g.subjects(RDF.type, reg_type):
            for action in g.objects(reg, CFR.hasRedeemerAction):
                add_edge(reg, action, "has action")
            for ca in g.objects(reg, CFR.hasConstraintAssessment):
                add_edge(reg, ca, "assessed")
            for tr in g.objects(reg, CFR.hasTrustRelationship):
                add_edge(reg, tr, "trust model")

    # --- Formal invariants ---
    for inv in g.subjects(RDF.type, CFR.FormalInvariant):
        stmt = get_literal(g, inv, [CFR.invariantStatement])
        status = get_literal(g, inv, [CFR.proofStatus])
        if stmt:
            add_node(inv, "invariant", f"{status}: {stmt[:60]}", stmt, get_group(g, inv))

    # Write display TTL
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--views-dir", default=None,
                        help="Directory to write view JSON files")
    args = parser.parse_args()

    ttl = out.serialize(format="turtle")
    with open(args.output, "w") as f:
        f.write(ttl)

    node_count = len(list(out.subjects(RDF.type, GB.Node)))
    edge_count = len(list(out.subjects(RDF.type, GB.EdgeAssertion)))
    print(f"Generated: {args.output} ({node_count} nodes, {edge_count} edges)")

    # Generate views if requested
    if args.views_dir:
        import json
        import os
        os.makedirs(args.views_dir, exist_ok=True)

        # Merge display.ttl + generated into one graph for complete edge list
        combined = Graph()
        combined += out
        combined += display_g

        # Collect all edges with their source/target node IDs
        all_edges = []
        for edge in combined.subjects(RDF.type, GB.EdgeAssertion):
            src = list(combined.objects(edge, GB["from"]))
            tgt = list(combined.objects(edge, GB.to))
            lbl = get_literal(combined, edge, [RDFS.label])
            if src and tgt and lbl:
                src_id = get_literal(combined, src[0], [GB.nodeId]) or safe_id(src[0])
                tgt_id = get_literal(combined, tgt[0], [GB.nodeId]) or safe_id(tgt[0])
                # gb:group can be a URIRef (gbg:schema) or absent
                src_grps = list(combined.objects(src[0], GB.group))
                tgt_grps = list(combined.objects(tgt[0], GB.group))
                src_g = str(src_grps[0]).rsplit("#", 1)[-1] if src_grps else ""
                tgt_g = str(tgt_grps[0]).rsplit("#", 1)[-1] if tgt_grps else ""
                all_edges.append((src_id, tgt_id, lbl, src_g, tgt_g))

        # Find regulations and their groups
        reg_views = {}
        for reg_type in [CFR.EURegulation, CFR.ISOStandard, CFR.IndustryCertification]:
            for reg in g.subjects(RDF.type, reg_type):
                if not list(g.objects(reg, CFR.hasFitAssessment)):
                    continue
                label = get_literal(g, reg, [RDFS.label])
                group = safe_id(label)
                reg_views[group] = label

        # Framework view: edges where both endpoints are in framework/schema groups
        framework_groups = {"schema", "protocol", "constraint", "mechanism"}

        # Write view index
        view_index = [
            {"name": "Framework", "description": "Schema roles, artifacts, patterns, constraints.", "file": "framework.json"}
        ]
        for group, label in sorted(reg_views.items()):
            view_index.append({
                "name": label,
                "description": f"{label} instance: parties, obligations, trust model, validator.",
                "file": f"{group}.json"
            })

        with open(os.path.join(args.views_dir, "index.json"), "w") as f:
            json.dump(view_index, f, indent=2)

        # Framework view
        fw_edges = [[s, t, l] for s, t, l, sg, tg in all_edges
                    if sg in framework_groups or tg in framework_groups]
        with open(os.path.join(args.views_dir, "framework.json"), "w") as f:
            json.dump({"name": "Framework", "description": "Schema roles, artifacts, patterns, constraints.", "edges": fw_edges}, f, indent=2)
        print(f"  View: framework ({len(fw_edges)} edges)")

        # Per-regulation views: edges where at least one endpoint is in the reg's group
        for group, label in reg_views.items():
            reg_edges = [[s, t, l] for s, t, l, sg, tg in all_edges
                         if sg == group or tg == group
                         or sg in framework_groups or tg in framework_groups]
            with open(os.path.join(args.views_dir, f"{group}.json"), "w") as f:
                json.dump({"name": label, "description": f"{label} instance.", "edges": reg_edges}, f, indent=2)
            print(f"  View: {group} ({len(reg_edges)} edges)")


if __name__ == "__main__":
    main()
