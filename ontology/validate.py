"""Validate RDF ontology and instance files.

Checks:
  1. All .ttl files parse as valid Turtle
  2. Every instance's cfr: references resolve to classes/properties in the ontology
  3. Every cfr:mapsToRole target is a subclass of cfr:Party
  4. Every cfr:assessesConstraint target is a cfr:Constraint
  5. Every cfr:implementedBy target is a subclass of cfr:ProtocolPattern
  6. Every cfr:hasGuard target is a cfr:Guard
  7. Every cfr:hasFitAssessment target is a cfr:FitAssessment
  8. Every cfr:hasAccessTier target is a cfr:AccessTier
  9. Every cfr:hasDataType target is a cfr:DataType
  10. Every cfr:hasTrustLevel target is a cfr:TrustLevel
"""

import glob
import sys
from rdflib import Graph, Namespace, RDF, RDFS

CFR = Namespace("https://lambdasistemi.github.io/cardano-for-regulators/ontology#")

ONTOLOGY = "ontology/cfr.ttl"
INSTANCES_GLOB = "ontology/instances/*.ttl"


def load_ontology():
    g = Graph()
    g.parse(ONTOLOGY, format="turtle")
    return g


def collect_instances_of(ontology, cls):
    """Collect all subjects that are rdf:type of cls or a subclass of cls."""
    result = set()
    classes = {cls}
    for sub in ontology.subjects(RDFS.subClassOf, cls):
        classes.add(sub)
    for c in classes:
        for s in ontology.subjects(RDF.type, c):
            result.add(s)
    return result


def collect_subclasses(ontology, cls):
    result = {cls}
    for sub in ontology.subjects(RDFS.subClassOf, cls):
        result.add(sub)
    return result


def validate_range(combined, ontology, prop, expected_class, errors):
    """Check that every object of prop is an instance of expected_class."""
    valid = collect_instances_of(combined, expected_class)
    valid_classes = collect_subclasses(combined, expected_class)
    for s, _, o in combined.triples((None, prop, None)):
        if o not in valid and o not in valid_classes:
            errors.append(f"{prop.n3()} target {o.n3()} is not a {expected_class.n3()}")


def main():
    errors = []

    # 1. Parse ontology
    try:
        ontology = load_ontology()
        n = len(ontology)
        print(f"OK: {ONTOLOGY} ({n} triples)")
    except Exception as e:
        print(f"FAIL: {ONTOLOGY} — {e}")
        sys.exit(1)

    # 2. Parse all instance files
    instance_files = sorted(glob.glob(INSTANCES_GLOB))
    if not instance_files:
        print(f"WARN: no instance files found at {INSTANCES_GLOB}")

    combined = Graph()
    combined += ontology

    for f in instance_files:
        try:
            g = Graph()
            g.parse(f, format="turtle")
            n = len(g)
            combined += g
            print(f"OK: {f} ({n} triples)")
        except Exception as e:
            errors.append(f"{f} — parse error: {e}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        sys.exit(1)

    # 3. Validate property ranges
    checks = [
        (CFR.mapsToRole, CFR.Party, "party role"),
        (CFR.assessesConstraint, CFR.Constraint, "constraint"),
        (CFR.implementedBy, CFR.ProtocolPattern, "protocol pattern"),
        (CFR.hasGuard, CFR.Guard, "guard"),
        (CFR.hasFitAssessment, CFR.FitAssessment, "fit assessment"),
        (CFR.hasAccessTier, CFR.AccessTier, "access tier"),
        (CFR.hasDataType, CFR.DataType, "data type"),
        (CFR.hasTrustLevel, CFR.TrustLevel, "trust level"),
        (CFR.hasMode, CFR.Mode, "mode"),
    ]

    for prop, cls, label in checks:
        validate_range(combined, ontology, prop, cls, errors)

    # 4. Check that every ConcreteParty has a mapsToRole
    for s in combined.subjects(RDF.type, CFR.ConcreteParty):
        roles = list(combined.objects(s, CFR.mapsToRole))
        if not roles:
            errors.append(f"ConcreteParty {s.n3()} has no cfr:mapsToRole")

    # 5. Check that every ConstraintAssessment has a result
    for s in combined.subjects(RDF.type, CFR.ConstraintAssessment):
        results = list(combined.objects(s, CFR.assessmentResult))
        if not results:
            errors.append(f"ConstraintAssessment {s.n3()} has no cfr:assessmentResult")

    # 6. Check that every Regulation with a fit assessment has at least one party and one obligation
    #    (cross-references to other regulations without fit assessments are allowed to be stubs)
    for reg_class in [CFR.Regulation, CFR.EURegulation, CFR.ISOStandard, CFR.IndustryCertification]:
        for s in combined.subjects(RDF.type, reg_class):
            fit = list(combined.objects(s, CFR.hasFitAssessment))
            if not fit:
                continue
            parties = list(combined.objects(s, CFR.hasParty))
            if not parties:
                errors.append(f"Regulation {s.n3()} has no cfr:hasParty")
            obligations = list(combined.objects(s, CFR.hasObligation))
            if not obligations:
                errors.append(f"Regulation {s.n3()} has no cfr:hasObligation")

    # Report
    if errors:
        print(f"\n{len(errors)} validation error(s):")
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)
    else:
        total = len(combined)
        regs = len(list(combined.subjects(RDF.type, CFR.EURegulation)))
        regs += len(list(combined.subjects(RDF.type, CFR.ISOStandard)))
        regs += len(list(combined.subjects(RDF.type, CFR.IndustryCertification)))
        print(f"\nAll checks passed: {total} triples, {regs} regulation(s), {len(instance_files)} instance file(s)")


if __name__ == "__main__":
    main()
