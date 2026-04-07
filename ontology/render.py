"""Render RDF ontology instances as markdown with Mermaid graphs.

Reads each instance .ttl file, queries structured data, and produces
markdown with both visual graphs and tables. Output goes to
docs/generated/<instance-name>.md.
"""

import glob
import os
import re
import sys
from rdflib import Graph, Namespace, RDF, RDFS

CFR = Namespace("https://lambdasistemi.github.io/cardano-for-regulators/ontology#")

ONTOLOGY = "ontology/cfr.ttl"
INSTANCES_GLOB = "ontology/instances/*.ttl"
OUTPUT_DIR = "docs/generated"

# Mermaid node shape per schema role
ROLE_SHAPE = {
    "Regulator": ("[[", "]]"),
    "Identity Provider": ("[[", "]]"),
    "Operator": ("[", "]"),
    "User": ("([", "])"),
    "Verification Body": ("{{", "}}"),
    "Beneficiary": ("([", "])"),
}

# Colors for trust levels
TRUST_STYLE = {
    "Low": "stroke:#f85149,stroke-width:2px",
    "Medium": "stroke:#e3b341,stroke-width:2px",
    "High": "stroke:#56d364,stroke-width:2px",
    "None": "stroke:#f85149,stroke-width:3px,stroke-dasharray: 5 5",
}


def mermaid_id(s):
    """Make a safe mermaid node ID."""
    return re.sub(r'[^a-zA-Z0-9]', '_', s)


def label(g, node):
    for o in g.objects(node, RDFS.label):
        return str(o)
    return str(node).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def comment(g, node):
    for o in g.objects(node, RDFS.comment):
        return re.sub(r'\s+', ' ', str(o)).strip()
    return ""


def literal_val(g, subj, pred):
    for o in g.objects(subj, pred):
        return re.sub(r'\s+', ' ', str(o)).strip()
    return ""


def find_regulations(g):
    reg_classes = [CFR.Regulation, CFR.EURegulation, CFR.ISOStandard, CFR.IndustryCertification]
    regs = set()
    for cls in reg_classes:
        for s in g.subjects(RDF.type, cls):
            if list(g.objects(s, CFR.hasFitAssessment)):
                regs.add(s)
    return regs


def render_party_graph(g, reg, parties):
    """Mermaid graph: parties mapped to schema roles."""
    lines = []
    lines.append("```mermaid")
    lines.append("graph LR")

    # Group parties by role
    role_parties = {}
    for p in parties:
        p_label = literal_val(g, p, CFR.partyLabel) or label(g, p)
        roles = list(g.objects(p, CFR.mapsToRole))
        role = label(g, roles[0]) if roles else "Unknown"
        role_parties.setdefault(role, []).append(p_label)

    # Render role subgraphs
    for role, members in role_parties.items():
        rid = mermaid_id(role)
        lines.append(f'    subgraph {rid}["{role}"]')
        for m in members:
            mid = mermaid_id(m)
            l, r = ROLE_SHAPE.get(role, ("[", "]"))
            lines.append(f'        {mid}{l}"{m}"{r}')
        lines.append("    end")

    # Add edges from regulation to roles
    reg_label = label(g, reg)
    reg_id = mermaid_id(reg_label)
    lines.append(f'    {reg_id}{{"📋 {reg_label}"}}')
    for role in role_parties:
        rid = mermaid_id(role)
        lines.append(f"    {reg_id} --> {rid}")

    lines.append("```")
    return lines


def render_obligation_pattern_graph(g, obligations):
    """Mermaid graph: obligations connected to their protocol patterns."""
    lines = []
    lines.append("```mermaid")
    lines.append("graph LR")

    patterns_seen = set()
    for ob in obligations:
        ob_label = literal_val(g, ob, CFR.obligationLabel) or label(g, ob)
        ob_id = mermaid_id(ob_label)
        basis = literal_val(g, ob, CFR.legalBasis)
        deadline = literal_val(g, ob, CFR.deadline)
        display = ob_label
        if basis:
            display += f"<br/><i>{basis}</i>"

        impl = list(g.objects(ob, CFR.implementedBy))
        dtypes = list(g.objects(ob, CFR.hasDataType))
        dtype = label(g, dtypes[0]) if dtypes else ""
        tiers = list(g.objects(ob, CFR.hasAccessTier))
        tier = label(g, tiers[0]) if tiers else ""

        lines.append(f'    {ob_id}["{display}"]')

        if impl:
            p_label = label(g, impl[0])
            p_id = mermaid_id(p_label)
            if p_id not in patterns_seen:
                lines.append(f'    {p_id}{{{{"⚙️ {p_label}"}}}}')
                patterns_seen.add(p_id)
            edge_label = deadline if deadline else ""
            # Strip parentheses — mermaid edge labels can't contain them
            edge_label = edge_label.replace("(", "").replace(")", "")
            if edge_label:
                lines.append(f"    {ob_id} -->|{edge_label}| {p_id}")
            else:
                lines.append(f"    {ob_id} --> {p_id}")

        if dtype:
            d_id = mermaid_id(dtype) + "_dt"
            if d_id not in patterns_seen:
                lines.append(f'    {d_id}["{dtype}"]')
                patterns_seen.add(d_id)
            lines.append(f"    {ob_id} -.-> {d_id}")

    lines.append("```")
    return lines


