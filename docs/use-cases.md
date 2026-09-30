# Use cases

## Approved

Create a standard travel request with a clear USD amount at or below the travel policy threshold.
The source row is updated to `Approved`.

```powershell
uv run --project src --no-sync python scripts/demo_dataverse.py --scenario approved
```

## Needs Review

Create client entertainment, premium travel, recurring software, or a non-USD request. The source
row is updated to `Needs Review`.

```powershell
uv run --project src --no-sync python scripts/demo_dataverse.py --scenario review
```

## Flagged

Create a request with no usable amount, a cash advance, or an amount above the policy's upper
threshold. The source row is updated to `Flagged`.

```powershell
uv run --project src --no-sync python scripts/demo_dataverse.py --scenario flagged
```

## Policy change without redeployment

Use `scripts/set_policy.py` to replace a policy Blob, then create a new Dataverse row. The next
request uses the updated policy because policy discovery and reads happen at processing time.

## Integrating with an existing app

Canvas apps, model-driven apps, imports, APIs, and Power Automate flows can all create rows in the
same table. Each producer must provide a unique Expense ID and should leave the output columns
empty. Downstream views and automations can filter on `hep_decision`.
