# The Regulator Schema

How a regulator can use Cardano to enforce a multi-party regulation without
running infrastructure, managing identities, or trusting any single operator.

## Four parties, four concerns

A regulated process involves four independent parties. Each manages one
concern and trusts no other party beyond what the chain enforces.

```mermaid
graph TB
    IDP[Identity Provider<br/><i>identity trie</i>]
    REG[Regulator<br/><i>regulation trie</i>]
    OP[Operator<br/><i>process trie</i>]
    U[User<br/><i>signing function</i>]

    REG -->|publishes| SC{Smart Contract}
    REG -->|trusts| IDP
    SC -->|governs| OP
    IDP -.->|reference input| SC
    REG -.->|reference input| SC
    OP -->|distributes signing functions| U
    U -->|double-signed payloads| OP
    OP -->|submits transactions| SC
```

| Party | Trie | Contains | Responsibility |
|-------|------|----------|----------------|
| **Identity provider** | Identity trie | Attested actor public keys | Who exists as a verified entity |
| **Regulator** | Regulation trie | Actor qualifications for this regulation | Who is qualified to participate |
| **Operator** | Process trie | Items, processes, state | What is happening |
| **User** | — | Just acts via signing function | Performing regulated actions |

No overlap. The identity provider doesn't know about processes. The regulator
doesn't run infrastructure. The operator can't fake users. The user doesn't
need to trust anyone.

The **smart contract** is the regulation in executable form — published by
the regulator, it governs the operator's trie and reads both the identity trie
and regulation trie as reference inputs. The regulator audits that operators
use the correct smart contract and follows the transactions over it.

## The on-chain architecture

Four Merkle Patricia Tries, four UTxOs, and a smart contract that ties
them together.

```mermaid
graph LR
    subgraph Identity Provider
        IDP_UTxO[Identity UTxO<br/>root hash]
        IDP_T[Identity Trie]
        IDP_UTxO --- IDP_T
        IDP_T --- K1[Actor Key A]
        IDP_T --- K2[Actor Key B]
        IDP_T --- K3[Actor Key N]
    end

    subgraph Regulator
        REG_UTxO[Regulation UTxO<br/>root hash]
        REG_T[Regulation Trie]
        REG_UTxO --- REG_T
        REG_T --- R1[Actor A<br/>licensed carrier]
        REG_T --- R2[Actor B<br/>authorized dispatcher]
        REG_T --- R3[Actor N<br/>revoked]
    end

    subgraph Operator
        OP_UTxO[Process UTxO<br/>root hash]
        OP_T[Process Trie]
        OP_UTxO --- OP_T
        OP_T --- L1[Leaf 1<br/>item/process]
        OP_T --- L2[Leaf 2<br/>item/process]
        OP_T --- L3[Leaf N<br/>item/process]
    end

    subgraph Smart Contract
        SC[Plutus Validator]
    end

    SC -->|governs| OP_UTxO
    IDP_UTxO -.->|reference input| SC
    REG_UTxO -.->|reference input| SC
```

| Trie | Owner | Contains | Role |
|------|-------|----------|------|
| **Identity trie** | identity provider | Attested actor public keys | Who exists as a verified real-world entity |
| **Regulation trie** | Regulator | Actor qualifications specific to this regulation | Who is qualified to act in this regulated process |
| **Process trie** | Operator | Items, processes, leaves with state | What is happening |
| **Commitment** | Inside each process leaf | Slot windows, expected actions | When and how actions occur |

Both the identity trie and the regulation trie are **reference inputs** —
read-only from the operator's perspective. The operator never spends them.
The smart contract reads them at validation time to verify that the actor
submitting a state transition is both an attested real-world entity (identity)
and qualified for this specific regulation (regulation trie).

## On-chain and off-chain verification

Privacy requires splitting verification across two layers:

