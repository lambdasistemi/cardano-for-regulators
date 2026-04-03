# The thesis

## Web3 is expensive because it's honest

Blockchain infrastructure is expensive compared to Web2. This is not a
deficiency — it is the cost of guarantees that Web2 cannot provide:
decentralized consensus, immutability, censorship resistance, trustless
execution. Web2 is cheap because it delegates all trust to a single
operator.

But Web2 is not really cheap. For the mass, it is free — and "free"
means the user is the product. The cost is hidden: extracted through
data, attention, and lock-in. The business model pivots, the terms
change, the user has no recourse.

Web3 makes the cost explicit. No hidden extraction, no silent pivot. The
question is whether anyone will pay it.

## Users won't pay per action

People are trained to expect zero friction. Even if each blockchain
transaction costs cents, the cognitive overhead of deciding "is this
worth paying?" on every click destroys the experience. Micropayments are
an unsolved UX problem.

So the challenge is not reducing gas fees. It is finding a model where
the guarantees exist but the payment doesn't leak through to the user.

## The sponsor pays

The answer is: the entity that benefits from the on-chain guarantees
pays for them. Not the user.

Think regulated industries. A bank needs an auditable trail. A supply
chain needs provenance. A credentialing authority needs tamper-proof
records. These entities already pay for compliance infrastructure in
Web2 — proprietary audit systems, third-party certifiers, manual
inspections. Sponsoring blockchain transactions is a different line
item, and potentially cheaper.

The user gets a Web2-like experience backed by Web3 properties.
Honest cost, right payer.

## Regulation is the forcing function

No business voluntarily adds cost. Without external pressure, the
sponsor-pays model is wishful thinking.

Regulation is what compels businesses to need the guarantees that
blockchains naturally provide — auditability, immutability, multi-party
verifiability. When the law demands these properties, sponsoring on-chain
activity becomes the cheapest way to comply. Not an ideological choice,
a pragmatic one.

The viable adoption path:

1. Regulation forces businesses to provide guarantees
2. Businesses sponsor on-chain activity to comply
3. Users get a free experience backed by cryptographic assurance

## Accepting sponsorship means accepting trade-offs

The moment we accept that a sponsor pays, we accept that the sponsor
becomes a gatekeeper. They choose which transactions to fund, which
means they can filter, delay, or impose conditions. A trust dependency
is reintroduced — not as total as Web2, but real.

If the user renounces direct chain access, they cannot unilaterally
write to the blockchain. But they don't need to. They can still
**verify** — and verification is free. Anyone can read the chain.

So the user's role shifts: from transacting to verifying. The business
writes on-chain and pays for it. The user checks that the data is there
and correct. The blockchain becomes a public proof layer, not a
peer-to-peer transaction layer.

## Users don't just verify — they contribute

The user can still produce **signed data**: a credential, a claim, an
attestation about the real world. They hand it to the operator for
inclusion on-chain. The signature is what matters, not the transaction.
The data carries its own authenticity regardless of who posts it.

This separates **authorship** (user signs) from **publication**
(operator pays to post). The blockchain verifies the former; the latter
is logistics.

And the question becomes: what kind of signed data does the operator
need from the user?

## The blockchain as a tamper-proof anchor

A blockchain is an expensive database — especially if used wrong. But it
has one property no other infrastructure provides: **the operator cannot
manipulate it**.

This makes it the perfect anchor for the regulator to constrain the
operator. The regulator encodes rules in a smart contract. The operator
must follow them — not by policy, but by construction. Non-compliant
transactions are rejected by the chain itself.

And critically: **the regulator cannot tamper with the data either**. The
blockchain is neutral ground. It constrains everyone. The operator must
comply, the regulator must be consistent, and the user can verify both.
No single party controls the narrative.

## Time as the neutral witness

The operator could store signed information from users and present it to
the regulator as authentic data. The signatures prove it wasn't
fabricated. But there is a gap: **time**.

If the user signs a timestamp, the regulator must trust the user's
clock. If the operator signs it, the regulator must trust the operator's
clock. Neither is neutral.

The blockchain provides time certificates that neither party produced.
When data is included in a block, it receives a temporal proof that is a
consequence of consensus, not of anyone's claim. One hash on-chain can
timestamp an entire batch of off-chain signed data.

