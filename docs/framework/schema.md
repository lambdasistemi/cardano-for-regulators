# The Regulator Schema

How a regulator can use Cardano to enforce a multi-party regulation without
running infrastructure, managing identities, or trusting any single operator.

## Three roles, clean separation

A regulated process involves exactly three roles. Each role has a well-defined
power and a well-defined constraint.

| Role | Power | Constrained by |
|------|-------|----------------|
| **Regulator** | Defines the rules as a smart contract | Nothing — they are the authority |
| **Operator** | Runs infrastructure, pays fees, distributes signing functions | The smart contract — cannot deviate |
| **User** | Uses signing functions, passes the baton | The on-chain authorization — can only act when it's their turn |

The regulator doesn't run anything. The operator can't cheat. The user
doesn't need to trust anyone.

## What the regulator produces

The regulator writes a **smart contract** — the regulation in executable form.
This contract defines:

- **The data schema** — what fields a leaf in the Merkle Patricia Trie must
  contain
- **Valid transitions** — what updates are allowed, in what order, by whom
- **The commitment protocol** — how time windows work, what must be signed,
  what constitutes a valid submission
- **Authorization rules** — how the baton is assigned and passed between actors

The regulator deploys this contract once. Every operator in the market
operates under it. The regulator can audit any operator by checking their
trie against the contract — it's all on-chain, all governed by the same
rules.

The eUTxO model ensures the validator is evaluated at every transaction.
Non-compliant updates are rejected by the chain itself. The regulation is
enforced at the transaction level, not by inspectors after the fact.

## What the operator does

The operator participates in the regulated market. They manage a Merkle
Patricia Trie — one UTxO holding the root hash — containing all items or
processes under their responsibility.

The operator's duties:

1. **Mint signing functions** — generate key pairs, register public keys
   on-chain, distribute the signing capability
2. **Create commitments** — set time-bounded windows in the trie for
   expected actions
3. **Collect submissions** — receive double-signed payloads from users
4. **Submit transactions** — batch updates to the trie, paying all fees
5. **Prove correct computation** — the smart contract verifies that the
   signed payload matches the trie update

The operator is a **transparent pipe**. They choose *when* to batch, but
not *what* goes in. The signed payload is the input, the leaf update is
the output, and the contract verifies they match. The operator cannot
tamper with the data because:

- The commitment is defined by the smart contract
- The payload is signed (tampering invalidates the signature)
- The update is validated by the smart contract
- The new root hash must be consistent with the leaf change

## What the user does

The user interacts with a regulated process without any blockchain knowledge.
They don't have a wallet, don't hold ADA, don't know what Cardano is.

The user's actions:

1. **Receive a signing capability** — a physical device with a secure
   element, an app with a key in the secure enclave, or access to a
   signing service
2. **Perform the regulated action** — tap an NFC chip, scan a QR code,
   press a button in an app
3. **Pass the baton** — when the object or process moves to the next actor,
   the current user's final action designates the next authorized key

From the user's perspective: tap, use, pass on. The cryptography is
invisible.

## The signing function

The atomic unit of the system is not a key, not a device, not a user — it
is a **signing function**. An opaque capability that produces signatures
when invoked, without exposing the private key.

The operator mints signing functions and distributes them. The substrate
is irrelevant:

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

## The double signature

Every state transition requires two signatures:

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

Together they prove: an authorized actor interacted with a specific process
and is submitting a specific, time-bounded state update.

## The commitment protocol

The commitment is what prevents replay, ensures timeliness, and binds
each action to a specific moment in the on-chain state.

```
1. Operator creates a commitment in the leaf
   → the smart contract defines what a valid commitment looks like
   → the commitment includes a slot window (validFrom, validUntil)

2. The signing function signs the payload + commitment
   → the commitment is part of the signed data
   → tampering with the commitment invalidates the signature

3. The actor submits through the operator
   → the operator includes both signatures in the transaction

4. The validator checks:
   → commitment exists in the leaf? (expected action)
   → current slot within the window? (timely)
   → process signature valid over payload + commitment? (authentic)
   → actor key matches the authorized reporter? (authorized)
   → leaf update matches the signed payload? (untampered)

5. The commitment is cleared
   → single-use, no replay possible
```

The commitment is the mechanism that turns a generic signing capability
into a one-shot, time-bounded, authorized action.

## The baton pattern

Authorization to act on a process is a baton that travels through
the real world — physical or digital.

1. The operator creates a leaf with a signing function but no assigned
   actor
2. The first person to interact becomes the authorized actor — their
   key goes into the leaf's `reporterKey` field
3. They perform actions — each producing a double-signed, committed
   payload that the operator feeds into the trie
4. When the process moves to the next party, the current actor's final
   submission includes the next actor's public key — the baton passes
   atomically
5. The new actor is now authorized, the previous actor is locked out
6. The chain continues through the process lifecycle

No user registration. No identity database. No login. Authorization is
determined entirely by the on-chain state. You hold the baton or you
don't.

## Two modes

The same architecture supports two fundamentally different modes:

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

Both modes use:

- The same Merkle Patricia Trie structure
- The same commitment protocol
- The same double signature scheme
- The same baton passing mechanism
- The same smart contract validation

The difference is the trust basis: hardware attestation vs protocol
enforcement. Physical mode is strictly stronger (you get process
guarantees *plus* physical attestation), but process mode covers
regulations that have no physical component.

## Privacy

No single party has the full picture:

| Party | Knows | Doesn't know |
|-------|-------|-------------|
| **Operator** | Public-private key mapping | Who uses the signing function, when, or why |
| **User** | That they interacted with a signing function | The private key |
| **Chain** | Public keys and valid signatures | Any link to real-world identities |
| **Server** (process mode) | That signing requests came in | Who made them or what they mean |
| **Regulator** | That the smart contract was followed | Anything beyond what the contract requires |

The operator mints a private key, registers the public key on-chain, and
distributes the signing capability. The only link between the key and a
real-world identity is held by nobody — the operator doesn't know who
will use it, and the user doesn't know the private key.

Privacy is structural, not policy-based. There is no personal data to
protect because no personal data is collected.

## Summary

The regulator's workflow:

1. **Analyze the regulation** — extract the data schema, valid transitions,
   parties, and deadlines
2. **Write the smart contract** — encode the regulation as a Plutus
   validator that governs the Merkle Patricia Trie
3. **Publish the contract** — operators deploy their tries under it
4. **Audit** — verify any operator's trie against the contract at any time

The operator's workflow:

1. **Deploy a trie** — create a UTxO governed by the regulator's contract
2. **Mint signing functions** — generate keys, register on-chain, distribute
3. **Collect and submit** — receive double-signed payloads, batch into
   transactions
4. **Pay fees** — compliance is cheaper than non-compliance

The user's workflow:

1. **Receive** — get a device or access to a signing function
2. **Use** — tap, scan, click
3. **Pass on** — designate the next actor in your final submission

No blockchain knowledge required at any level. The regulator writes
rules. The operator follows them. The user participates. The chain
enforces.