```mermaid
graph TD
    subgraph On-chain - Smart Contract
        SIG[Signature verification<br/><i>public keys, actor signatures</i>]
        IDP_CHECK[identity trie membership<br/><i>actor key present?</i>]
        REG_CHECK[Regulation trie membership<br/><i>actor qualified?</i>]
        HASH[Root hash consistency<br/><i>MPT integrity</i>]
        SLOT[Slot window<br/><i>commitment timing</i>]
    end

    subgraph Off-chain - Operator
        LEAF[Leaf data verification<br/><i>actual claims behind hashes</i>]
        PAYLOAD[Payload content<br/><i>what the user actually submitted</i>]
        MATCH[Claim matches attestation<br/><i>user's claims vs trie leaves</i>]
    end

    SIG --> ACCEPT{Transaction<br/>accepted}
    IDP_CHECK --> ACCEPT
    REG_CHECK --> ACCEPT
    HASH --> ACCEPT
    SLOT --> ACCEPT
    LEAF --> SUBMIT[Operator submits<br/>transaction]
    PAYLOAD --> SUBMIT
    MATCH --> SUBMIT
    SUBMIT --> ACCEPT
```

**On-chain**: the smart contract verifies what's public — signatures, public
keys (actor in identity trie, actor qualified in regulation trie), commitment
windows, root hash consistency. All it sees are hashes and signatures.

**Off-chain**: the operator verifies the actual leaf data — the claims behind
the hashes. The smart contract can't see this data because only the hash
appears on-chain. The operator checks that what the user claims matches
what's in the leaf before submitting the transaction.

This split is the source of privacy: the chain proves *that* the right actor
with the right qualifications performed the right action at the right time,
but it never sees *what* the actual qualifications or claims contain. Only
hashes.

## Institutional responsibility

The responsibility for authentication and qualification lives with the
institutions — not with the operator.

```mermaid
graph TD
    subgraph Institutions
        KP[Identity Provider<br/><i>attests identities<br/>revokes keys</i>]
        RG[Regulator<br/><i>qualifies actors<br/>defines rules</i>]
    end

    subgraph Operator
        OP[Operator<br/><i>cannot add keys to identity trie<br/>cannot add qualifications<br/>to regulation trie</i>]
    end

    KP -.->|attestation| OP
    RG -.->|qualification| OP
    OP -->|verified claims| TX[Transaction]

    subgraph What the operator CAN do
        V1[Verify attestations off-chain]
        V2[Reject unattested submissions]
        V3[Submit only verified payloads]
    end

    subgraph What the operator CANNOT do
        X1[Fake users]
        X2[Invent qualifications]
        X3[Bypass identity or regulation trie]
    end
```

The operator can verify attestations from the institutions and be sure they
are operating with attested, qualified users. But they cannot invent fake
processes involving non-attested users — the smart contract will reject any
transaction where the actor's key is missing from the identity or regulation trie.

## How a transaction works

Every state transition follows this flow:

```mermaid
sequenceDiagram
    participant KP as Identity Provider
    participant R as Regulator
    participant O as Operator
    participant SF as Signing Function
    participant U as User
    participant C as Cardano

    Note over KP: Independently maintains<br/>identity trie

    Note over R: Independently maintains<br/>regulation trie

    R->>C: Publish smart contract<br/>(references identity + regulation UTxOs)

    O->>C: Deploy process trie<br/>(governed by smart contract)
    O->>SF: Mint signing function<br/>(register pubkey on-chain)

    O->>C: Create commitment in leaf<br/>(slot window)

    U->>SF: Request signature<br/>(payload + commitment)
    SF->>U: Signed payload

    U->>O: Submit double-signed payload<br/>(process sig + actor sig)

    Note over O: Off-chain verification:<br/>leaf data matches claims

    O->>C: Submit transaction

    Note over C: Validator checks:
    Note over C: 1. Actor key in identity trie?<br/>(reference input)
    Note over C: 2. Actor qualified in regulation trie?<br/>(reference input)
    Note over C: 3. Commitment exists?<br/>(expected action)
    Note over C: 4. Slot in window?<br/>(timely)
    Note over C: 5. Process signature valid?<br/>(authentic)
    Note over C: 6. Actor key authorized?<br/>(baton holder)
    Note over C: 7. Leaf update matches payload?<br/>(untampered)
    Note over C: 8. New root hash consistent?<br/>(MPT integrity)

    C->>C: Clear commitment<br/>(no replay)
```

The validator has access to all the information it needs in a single
evaluation: the process trie UTxO (spent input), the identity trie UTxO and
regulation trie UTxO (reference inputs), the signatures, and the slot range.

## What the regulator produces

The regulator does two things: maintains a **regulation trie** and publishes
a **smart contract**.