def render_trust_graph(g, trust_rels):
    """Mermaid graph: trust relationships between parties."""
    lines = []
    lines.append("```mermaid")
    lines.append("graph LR")

    parties_seen = set()
    style_lines = []

    for i, tr in enumerate(trust_rels):
        pa = list(g.objects(tr, CFR.trustPartyA))
        pb = list(g.objects(tr, CFR.trustPartyB))
        if not pa or not pb:
            continue
        pa_label = literal_val(g, pa[0], CFR.partyLabel)
        pb_label = literal_val(g, pb[0], CFR.partyLabel)
        pa_id = mermaid_id(pa_label)
        pb_id = mermaid_id(pb_label)

        if pa_id not in parties_seen:
            lines.append(f'    {pa_id}["{pa_label}"]')
            parties_seen.add(pa_id)
        if pb_id not in parties_seen:
            lines.append(f'    {pb_id}["{pb_label}"]')
            parties_seen.add(pb_id)

        tl = list(g.objects(tr, CFR.hasTrustLevel))
        tl_label = label(g, tl[0]) if tl else "?"
        risk = literal_val(g, tr, CFR.trustRisk)
        mitigation = literal_val(g, tr, CFR.blockchainMitigates)

        edge_id = f"edge_{i}"
        short_risk = risk[:40] + "..." if len(risk) > 40 else risk
        lines.append(f"    {pa_id} -- \"{tl_label}: {short_risk}\" --> {pb_id}")

    lines.append("```")
    return lines


def render_redeemer_graph(g, actions):
    """Mermaid graph: redeemer actions with their guards."""
    lines = []
    lines.append("```mermaid")
    lines.append("graph TB")

    # Collect all guards and which actions use them
    guard_actions = {}
    action_labels = {}
    for action in actions:
        a_label = literal_val(g, action, CFR.actionLabel) or label(g, action)
        a_id = mermaid_id(a_label)
        action_labels[a_id] = a_label
        for guard in g.objects(action, CFR.hasGuard):
            g_desc = literal_val(g, guard, CFR.guardDescription)
            g_id = mermaid_id(g_desc)
            universal = literal_val(g, guard, CFR.isUniversalGuard) == "true"
            guard_actions.setdefault((g_id, g_desc, universal), []).append(a_id)

    # Separate universal and specific guards
    universal_guards = []
    specific_guards = []
    for (g_id, g_desc, universal), acts in guard_actions.items():
        if universal:
            universal_guards.append((g_id, g_desc))
        else:
            specific_guards.append((g_id, g_desc, acts))

    # Render actions
    lines.append('    subgraph Actions["Redeemer Actions"]')
    for a_id, a_label in action_labels.items():
        lines.append(f'        {a_id}["{a_label}"]')
    lines.append("    end")

    # Render universal guards
    if universal_guards:
        lines.append('    subgraph Universal["Universal Guards"]')
        for g_id, g_desc in universal_guards:
            short = g_desc[:50]
            lines.append(f'        {g_id}{{{{"✓ {short}"}}}}')
        lines.append("    end")
        lines.append("    Actions --> Universal")

    # Render specific guards
    lines.append('    subgraph Specific["Action-Specific Guards"]')
    for g_id, g_desc, _ in specific_guards:
        short = g_desc[:50]
        lines.append(f'        {g_id}("{short}")')
    lines.append("    end")

    # Edges from actions to specific guards
    for g_id, g_desc, acts in specific_guards:
        for a_id in acts:
            lines.append(f"    {a_id} --> {g_id}")

    lines.append("```")
    return lines