The on-chain anchor provides not just integrity but **temporal
integrity** — verifiable proof of *when* something was committed,
without trusting either party.

## The beacon: regulator-to-user transparency

The most powerful mechanism is the **beacon**. The smart contract can
require that every batch the operator submits includes a commitment from
the regulator — a beacon scoped to that batch, that operator, that time
window.

The operator has its own questions for the user — "attest this data,
sign that claim." But it cannot ask them directly. It must submit its
questions to the regulator first. The regulator vets the request and
wraps it in a beacon — adding whatever disclosures the regulation
requires: compliance status, warnings, policy updates. The operator's
question reaches the user only after being validated and enriched by the
regulator.

The protocol works as follows:

1. The operator submits its questions to the regulator: "I need the user
   to attest these items — vet my request"
2. The regulator validates the request and issues a beacon — the
   operator's questions wrapped in the regulator's disclosures
3. The operator relays the beacon to the user
4. The user signs their data **together with the beacon**
5. The smart contract validates that the beacon the user signed matches
   the regulator's current issuance

The operator pays for this entire cycle because it initiated it — the
batch serves the operator's need to certify its own compliance through
user attestations.

### The beacon is on-chain, not off-chain

The vetting itself is an off-chain operation — the regulator evaluates
the operator through whatever process it uses. But the result is
anchored on-chain. The regulator maintains its own Merkle Patricia Trie
where each operator has a leaf containing the hash of the regulator's
current view — scores, compliance status, flags.

When the regulator issues a beacon, it mints this view on-chain. The
beacon the user receives is not some opaque off-chain token — it is
verifiable against the regulator's on-chain trie root. Anyone looking at
the blockchain can attest that the beacon is the regulator's actual
current assessment of the operator, not something fabricated for the
occasion.

This is what makes the beacon trustworthy without trusting the operator
as a relay. The data is public, the hash is on-chain, the smart contract
checks the match.

The operator **cannot filter the beacon**. If it says "this operator
failed audit last year," the operator still has to relay it — because
without the user's signature over the real beacon, the batch won't
validate on-chain.

And crucially, the operator cannot coast on past reputation. There is no
window to hide behind a stale score — the beacon is refreshed per batch.
An operator whose compliance status just dropped cannot keep presenting
yesterday's clean beacon to collect a few more rounds of user
attestations before the bad news surfaces. The smart contract rejects
any batch that doesn't carry the current beacon. Transparency is not
eventual — it is immediate.

The operator is forced into a transparent pipe between regulator and
user. Not by trust, but by construction.

## The user's one requirement

The user needs one thing: the regulator's public key. With it, the user
can verify that the beacon actually comes from the regulator before
signing over it — they are not blindly signing whatever the operator
hands them.

This is a minimal, reasonable requirement. The regulator's public key is
public by definition — published on official channels, embedded in the
smart contract, verifiable on-chain. It is the single piece of
out-of-band trust the entire system requires.

## Informed consent by construction

The beacon turns the blockchain into a **disclosure channel**. The
regulator can inject information directly into the user's workflow —
sanctions, risk scores, compliance history — using the operator as a
dumb relay.

And the user cannot claim ignorance. Their signature over the beacon is
cryptographic proof of awareness. "I didn't know" is not a defense when
the chain shows you signed over the disclosure.

This is informed consent enforced by protocol, not by policy. No cookie
banner. No terms-of-service nobody reads. The information is in the
data the user signs, and the signature is the acknowledgment.

## The complete picture

A three-way binding where each party is held accountable:

- **The regulator** encodes rules in a smart contract and publishes
  beacons. Cannot retroactively rewrite evidence or selectively enforce.
- **The operator** relays beacons, collects user attestations, submits
  batches. Cannot tamper with data, censor beacons, or deviate from the
  contract.
- **The user** signs contributions and beacons, verifies on-chain state.
  Cannot claim ignorance of disclosed information.

The blockchain is the substrate that makes this possible: a neutral,
immutable, temporally certified anchor that no single party controls.
The regulation defines the protocol. The smart contract enforces it. The
user gets both free access and real guarantees.

This is not about decentralization as ideology. It is about using the
most cost-effective tool to solve a specific problem: multi-party
compliance where no party can be fully trusted — not even the regulator.