```mermaid
graph TD
    REG[Regulator]

    REG -->|maintains| RT[Regulation Trie<br/><i>actor qualifications</i>]
    RT --> Q1[Licensed carrier A]
    RT --> Q2[Authorized dispatcher B]
    RT --> Q3[Certified inspector C]

    REG -->|publishes| SC[Smart Contract]
    SC --> DS[Data Schema<br/><i>what fields a leaf must contain</i>]
    SC --> VT[Valid Transitions<br/><i>what updates are allowed,<br/>in what order, by whom</i>]
    SC --> CP[Commitment Protocol<br/><i>how time windows work,<br/>what must be signed</i>]
    SC --> AR[Authorization Rules<br/><i>how the baton is assigned<br/>and passed</i>]
    SC --> REF[Reference Inputs<br/><i>which identity and regulation<br/>UTxOs to read</i>]
```

The **regulation trie** contains process-specific actor qualifications —
not generic identity (that's the identity provider's job), but credentials
specific to what this regulation requires. A traceability regulation might
qualify actors as licensed carriers, authorized dispatchers, or certified
inspectors.

The **smart contract** encodes the regulation as a Plutus validator. The
regulator publishes it once. Every operator in the market operates under it.
The regulator audits that operators use the correct smart contract and
follows the transactions over it.

The regulator does not run the identity infrastructure. They decide **which
identity provider to trust** — a government identity agency, eIDAS, a private
service — and reference that provider's UTxO in their smart contract
alongside their own regulation trie UTxO.

The eUTxO model ensures the validator is evaluated at every transaction.
Non-compliant updates are rejected by the chain itself. The regulation is
enforced at the transaction level, not by inspectors after the fact.

## What the identity provider does

The identity provider maintains a Merkle Patricia Trie of verified actors.

```mermaid
graph TD
    subgraph Off-chain Verification
        V1[Identity check]
        V2[Document verification]
        V3[Institutional accreditation]
    end

    subgraph On-chain Identity Trie
        ROOT[Identity UTxO<br/>root hash]
        ROOT --- A1[Actor Key A<br/><i>verified manufacturer</i>]
        ROOT --- A2[Actor Key B<br/><i>verified inspector</i>]
        ROOT --- A3[Actor Key C<br/><i>verified importer</i>]
        ROOT --- A4[Actor Key N<br/><i>revoked</i>]
    end

    V1 --> ROOT
    V2 --> ROOT
    V3 --> ROOT
```

The identity provider:

1. **Verifies real-world entities** — through whatever process they use
   (government ID, corporate registration, professional accreditation)
2. **Adds public keys to their trie** — each verified entity gets a leaf
3. **Revokes keys** — when an entity's status changes, their leaf is
   updated or removed
4. **Maintains the UTxO** — independent of any specific regulation

The same identity trie can serve multiple regulators and multiple regulations.
One identity infrastructure, many smart contracts referencing it. Or
different regulators can trust different providers — each contract points
to its own.

This is what prevents the operator from faking users. The operator can
mint signing functions and simulate processes, but they cannot add keys to
the identity provider's trie. Every actor in a regulated process must have a
key that appears in the trusted identity trie. The validator checks this via
reference input at every transaction.

## What the operator does

The operator participates in the regulated market. They manage a process
trie — one UTxO holding the root hash — containing all items or processes
under their responsibility.

```mermaid
graph TD
    OP[Operator] -->|1| MK[Mint signing functions<br/><i>generate keys, register on-chain,<br/>distribute capability</i>]
    OP -->|2| CC[Create commitments<br/><i>set time-bounded windows<br/>in trie leaves</i>]
    OP -->|3| VF[Verify off-chain<br/><i>check user claims against<br/>leaf data before submitting</i>]
    OP -->|4| CS[Collect submissions<br/><i>receive double-signed<br/>payloads from users</i>]
    OP -->|5| ST[Submit transactions<br/><i>batch updates to trie,<br/>pay all fees</i>]
```

The operator is a **transparent pipe**. They choose *when* to batch, but
not *what* goes in. The signed payload is the input, the leaf update is
the output, and the contract verifies they match.

The operator **verifies off-chain** what the smart contract cannot see:
the actual data behind the hashes. This is the operator's added value —
they leverage institutional attestations (from identity and regulation tries)
to be sure they are operating with attested, qualified users, and they
verify the actual claims before submitting the transaction.