def render_pattern_overview(g, reg):
    """Mermaid graph: all protocol patterns used by this regulation."""
    patterns = list(g.objects(reg, CFR.usesPattern))
    if not patterns:
        return []

    lines = []
    lines.append("```mermaid")
    lines.append("graph TB")

    reg_label = label(g, reg)
    reg_id = mermaid_id(reg_label)
    lines.append(f'    {reg_id}{{"📋 {reg_label}"}}')

    for p in patterns:
        p_label = label(g, p)
        p_id = mermaid_id(p_label)
        lines.append(f'    {p_id}{{{{"⚙️ {p_label}"}}}}')
        lines.append(f"    {reg_id} --> {p_id}")

    lines.append("```")
    return lines


def render_regulation(g, reg):
    """Render a single regulation as markdown with graphs."""
    lines = []
    reg_label = label(g, reg)
    ref = literal_val(g, reg, CFR.officialReference)
    url = literal_val(g, reg, CFR.fullTextURL)
    mode = label(g, list(g.objects(reg, CFR.hasMode))[0]) if list(g.objects(reg, CFR.hasMode)) else ""
    fit = label(g, list(g.objects(reg, CFR.hasFitAssessment))[0]) if list(g.objects(reg, CFR.hasFitAssessment)) else ""

    lines.append(f"# {reg_label}")
    lines.append("")
    lines.append("*Generated from the [RDF ontology](https://github.com/lambdasistemi/cardano-for-regulators/tree/main/ontology).*")
    lines.append("")
    if ref and url:
        lines.append(f"**Regulation:** [{ref}]({url})")
    elif ref:
        lines.append(f"**Regulation:** {ref}")
    if mode:
        lines.append(f"  |  **Mode:** {mode}")
    if fit:
        lines.append(f"  |  **Blockchain fit:** {fit}")
    lines.append("")

    # --- Protocol patterns overview graph ---
    patterns = list(g.objects(reg, CFR.usesPattern))
    if patterns:
        lines.append("## Protocol patterns")
        lines.append("")
        lines.extend(render_pattern_overview(g, reg))
        lines.append("")

    # --- Party graph ---
    parties = list(g.objects(reg, CFR.hasParty))
    if parties:
        lines.append("## Parties")
        lines.append("")
        lines.extend(render_party_graph(g, reg, parties))
        lines.append("")
        lines.append("| Actor | Schema role | Notes |")
        lines.append("|-------|------------|-------|")
        for p in parties:
            p_label = literal_val(g, p, CFR.partyLabel) or label(g, p)
            roles = list(g.objects(p, CFR.mapsToRole))
            role_label = label(g, roles[0]) if roles else "—"
            p_comment = comment(g, p).replace("\n", " ").replace("|", "—")
            lines.append(f"| {p_label} | {role_label} | {p_comment} |")
        lines.append("")

    # --- Constraint assessment ---
    assessments = list(g.objects(reg, CFR.hasConstraintAssessment))
    if assessments:
        lines.append("## Constraint check")
        lines.append("")
        lines.append("| Constraint | Result | Justification |")
        lines.append("|-----------|--------|---------------|")
        for ca in assessments:
            constraint = list(g.objects(ca, CFR.assessesConstraint))
            c_label = label(g, constraint[0]) if constraint else "?"
            result = literal_val(g, ca, CFR.assessmentResult)
            justification = literal_val(g, ca, CFR.assessmentJustification).replace("\n", " ").replace("|", "—")
            lines.append(f"| **{c_label}** | {result} | {justification} |")
        lines.append("")

    # --- Obligation-to-pattern graph ---
    obligations = list(g.objects(reg, CFR.hasObligation))
    if obligations:
        lines.append("## Obligations")
        lines.append("")
        lines.extend(render_obligation_pattern_graph(g, obligations))
        lines.append("")
        lines.append("| Obligation | Legal basis | Deadline | Pattern | Data type | Access |")
        lines.append("|-----------|-------------|----------|---------|-----------|--------|")
        for ob in obligations:
            ob_label = literal_val(g, ob, CFR.obligationLabel) or label(g, ob)
            basis = literal_val(g, ob, CFR.legalBasis)
            deadline = literal_val(g, ob, CFR.deadline)
            impl = list(g.objects(ob, CFR.implementedBy))
            pattern_label = label(g, impl[0]) if impl else "—"
            dtypes = list(g.objects(ob, CFR.hasDataType))
            dtype_label = label(g, dtypes[0]) if dtypes else "—"
            tiers = list(g.objects(ob, CFR.hasAccessTier))
            tier_label = label(g, tiers[0]) if tiers else "—"
            lines.append(f"| {ob_label} | {basis} | {deadline} | {pattern_label} | {dtype_label} | {tier_label} |")
        lines.append("")

    # --- Trust model graph ---
    trust_rels = list(g.objects(reg, CFR.hasTrustRelationship))
    if trust_rels:
        lines.append("## Trust model")
        lines.append("")
        lines.extend(render_trust_graph(g, trust_rels))
        lines.append("")
        lines.append("| Party A | Party B | Trust | Risk | Mitigation |")
        lines.append("|---------|---------|-------|------|------------|")
        for tr in trust_rels:
            pa = list(g.objects(tr, CFR.trustPartyA))
            pb = list(g.objects(tr, CFR.trustPartyB))
            pa_label = literal_val(g, pa[0], CFR.partyLabel) if pa else "?"
            pb_label = literal_val(g, pb[0], CFR.partyLabel) if pb else "?"
            tl = list(g.objects(tr, CFR.hasTrustLevel))
            tl_label = label(g, tl[0]) if tl else "?"
            risk = literal_val(g, tr, CFR.trustRisk).replace("|", "—")
            mitigation = literal_val(g, tr, CFR.blockchainMitigates).replace("|", "—")
            lines.append(f"| {pa_label} | {pb_label} | {tl_label} | {risk} | {mitigation} |")
        lines.append("")

    # --- Redeemer action graph ---
    actions = list(g.objects(reg, CFR.hasRedeemerAction))
    if actions:
        lines.append("## Validator")
        lines.append("")
        lines.extend(render_redeemer_graph(g, actions))
        lines.append("")

    # --- Penalties ---
    penalties = list(g.objects(reg, CFR.hasPenalty))
    if penalties:
        lines.append("## Penalties")
        lines.append("")
        lines.append("| Description | Maximum fine |")
        lines.append("|-------------|-------------|")
        for pen in penalties:
            desc = literal_val(g, pen, CFR.penaltyDescription).replace("|", "—")
            fine = literal_val(g, pen, CFR.maxFine)
            lines.append(f"| {desc} | {fine} |")
        lines.append("")

    return "\n".join(lines)


