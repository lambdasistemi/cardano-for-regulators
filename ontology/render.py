"""Render RDF ontology instances as markdown tables.

Reads each instance .ttl file, queries structured data, and produces
a markdown snippet that mkdocs can include. Output goes to
docs/generated/<instance-name>.md.

Each generated file contains:
  - Schema mapping (concrete party → schema role)
  - Constraint assessment table
  - Obligation map with patterns and data types
  - Trust model table
  - Redeemer actions with guards
  - Penalties
"""

import glob
import os
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, Literal

CFR = Namespace("https://lambdasistemi.github.io/cardano-for-regulators/ontology#")

ONTOLOGY = "ontology/cfr.ttl"
INSTANCES_GLOB = "ontology/instances/*.ttl"
OUTPUT_DIR = "docs/generated"


def label(g, node):
    """Get rdfs:label or fall back to local name."""
    for o in g.objects(node, RDFS.label):
        return str(o)
    return str(node).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def comment(g, node):
    """Get rdfs:comment or empty string."""
    for o in g.objects(node, RDFS.comment):
        return str(o)
    return ""


def literal_val(g, subj, pred):
    """Get a single literal value or empty string."""
    for o in g.objects(subj, pred):
        return str(o)
    return ""


def find_regulations(g):
    """Find all regulation instances (any subclass of cfr:Regulation)."""
    reg_classes = [CFR.Regulation, CFR.EURegulation, CFR.ISOStandard, CFR.IndustryCertification]
    regs = set()
    for cls in reg_classes:
        for s in g.subjects(RDF.type, cls):
            if list(g.objects(s, CFR.hasFitAssessment)):
                regs.add(s)
    return regs


def render_regulation(g, reg):
    """Render a single regulation as markdown."""
    lines = []
    reg_label = label(g, reg)
    ref = literal_val(g, reg, CFR.officialReference)
    url = literal_val(g, reg, CFR.fullTextURL)
    mode = label(g, list(g.objects(reg, CFR.hasMode))[0]) if list(g.objects(reg, CFR.hasMode)) else ""
    fit = label(g, list(g.objects(reg, CFR.hasFitAssessment))[0]) if list(g.objects(reg, CFR.hasFitAssessment)) else ""

    lines.append(f"# {reg_label} — generated from ontology")
    lines.append("")
    if ref and url:
        lines.append(f"**Regulation:** [{ref}]({url})")
    elif ref:
        lines.append(f"**Regulation:** {ref}")
    if mode:
        lines.append(f"**Mode:** {mode}")
    if fit:
        lines.append(f"**Blockchain fit:** {fit}")
    lines.append("")

    # --- Schema mapping ---
    parties = list(g.objects(reg, CFR.hasParty))
    if parties:
        lines.append("## Schema mapping")
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

    # --- Obligations ---
    obligations = list(g.objects(reg, CFR.hasObligation))
    if obligations:
        lines.append("## Obligations")
        lines.append("")
        lines.append("| Obligation | Legal basis | Deadline | Pattern | Data type | Access |")
        lines.append("|-----------|-------------|----------|---------|-----------|--------|")
        for ob in obligations:
            ob_label = literal_val(g, ob, CFR.obligationLabel) or label(g, ob)
            basis = literal_val(g, ob, CFR.legalBasis)
            deadline = literal_val(g, ob, CFR.deadline)
            patterns = list(g.objects(ob, CFR.implementedBy))
            pattern_label = label(g, patterns[0]) if patterns else "—"
            dtypes = list(g.objects(ob, CFR.hasDataType))
            dtype_label = label(g, dtypes[0]) if dtypes else "—"
            tiers = list(g.objects(ob, CFR.hasAccessTier))
            tier_label = label(g, tiers[0]) if tiers else "—"
            lines.append(f"| {ob_label} | {basis} | {deadline} | {pattern_label} | {dtype_label} | {tier_label} |")
        lines.append("")

    # --- Trust model ---
    trust_rels = list(g.objects(reg, CFR.hasTrustRelationship))
    if trust_rels:
        lines.append("## Trust model")
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

    # --- Redeemer actions ---
    actions = list(g.objects(reg, CFR.hasRedeemerAction))
    if actions:
        lines.append("## Redeemer actions")
        lines.append("")
        for action in actions:
            a_label = literal_val(g, action, CFR.actionLabel) or label(g, action)
            guards = list(g.objects(action, CFR.hasGuard))
            guard_descs = []
            for guard in guards:
                desc = literal_val(g, guard, CFR.guardDescription)
                universal = literal_val(g, guard, CFR.isUniversalGuard)
                if universal == "true":
                    desc += " *(universal)*"
                guard_descs.append(desc)
            lines.append(f"### {a_label}")
            lines.append("")
            if guard_descs:
                lines.append("Guards:")
                lines.append("")
                for gd in guard_descs:
                    lines.append(f"- {gd}")
            a_comment = comment(g, action)
            if a_comment:
                lines.append("")
                lines.append(a_comment)
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

    # --- Patterns used ---
    patterns = list(g.objects(reg, CFR.usesPattern))
    if patterns:
        lines.append("## Protocol patterns used")
        lines.append("")
        for p in patterns:
            p_label = label(g, p)
            p_comment = comment(g, p).replace("\n", " ")
            lines.append(f"- **{p_label}** — {p_comment}")
        lines.append("")

    return "\n".join(lines)


def main():
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")

    instance_files = sorted(glob.glob(INSTANCES_GLOB))
    for f in instance_files:
        g.parse(f, format="turtle")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    regulations = find_regulations(g)
    if not regulations:
        print("No regulations with fit assessment found")
        sys.exit(1)

    for reg in regulations:
        md = render_regulation(g, reg)
        name = label(g, reg).lower().replace(" ", "-").replace("/", "-")
        out_path = os.path.join(OUTPUT_DIR, f"{name}.md")
        with open(out_path, "w") as f:
            f.write(md)
        print(f"Generated: {out_path}")

    print(f"\n{len(regulations)} regulation(s) rendered to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
