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

## The standing: the regulator's public assessment

The regulator maintains an on-chain Merkle Patricia Trie — the
**standing trie** — where each operator has a leaf. The leaf contains
the hash of the regulator's current assessment: scores, compliance
status, flags, warnings. The regulator updates this trie whenever its
off-chain evaluation of an operator changes.

This is public data on a public chain. Anyone can read it. The standing
trie is the regulator's official, verifiable record of every operator
under its jurisdiction.

## The beacon: sampling the standing

When the operator needs user attestations, it must produce a **beacon**
— a minted token that carries the operator's query to the user. The
minting policy enforces that the beacon includes the operator's current
standing, sampled from the regulator's trie as a reference input at mint
time. The beacon also carries an expiry — a bounded validity window.

The operator has its own questions for the user — "attest this data,
sign that claim." But it cannot present them without first minting a
beacon, and the minting policy won't produce one without reading the
operator's current quality certificate from the regulator's trie. The
operator's questions reach the user wrapped in the regulator's
assessment — not because the operator chose to include it, but because
the smart contract forced it.

The protocol works as follows:

1. The regulator maintains the standing trie on-chain — each operator
   has a leaf with the regulator's current assessment
2. The operator mints a beacon — the minting policy reads the operator's
   leaf from the standing trie (reference input), validates query
   parameters (timestamp, scope), and produces a token that includes the
   standing and an expiry
3. The operator relays the beacon to the user
4. The user verifies the beacon is current (not expired) and authentic
   (matches the regulator's known minting policy), then signs their data
   **together with the beacon**
5. At batch submission, the smart contract validates that the beacon the
   user signed is genuine and not expired

The operator pays for the mint and the batch because it initiated the
cycle — the batch serves the operator's need to certify its own
compliance through user attestations.

### Why minting matters

The standing trie is always on-chain, readable by anyone. But the user
doesn't read the chain — they receive the beacon from the operator. The
mint is what bridges this gap. It produces a verifiable artifact that
attests: "at mint time, this was the regulator's assessment of this
operator." The expiry ensures the artifact cannot be hoarded and
replayed after the assessment changes.

Without the mint, the user would have to query the chain directly to
verify the operator's standing. With it, the minted token is
self-contained proof of currency.

### No stale reputation

The beacon expires. An operator whose compliance status just dropped
cannot keep presenting yesterday's clean beacon to collect more user
attestations before the bad news surfaces. The minting policy reads the
current state of the standing trie — if the regulator has updated the
leaf, the next beacon reflects it. Transparency is not eventual — it is
bounded by the beacon's expiry window.

### The operator as a transparent pipe

The operator **cannot filter the standing**. If the regulator's
assessment says "this operator failed audit last year," the beacon
carries it — because the minting policy included it, and the user
signed over it. The operator relays the regulator's judgment to the
user not by choice, but by construction.

### The standing is the regulator's judgment

The standing trie is entirely under the regulator's control. Its inputs
are heterogeneous: some are derived from on-chain data (inspecting
operator trees, computing compliance metrics from chain history), some
are off-chain (audits, inspections, complaints, legal proceedings), and
some are cross-operator (aggregations across multiple operator trees,
comparative metrics, systemic risk flags). The regulator fuses all of
these into a single leaf per operator.

This means the standing is not a mechanical derivation that anyone can
independently recompute. The operator and the user can see *what* the
regulator committed to — the hash is on-chain, immutable, timestamped —
but not *how* it was computed. The methodology, the weighting, the
off-chain inputs that went into the assessment are all inside the
regulator's process.

This is the irreducible trust point in the system. The blockchain
removes the need to trust the operator. It guarantees data integrity and
temporal integrity. But the regulator's judgment itself — the content of
the standing — must be trusted, or challenged through external
mechanisms: courts, appeals, competing regulators, public scrutiny of
the methodology.

What the chain does guarantee is **accountability**. Every assessment is
timestamped, public, and immutable. If the methodology is later shown to
be flawed or biased, the historical record of what was assessed and when
is there for everyone — operators, users, courts — to examine. The
regulator cannot retroactively revise its own history. The chain doesn't
make the regulator fair, but it makes the regulator answerable.

### Data availability and the burden of proof

The standing trie stores hashes on-chain, not the full certificate
content. There is no guarantee that the pre-image behind a leaf hash can
be reconstructed from the chain alone. This is a deliberate trade-off —
storing full certificates on-chain would be prohibitively expensive.

The auditability burden falls on the party that wants to challenge. The
chain guarantees the *existence* and *timing* of every certificate — the
hashes are immutable — but reconstructing the content is the
challenger's responsibility.

This works because each party naturally holds the data they need:

- **The operator** received every certificate the regulator issued for
  it. If the operator wants to challenge the regulator's assessment in
  court, the operator must have kept its certificate history.
- **The user** signed over beacons that contained the operator's
  standing. If the user wants to challenge the operator, the user must
  have kept the beacons.

In both cases, the chain serves as the arbiter of *whether* the
presented data matches the on-chain hash — not as the archive itself.
The hash settles disputes: if the challenger produces a certificate and
its hash matches the leaf at that point in time, the content is proven
authentic.

The only gap is a third party wanting to audit without having
participated. This is an edge case that could be addressed by regulatory
archiving mandates or content-addressed storage, but the core protocol
does not depend on it.

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