The operator cannot tamper with the data:

```mermaid
graph LR
    subgraph Cannot Tamper
        P[Signed Payload] -->|operator receives| O[Operator]
        O -->|operator submits| TX[Transaction]
        TX -->|validator checks| V{Payload = Leaf Update?}
        V -->|yes| OK[Accepted]
        V -->|no| REJECT[Rejected]
    end

    C[Commitment<br/><i>defined by smart contract</i>] -->|constrains| TX
    S[Signature<br/><i>invalidated if modified</i>] -->|protects| P
    R[Root Hash<br/><i>must be consistent</i>] -->|constrains| TX
```

- The commitment is defined by the smart contract
- The payload is signed (tampering invalidates the signature)
- The update is validated by the smart contract
- The new root hash must be consistent with the leaf change

## What the user does

The user interacts with a regulated process without any blockchain knowledge.
They don't have a wallet, don't hold ADA, don't know what Cardano is.

```mermaid
graph LR
    U[User] -->|1. receive| SF[Signing<br/>Function]
    U -->|2. use| ACT[Tap / Scan / Click]
    ACT --> DS[Double-Signed<br/>Payload]
    U -->|3. pass on| NEXT[Next Actor's<br/>Public Key]
    DS --> OP[Operator]
    NEXT --> OP
```

1. **Receive a signing capability** — a physical device, an app, or access
   to a signing service
2. **Perform the regulated action** — tap an NFC chip, scan a QR code,
   press a button in an app
3. **Pass the baton** — the final action designates the next authorized key

From the user's perspective: tap, use, pass on. The cryptography is
invisible.

## The signing function

The atomic unit of the system is not a key, not a device, not a user — it
is a **signing function**. An opaque capability that produces signatures
when invoked, without exposing the private key.

```mermaid
graph TB
    OP[Operator] -->|mints| SF[Signing Function]
    SF -->|public key| CHAIN[On-chain Leaf]
    SF -->|capability| WORLD[Physical or Digital World]

    subgraph Substrates
        HW[Hardware SE<br/><i>physical isolation</i>]
        PH[Phone Enclave<br/><i>OS isolation</i>]
        SV[Server Endpoint<br/><i>access control</i>]
        TEE[TEE / Enclave<br/><i>HW-assisted SW</i>]
        ZK[ZK Circuit<br/><i>cryptographic isolation</i>]
    end

    WORLD --- HW
    WORLD --- PH
    WORLD --- SV
    WORLD --- TEE
    WORLD --- ZK
```

| Substrate | Key protection | When to use |
|-----------|---------------|-------------|
| Hardware secure element (SE050) | Physical isolation — key never leaves chip | Sensor-bound, physical measurements |
| Phone secure enclave | OS-level isolation | Consumer actions |
| Server endpoint | Access control | Abstract processes, enterprise |
| TEE / enclave | Hardware-assisted software isolation | High-assurance backends |
| ZK circuit | Cryptographic isolation | Privacy-preserving proofs |

All substrates present the same interface to the chain: a public key
registered in a leaf, and signatures the validator can verify.

The signing function does not need to be secret. It signs whatever is
asked of it. The security is not in the key's secrecy — it is in the
double signature and the commitment protocol.

### Key slots and reuse

A signing device — physical or software — can hold multiple key slots.
Each slot is an independent signing capability.

```mermaid
graph TD
    DEV[Signing Device]
    DEV --> S1[Slot 1<br/><i>Battery Regulation<br/>Operator A</i>]
    DEV --> S2[Slot 2<br/><i>Logistics Tracking<br/>Operator B</i>]
    DEV --> S3[Slot 3<br/><i>Empty — available<br/>for future use</i>]

    S1 -.->|registered in| L1[Operator A's Trie<br/>Leaf #4721]
    S2 -.->|registered in| L2[Operator B's Trie<br/>Leaf #89]
```

- **One slot, one purpose** — cheap, disposable. Lost? The on-chain key is
  deauthorized.
- **Multiple slots, multiple operators** — the same device participates in
  different compliance schemes simultaneously. Each operator only sees
  their own leaf.
- **Reflash and repurpose** — new key, new on-chain registration, new
  meaning. The device outlives any single use case.