def render_ontology_overview(g):
    """Render the ontology itself — class hierarchy and property map."""
    lines = []
    lines.append("# Ontology")
    lines.append("")
    lines.append("*Generated from [`ontology/cfr.ttl`](https://github.com/lambdasistemi/cardano-for-regulators/blob/main/ontology/cfr.ttl).*")
    lines.append("")

    OWL = Namespace("http://www.w3.org/2002/07/owl#")

    # Collect classes with hierarchy
    classes = {}
    for cls in g.subjects(RDF.type, OWL.Class):
        cls_label = label(g, cls)
        parent = None
        for p in g.objects(cls, RDFS.subClassOf):
            parent = label(g, p)
        cls_comment = comment(g, cls).replace("\n", " ")
        classes[cls_label] = {"parent": parent, "comment": cls_comment, "uri": cls}

    # Build hierarchy: group children by root parent
    roots = {}  # root_label -> [(child_label, comment)]
    orphans = []  # classes with no parent and no children
    children_of = {}  # parent_label -> [child_label]
    for cls_label, info in classes.items():
        if info["parent"]:
            children_of.setdefault(info["parent"], []).append(cls_label)

    # Find roots: classes that are parents but have no parent themselves
    for cls_label, info in classes.items():
        if info["parent"] is None:
            if cls_label in children_of:
                roots[cls_label] = children_of[cls_label]
            else:
                orphans.append(cls_label)

    # One mermaid graph per root class — keeps each diagram focused
    lines.append("## Class hierarchy")
    lines.append("")
    for root_label in sorted(roots):
        children = sorted(roots[root_label])
        rid = mermaid_id(root_label)
        lines.append(f"### {root_label}")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph LR")
        lines.append(f'    {rid}["{root_label}"]')
        for child in children:
            cid = mermaid_id(child)
            lines.append(f'    {rid} --> {cid}["{child}"]')
            # Check for grandchildren
            if child in children_of:
                for grandchild in sorted(children_of[child]):
                    gcid = mermaid_id(grandchild)
                    lines.append(f'    {cid} --> {gcid}["{grandchild}"]')
        lines.append("```")
        lines.append("")
        # Table for this group
        lines.append("| Class | Description |")
        lines.append("|-------|-------------|")
        root_desc = classes[root_label]["comment"].replace("|", "—")
        lines.append(f"| **{root_label}** | {root_desc} |")
        for child in children:
            desc = classes[child]["comment"].replace("|", "—")
            lines.append(f"| {child} | {desc} |")
            if child in children_of:
                for grandchild in sorted(children_of[child]):
                    desc = classes[grandchild]["comment"].replace("|", "—")
                    lines.append(f"| ↳ {grandchild} | {desc} |")
        lines.append("")

    # Standalone classes (no parent, no children)
    if orphans:
        lines.append("### Standalone classes")
        lines.append("")
        lines.append("| Class | Description |")
        lines.append("|-------|-------------|")
        for cls_label in sorted(orphans):
            desc = classes[cls_label]["comment"].replace("|", "—")
            lines.append(f"| **{cls_label}** | {desc} |")
        lines.append("")

    # Collect properties
    obj_props = []
    data_props = []
    for prop in g.subjects(RDF.type, OWL.ObjectProperty):
        p_label = label(g, prop)
        domain = list(g.objects(prop, RDFS.domain))
        rng = list(g.objects(prop, RDFS.range))
        p_comment = comment(g, prop).replace("\n", " ")
        d = label(g, domain[0]) if domain else "—"
        r = label(g, rng[0]) if rng else "—"
        obj_props.append((p_label, d, r, p_comment))

    for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
        p_label = label(g, prop)
        domain = list(g.objects(prop, RDFS.domain))
        rng = list(g.objects(prop, RDFS.range))
        p_comment = comment(g, prop).replace("\n", " ")
        d = label(g, domain[0]) if domain else "—"
        r = label(g, rng[0]) if rng else "—"
        r = r.replace("http://www.w3.org/2001/XMLSchema#", "xsd:")
        data_props.append((p_label, d, r, p_comment))

    # Property relationship graph
    lines.append("## Property map")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph LR")
    seen_edges = set()
    for p_label, d, r, _ in obj_props:
        if d == "—" or r == "—":
            continue
        edge = (d, r, p_label)
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        did = mermaid_id(d)
        rid = mermaid_id(r)
        lines.append(f'    {did}["{d}"] -->|{p_label}| {rid}["{r}"]')
    lines.append("```")
    lines.append("")

    # Object properties table
    if obj_props:
        lines.append("### Object properties")
        lines.append("")
        lines.append("| Property | Domain | Range | Description |")
        lines.append("|----------|--------|-------|-------------|")
        for p_label, d, r, p_comment in sorted(obj_props):
            desc = p_comment.replace("|", "—")
            lines.append(f"| `{p_label}` | {d} | {r} | {desc} |")
        lines.append("")

    # Datatype properties table
    if data_props:
        lines.append("### Datatype properties")
        lines.append("")
        lines.append("| Property | Domain | Range | Description |")
        lines.append("|----------|--------|-------|-------------|")
        for p_label, d, r, p_comment in sorted(data_props):
            desc = p_comment.replace("|", "—")
            lines.append(f"| `{p_label}` | {d} | {r} | {desc} |")
        lines.append("")

    # Named individuals (constraint instances, trust levels, etc.)
    named = []
    for cls_label, info in classes.items():
        for inst in g.subjects(RDF.type, info["uri"]):
            inst_label = label(g, inst)
            if inst_label != cls_label:
                named.append((inst_label, cls_label))

    if named:
        lines.append("## Named individuals")
        lines.append("")
        lines.append("| Individual | Type |")
        lines.append("|-----------|------|")
        for inst_label, cls_label in sorted(named):
            lines.append(f"| {inst_label} | {cls_label} |")
        lines.append("")

    return "\n".join(lines)


def main():
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Render ontology overview (from ontology alone)
    overview_md = render_ontology_overview(g)
    overview_path = os.path.join(OUTPUT_DIR, "ontology.md")
    with open(overview_path, "w") as fout:
        fout.write(overview_md)
    print(f"Generated: {overview_path}")

    # Load instances
    instance_files = sorted(glob.glob(INSTANCES_GLOB))
    for f in instance_files:
        g.parse(f, format="turtle")

    regulations = find_regulations(g)
    if not regulations:
        print("No regulations with fit assessment found")
        sys.exit(1)

    for reg in regulations:
        md = render_regulation(g, reg)
        name = label(g, reg).lower().replace(" ", "-").replace("/", "-")
        out_path = os.path.join(OUTPUT_DIR, f"{name}.md")
        with open(out_path, "w") as fout:
            fout.write(md)
        print(f"Generated: {out_path}")

    print(f"\n{len(regulations)} regulation(s) + ontology overview rendered to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
