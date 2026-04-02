# Cardano for Regulators

How a regulator can use Cardano to enforce a multi-party regulation without
running infrastructure, managing identities, or trusting any single operator.

## Four parties, zero trust

A regulated process involves four independent parties. Each manages one
concern and trusts no other party beyond what the chain enforces.

```mermaid
graph TB
    KYC[KYC Provider<br/><i>identity trie</i>]
    REG[Regulator<br/><i>smart contract</i>]
    OP[Operator<br/><i>process trie</i>]
    U[User<br/><i>signing function</i>]

    REG -->|writes| SC{Smart Contract}
    REG -->|trusts| KYC
    SC -->|governs| OP
    KYC -->|reference input| SC
    OP -->|distributes signing functions| U
    U -->|double-signed payloads| OP
    OP -->|submits transactions| SC
```

| Party | Manages | Trusts |
|-------|---------|--------|
| **Regulator** | Smart contract — the rules of the game | The KYC provider's UTxO |
| **KYC provider** | Identity trie — attested actor public keys | Their own verification process |
| **Operator** | Process trie — items and processes | The smart contract — cannot deviate |
| **User** | Nothing — just acts | The signing function they received |

## On-chain architecture

Three Merkle Patricia Tries, three UTxOs, three owners. The regulator's
smart contract governs the operator's trie and reads the KYC provider's
trie as a reference input.

```mermaid
graph LR
    subgraph Regulator's Trust Anchor
        KYC_UTxO[KYC UTxO<br/>root hash]
        KYC_T[KYC Trie]
        KYC_UTxO --- KYC_T
    end

    subgraph Operator's Data
        OP_UTxO[Process UTxO<br/>root hash]
        OP_T[Process Trie]
        OP_UTxO --- OP_T
    end

    subgraph Regulator's Rules
        SC[Smart Contract<br/>Plutus Validator]
    end

    SC -->|governs| OP_UTxO
    KYC_UTxO -.->|reference input| SC
```

## Two modes, same architecture

The framework supports two fundamentally different modes under the same
on-chain architecture:

```mermaid
graph TB
    subgraph Physical Mode
        SENSOR[Physical Sensor] -->|I2C| SE[Secure Element]
        SE -->|COSE_Sign1| NFC[NFC Interface]
        NFC -->|tap| PHONE[Phone]
        PHONE -->|payload| OP1[Operator]

        NOTE1[Object is the identity<br/>AND the witness]
    end

    subgraph Process Mode
        SERVER[Server] -->|hosts| SFUNC[Signing Function]
        APP[App / API] -->|invokes| SFUNC
        SFUNC -->|signed payload| OP2[Operator]

        NOTE2[Identity is abstract<br/>Protocol is the witness]
    end
```

- **Physical mode** — a battery, a sensor, a chip. The object carries its
  own identity and attests its own state.
- **Process mode** — a permit, a certification, a supply chain declaration.
  The signing function lives on a server, the identity is abstract.

## What you'll find here

- [**The Regulator Schema**](framework/schema.md) — the full architecture:
  four parties, signing functions, double signatures, the commitment
  protocol, the baton pattern, and the two modes
- [**The Five Constraints**](framework/constraints.md) — what makes a
  regulation a good fit: data cadence, sequential access, liveness, fee
  alignment, identity delegation
- [**Analysis Methodology**](framework/methodology.md) — step-by-step process
  for decomposing a regulation into on-chain patterns
- [**Architecture Patterns**](framework/patterns.md) — reusable patterns
  (MPT-per-operator, commitment protocols, relay state machines, reward
  distribution)
- [**Case Studies**](cases/battery-regulation.md) — regulations analyzed
  through this framework