The device has no owner in the blockchain sense. It has a *holder*. The
meaning of each slot is defined entirely by the on-chain leaf it's
registered in. The same hardware can be recollected and reused indefinitely,
as long as it has available slots.

## The double signature

Every state transition requires two signatures:

```mermaid
graph TD
    subgraph Process Signature
        SF[Signing Function] -->|signs| PL[Payload + Commitment]
        PL --> PS[Process Signature]
        PS -->|proves| ID[This process produced<br/>this data at this time]
    end

    subgraph Actor Signature
        AK[Actor's Key] -->|signs| SUB[Submission]
        SUB --> AS[Actor Signature]
        AS -->|proves| AUTH[The authorized party<br/>requests this transition]
    end

    PS --> V{Validator}
    AS --> V
    V -->|both valid +<br/>actor in identity trie +<br/>actor in regulation trie| OK[State transition accepted]
```

1. **The process signature** — the signing function signs the payload,
   including the commitment. This proves: *this specific process or item
   produced this specific data at this specific time*. It is an identifier,
   not an access control.

2. **The actor signature** — the current baton holder signs the submission.
   This proves: *the authorized party is requesting this state transition*.
   This is the access control.

Neither signature alone is sufficient:

- Process signature without actor signature → anyone could have called
  the signing function, no authorization
- Actor signature without process signature → the actor could claim
  anything about the process, no authentication

Together they prove: an authorized, attested, qualified actor interacted
with a specific process and is submitting a specific, time-bounded state
update.

## The commitment protocol

The commitment prevents replay, ensures timeliness, and binds each action
to a specific moment in the on-chain state.

```mermaid
sequenceDiagram
    participant O as Operator
    participant C as Chain
    participant SF as Signing Function
    participant U as User (Baton Holder)

    O->>C: 1. Create commitment in leaf<br/>(validFrom, validUntil)
    Note over C: Leaf now expects an action

    U->>SF: 2. Feed payload + commitment
    SF->>U: Signed payload

    U->>U: 3. Sign submission with own key

    U->>O: 4. Send double-signed payload

    O->>C: 5. Submit transaction

    Note over C: Validator checks:<br/>commitment exists ✓<br/>slot in window ✓<br/>process sig valid ✓<br/>actor in identity trie ✓<br/>actor in regulation trie ✓<br/>actor authorized ✓<br/>leaf update matches ✓

    C->>C: 6. Clear commitment
    Note over C: Single-use — no replay
```

The commitment is the mechanism that turns a generic signing capability
into a one-shot, time-bounded, authorized action. Because the signing
function signs the commitment as part of the payload, and the smart
contract defines what a valid commitment looks like, the operator has no
room to manipulate timing or replay old submissions.

## The baton pattern

Authorization to act on a process is a baton that travels through
the real world — physical or digital.

```mermaid
graph LR
    subgraph Lifecycle
        O[Operator creates leaf<br/><i>no actor assigned</i>]
        O --> A1[First tap<br/><i>Actor A becomes<br/>baton holder</i>]
        A1 --> U1[Actor A uses<br/><i>submits readings,<br/>progresses state</i>]
        U1 --> P1[Actor A passes<br/><i>final submission includes<br/>Actor B's pubkey</i>]
        P1 --> A2[Actor B holds baton<br/><i>Actor A locked out</i>]
        A2 --> U2[Actor B uses]
        U2 --> P2[Actor B passes<br/><i>to Actor C</i>]
        P2 --> A3[Actor C holds baton]
        A3 --> END[End of lifecycle]
    end
```

The baton passes atomically with the last action. There is no gap where
nobody holds authorization — the transfer is part of the state transition,
validated by the smart contract.

No user registration. No identity database. No login. Authorization is
determined entirely by the on-chain state. You hold the baton or you
don't.

## Two modes

The same architecture supports two fundamentally different modes:

```mermaid
graph TB
    subgraph Physical Mode
        SENSOR[Physical Sensor] -->|I2C| SE[Secure Element]
        SE -->|COSE_Sign1| NFC[NFC Interface]
        NFC -->|tap| PHONE[Phone]
        PHONE -->|payload| OP1[Operator]
        OP1 -->|tx| CHAIN1[Chain]

        NOTE1[Object is the identity<br/>AND the witness]
    end

    subgraph Process Mode
        SERVER[Server] -->|hosts| SFUNC[Signing Function]
        APP[App / API] -->|invokes| SFUNC
        SFUNC -->|signed payload| OP2[Operator]
        OP2 -->|tx| CHAIN2[Chain]

        NOTE2[Identity is abstract<br/>Protocol is the witness]
    end
```

