# Travel & Transportation Expense Policy

**Applies to:** air travel, rail, lodging and hotels, ground transportation,
ride-share and taxis, car rental, and mileage reimbursement.

_Owner: Finance Operations. Travel is pre-planned and usually pre-approved, so the
auto-approve ceiling is higher than the general policy — but premium travel and
foreign-currency receipts still get a human look._

Work the rules in order, **top to bottom; the first rule that matches decides the
outcome**. Every request receives exactly one Dataverse decision status.

## 1. Completeness

If you cannot determine an amount, or the request is too vague to price, it cannot
be auto-processed.

- **Decision:** `Flagged` (needs clarification).

## 2. Cash advances

Travel cash advances require manager sign-off, regardless of amount.

- **Decision:** `Flagged`.

## 3. Premium travel

First-class or business-class airfare, suites, and other premium upgrades always
need review, regardless of amount, so the business justification can be recorded.

- **Decision:** `Needs Review`.

## 4. Currency

Travel receipts are frequently foreign. Evaluate amounts in **US dollars (USD)**; if
the amount is in any other currency, do **not** guess an exchange rate.

- **Decision:** `Needs Review` for FX verification.

## 5. Amount thresholds (USD)

For standard (economy / standard-rate) travel with a clear USD amount:

| Amount (USD)               | Decision       |
| -------------------------- | -------------- |
| $1,000 or less             | `Approved`     |
| Over $1,000, up to $5,000  | `Needs Review` |
| Over $5,000                | `Flagged`      |

Boundary values follow the table exactly: **$1,000 is `Approved`**, **$5,000 is
`Needs Review`**.

## Notes for the reviewer

- Rules 1–4 are the judgment layer and may override the amount thresholds, but only
  for the reasons stated above.
- The `reason` on each decision should name the amount and the rule from **this
  travel policy** that applied.
