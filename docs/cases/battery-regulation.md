# EU Battery Regulation

**Regulation:** (EU) 2023/1542 on batteries and waste batteries

**Status:** Reference case — this regulation was the source from which the
framework was extracted.

**Full implementation:** [eu-digital-product-passport](https://github.com/lambdasistemi/eu-digital-product-passport)
**Smart contract:** [Battery Smart Contract](battery-contract.md) — UTxO diagrams, guard table, lifecycle state machines, hardware signing flow.

## Constraint check

| Constraint | Assessment | Notes |
|-----------|-----------|-------|
| **Data cadence** | Pass | SoH readings monthly at most. Lifecycle events are rare. |
| **Sequential access** | Pass | One manufacturer per trie. Relay on repurposing. |
| **Liveness** | Pass | Art. 77 penalties for non-compliance. Slot-based timeouts for readings. |
| **Fee alignment** | Pass | Manufacturers pay ~$0.10-0.15 per reading. Compliance value far exceeds cost. |
| **Identity delegation** | Pass | NFC secure element (SE050) signs readings. Consumer taps phone, no wallet needed. |

## Obligation map

| Element | Battery Regulation |
|---------|-------------------|
| **Regulator** | European Commission |
| **Obligated parties** | Manufacturers, importers, distributors |
| **Reporting obligations** | SoH, recycled content %, carbon footprint, composition |
| **Verification bodies** | Market surveillance authorities, notified bodies |
| **Beneficiaries** | Consumers, second-life market, recyclers |
| **Penalties** | Fines, market withdrawal, criminal liability |
| **Timeline** | 2027 EV batteries, 2028 industrial, phased |

## Data classification

| Data | Type | Access tier |
|------|------|-------------|
| Product identity, chemistry, manufacturing date | Static | Public |
| Carbon footprint per kWh, performance class | Static | Public |
| Recycled content percentages | Static | Public |
| State of Health (SoH) | Dynamic | Public |
| Cycle count, capacity fade | Dynamic | Public |
| Detailed composition | Static | Authorized operators |
| Disassembly instructions | Static | Authorized operators |
| Full SoH history | Dynamic | Authorities |
| Supply chain audit trail | Event-driven | Authorities |

## Architecture

### Storage: MPT-per-operator

- ~100-200 battery manufacturers operate in the EU market
- ~4-5 million EV/industrial batteries placed on market per year
- One UTxO per manufacturer, items are leaves
- Cost: ~$18/year for daily root updates across all operators

### Protocol: commitment-then-submit

Two-transaction protocol for authenticated readings:

1. Operator sets commitment on item leaf (slot window)
2. Consumer taps NFC → SE050 signs reading → operator submits + clears
   commitment

### Hardware: NFC signing module

| Component | Cost (1M volume) |
|-----------|-----------------|
| NXP NTAG 5 Link (NFC + I2C master) | $0.35 |
| NXP SE050 (Ed25519 + secp256k1) | $1.50 |
| Antenna + passives | $0.06 |
| **Total** | **$1.91** |

### Lifecycle state machine

```
Virgin → Active → Repurposed → Recycled
                ↘ Recycled
```

Cross-operator handoff on repurposing: new leaf in new operator's trie
with back-link to original.

## Formal invariants

| Invariant | Lean theorem | Status |
|-----------|-------------|--------|
| Single-use commitment | `commitment_cleared_after_submit` | Proved |
| Reward monotonicity | `credit_increases` | Proved |
| MPT consistency | `transition_preserves_consistency` | Proved |

## Trust model

| Party A | Party B | Trust | Risk | Mitigation |
|---------|---------|-------|------|------------|
| Manufacturer | Consumer | Low | SoH manipulation | Immutable on-chain history |
| Manufacturer | Regulator | Medium | Selective reporting | Completeness proofs via MPT |
| Consumer | Consumer | None | Counterfeit resale | On-chain provenance |
| Sensor | Chain | Hardware | Analog tampering | Expensive, destructive |

## Economics

| Scale | Pattern | Annual cost |
|-------|---------|------------|
| 1K batteries | CIP-68 per item | $200-500 |
| 1M batteries | CIP-68 per item | $6-10M locked |
| 1M batteries | MPT per operator | $1,800-3,600 |
| 10M+ batteries | Hydra L2 + MPT | ~$750 |