### Physical mode

The object carries its own identity and can attest its own state.

- A battery with a sensor and secure element signs "my state of health
  is 87%"
- The data comes from the thing itself — a physical measurement
- No server needed — the object is both the identifier and the witness
- Trust comes from the hardware: the sensor measured reality, the secure
  element signed it, the chain anchored it

Use when: the regulation requires physical measurements, sensor data,
or tamper-evident attestation from the object itself.

### Process mode

There is no physical object — just a logical process advancing through
stages.

- A permit application moves from applicant → reviewer → approver
- A certification workflow passes through inspector → auditor → issuer
- A supply chain declaration flows from producer → transporter → customs

The signing function lives on a server. The operator mints a key pair,
registers the public key on-chain, and makes the signing function
available. The identity is abstract — it represents a process, not a
thing.

Trust comes from the protocol: the double signature proves the right
actor performed the right action, the commitment proves timeliness, the
smart contract proves correctness.

Use when: the regulation governs a multi-party workflow where what
matters is that the right sequence of actions happened, not what a
physical sensor measured.

### Same architecture

```mermaid
graph TD
    subgraph Shared Architecture
        MPT[Merkle Patricia Trie]
        COMMIT[Commitment Protocol]
        DSIG[Double Signature]
        BATON[Baton Pattern]
        SC[Smart Contract Validation]
        IDPC[Identity Trie Reference]
        REGC[Regulation Trie Reference]
    end

    PHYS[Physical Mode] --> MPT
    PROC[Process Mode] --> MPT
    PHYS --> COMMIT
    PROC --> COMMIT
    PHYS --> DSIG
    PROC --> DSIG
    PHYS --> BATON
    PROC --> BATON
    PHYS --> SC
    PROC --> SC
    PHYS --> IDPC
    PROC --> IDPC
    PHYS --> REGC
    PROC --> REGC
```

The difference is the trust basis: hardware attestation vs protocol
enforcement. Physical mode is strictly stronger (you get process
guarantees *plus* physical attestation), but process mode covers
regulations that have no physical component.

## Privacy

No single party has the full picture:

```mermaid
graph TD
    subgraph Knowledge Boundaries
        OP[Operator<br/><i>verifies claims off-chain<br/>doesn't know real identities</i>]
        U[User<br/><i>knows they acted<br/>doesn't know the private key</i>]
        CH[Chain<br/><i>knows pubkeys + hashes<br/>no real-world data</i>]
        KP[Identity Provider<br/><i>knows identities<br/>doesn't know which process</i>]
        RG[Regulator<br/><i>knows qualifications<br/>doesn't see process data</i>]
    end

    OP -.-|no link| U
    U -.-|no link| CH
    KP -.-|no link| OP
    RG -.-|no link| OP
```

| Party | Knows | Doesn't know |
|-------|-------|-------------|
| **Identity provider** | Real-world identity behind each attested key | Which processes the key participates in |
| **Regulator** | Which actors are qualified for their regulation | Process data, operator activity |
| **Operator** | Claims and leaf data (verified off-chain) | Real-world identity behind the keys |
| **User** | That they interacted with a signing function | The private key |
| **Chain** | Public keys, hashes, and valid signatures | Any actual data or real-world identities |

The identity provider knows identities but not processes. The regulator knows
qualifications but not process data. The operator verifies claims but
doesn't know identities. The chain sees only hashes and signatures. No
single party can reconstruct the full picture.

Privacy is structural, not policy-based. The chain only stores hashes —
the actual data behind the leaves is verified off-chain by the operator.
The on-chain proofs (signatures, trie membership) establish *that* the
right things happened without revealing *what* the actual content is.

## The full picture

```mermaid
graph TB
    subgraph Identity Layer
        IDP_P[Identity Provider<br/><i>off-chain verification</i>]
        IDP_UTxO[Identity UTxO<br/><i>identity trie root</i>]
        IDP_P -->|maintains| IDP_UTxO
    end

    subgraph Regulator Layer
        REG[Regulator<br/><i>qualifies actors</i>]
        REG_UTxO[Regulation UTxO<br/><i>qualification trie root</i>]
        SC[Smart Contract<br/><i>Plutus validator</i>]
        REG -->|maintains| REG_UTxO
        REG -->|publishes| SC
        SC -->|references| IDP_UTxO
        SC -->|references| REG_UTxO
    end

    subgraph Operator Layer
        OP[Operator<br/><i>transparent pipe</i>]
        TRIE[Process Trie UTxO<br/><i>items / processes</i>]
        SF1[Signing Function 1]
        SF2[Signing Function 2]
        SF3[Signing Function N]
        OP -->|manages| TRIE
        OP -->|mints| SF1
        OP -->|mints| SF2
        OP -->|mints| SF3
        SC -->|governs| TRIE
    end

    subgraph User Layer
        U1[User A<br/><i>holds baton</i>]
        U2[User B<br/><i>next in line</i>]
        U3[User N<br/><i>future actor</i>]
    end

    SF1 -.->|signing capability| U1
    SF2 -.->|signing capability| U2
    SF3 -.->|signing capability| U3

    U1 -->|double-signed payload| OP
    U1 -->|passes baton to| U2
```

## Summary

The regulator's workflow:

1. **Analyze the regulation** — extract the data schema, valid transitions,
   parties, qualifications, and deadlines
2. **Maintain a regulation trie** — qualify actors with process-specific
   credentials (licensed carrier, authorized dispatcher, etc.)
3. **Choose a identity provider** — decide which identity infrastructure to
   trust, reference its UTxO
4. **Publish the smart contract** — encode the regulation as a Plutus
   validator that references both the identity and regulation tries
5. **Audit** — verify that operators use the correct smart contract and
   follow the transactions over it

The identity provider's workflow:

1. **Verify entities** — through off-chain identity checks
2. **Maintain the trie** — add, update, or revoke actor keys
3. **Serve multiple regulators** — the same trie can be referenced by
   many smart contracts

The operator's workflow:

1. **Deploy a trie** — create a UTxO governed by the regulator's contract
2. **Mint signing functions** — generate keys, register on-chain, distribute
3. **Verify off-chain** — check user claims against leaf data before
   submitting
4. **Collect and submit** — receive double-signed payloads, batch into
   transactions
5. **Pay fees** — compliance is cheaper than non-compliance

The user's workflow:

1. **Receive** — get a device or access to a signing function
2. **Use** — tap, scan, click
3. **Pass on** — designate the next actor in your final submission

No blockchain knowledge required at any level. The regulator qualifies
actors and publishes rules. The identity provider attests identities. The
operator leverages institutional attestations and follows the rules.
The user participates. The chain enforces.

## Why Cardano

This analysis is based on Cardano's capabilities. The design patterns
described here — signing functions, double signatures, commitment
protocols, the baton pattern — are conceptual and other blockchains are
free to find their own way to implement them.

That said, the on-chain requirements are non-trivial:

- **Merkle Patricia Trie verification in the validator** — the smart
  contract must verify that a leaf update produces the correct new root
  hash. This is Merkle proof verification at every transaction.
- **Reference inputs** — the validator must read the identity and regulation
  trie UTxOs without spending them. This is a Cardano-native feature
  (CIP-31) that enables cross-trie verification without coordination.
- **Native signature verification** — Ed25519 and secp256k1 must be
  available as cheap built-in operations, not expensive general-purpose
  computation.
- **Full transaction context** — the validator must see the previous state,
  the new state, all signatures, and the current slot range in a single
  evaluation.
- **Deterministic payload parsing** — CBOR/COSE decoding inside the
  validator to check that signed data matches the state update.
- **Economically viable validator complexity** — all of the above must
  fit within the execution budget of a single transaction at reasonable
  cost.

Cardano's eUTxO model and Plutus built-ins meet these requirements. The
UTxO model naturally maps to the operator-owns-their-trie pattern — one
UTxO per operator, the validator sees the full spend-and-produce context,
reference inputs enable cross-trie identity and regulation checks, and native
built-ins for Ed25519 and secp256k1 make signature verification practical.

Other chains may offer equivalent primitives. The schema does not depend
on Cardano-specific features at the design level — but the implementation
does depend on a chain that can handle non-trivial smart contract logic
at reasonable cost.
