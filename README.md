# Dataverse expense processor hosted skill

An Azure Functions hosted skill that processes expense requests end to end in Microsoft Dataverse.
A created `Expense Request` row starts the flow. The skill selects the applicable policy from Blob
Storage and updates that same row with one of three outcomes: **Approved**, **Needs Review**, or
**Flagged**.

## What changed from the queue sample

- Dataverse `GetOnNewItems_V2` replaces the `expense-requests` Storage Queue trigger.
- The Dataverse connector callback invokes the hosted skill directly.
- Dataverse `PatchItem_V2` update replaces the three outcome queues.
- The source row receives `Decision`, `Reason`, `Policy applied`, and `Processed on`.
- The demo creates real Dataverse rows and waits for their final updates.

## Dataverse row contract

The included unmanaged solution creates the `Expense Request` table:

| Field | Logical name | Direction |
| --- | --- | --- |
| Expense ID | `hep_expenseid` | Input / primary name |
| Description | `hep_description` | Input |
| Amount | `hep_amount` | Input |
| Currency | `hep_currency` | Input |
| Vendor | `hep_vendor` | Input |
| Category | `hep_category` | Input |
| Submitted by | `hep_submittedby` | Input |
| Decision | `hep_decision` | Output |
| Reason | `hep_reason` | Output |
| Policy applied | `hep_policyapplied` | Output |
| Processed on | `hep_processedon` | Output |

`Decision` is set to exactly `Approved`, `Needs Review`, or `Flagged`.
`Reason` is limited to 90 characters for connector compatibility. `Processed on` uses compact UTC
format `YYYYMMDDTHHMMSSZ`.

## Prerequisites

- Azure subscription with permission to deploy the included infrastructure
- Existing Power Platform environment with Dataverse
- Azure CLI, Azure Developer CLI, `uv`, and Python 3.13
- Power Platform CLI (`pac`) recommended for Dataverse setup; Azure CLI authentication is also
  supported
- Permission to create Dataverse customizations and authorize a Dataverse connector connection

## 1. Install dependencies

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path $HOME ".cache\hosted-skills-expense-processor"
uv sync --project src
```

This keeps the Python environment outside the repository.

## 2. Create the Dataverse schema

Use the environment URL directly:

```powershell
uv run --project src --no-sync python scripts/setup_dataverse_schema.py `
  --environment-url https://<organization>.crm.dynamics.com
```

You can use `--environment-id` or `--environment-name` instead. The script creates or verifies the
publisher, unmanaged solution, table, and all input/output columns described in
`dataverse/expense-request.schema.json`.

## 3. Configure and deploy

```powershell
azd auth login
az login
azd env new
azd env set DATAVERSE_ENVIRONMENT_URL https://<organization>.crm.dynamics.com
azd up
```

During `azd up`:

1. Azure resources and the Connector Namespace are provisioned.
2. A browser opens so you can authorize the Dataverse connection.
3. The policy documents are seeded into Blob Storage.
4. The Function app is deployed.
5. The Dataverse created-row trigger is connected directly to the hosted skill's `main` function.

Instead of the URL, set `DATAVERSE_ENVIRONMENT_ID` or `DATAVERSE_ENVIRONMENT_NAME`.

## 4. Run the full demo

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path $HOME ".cache\hosted-skills-expense-processor"
uv run --project src --no-sync python scripts/demo_dataverse.py --scenario all
```

The command creates three unique Dataverse rows and waits for:

| Scenario | Policy | Expected result |
| --- | --- | --- |
| $450 standard airfare | `travel-policy.md` | `Approved` |
| $450 client dinner | `meals-entertainment-policy.md` | `Needs Review` |
| $5,000 workstation | `equipment-software-policy.md` | `Flagged` |

The connector trigger polls every five minutes, so a full run can take several minutes. The script
creates all three rows before polling, refreshes Dataverse authentication if needed, and prints each
row ID, final decision, reason, policy, and processing timestamp. Use `--no-wait` to create rows
without polling.

## Demo talk track

For a timed presenter script, checkpoints, and fallback path, see
[`docs/demo-run-sheet.md`](docs/demo-run-sheet.md).

1. Open the `Expense Requests` Dataverse table and show the output columns are empty.
2. Run `scripts/demo_dataverse.py --scenario all`.
3. Explain that the Dataverse connector detects new rows and calls the Function connector webhook.
4. Show the hosted skill reading category-specific policy Markdown through a read-only Blob MCP
   server.
5. Refresh Dataverse and show all three source rows updated in place.
6. Replace a policy with `scripts/set_policy.py`, submit another row, and show behavior changing
   without a code deployment.

## Architecture

1. Dataverse Connector Namespace polls `hep_expenserequests` for created rows.
2. The connector invokes the hosted skill's `connector_trigger` directly.
3. The skill extracts the Dataverse row fields and row GUID from the connector payload.
4. The skill lists and reads the applicable Markdown policy through the Blob MCP server.
5. The skill calls the Dataverse MCP server's `PatchItem_V2` update operation once for the source
   row.

The Dataverse connection is OAuth-authorized interactively. The hosted skill can invoke only the
single table-pinned update operation exposed by its MCP server.

## Key files

- `dataverse/expense-request.schema.json` — Dataverse solution and table contract
- `scripts/setup_dataverse_schema.py` — repeatable schema setup and verification
- `scripts/demo_dataverse.py` — end-to-end three-outcome demo
- `src/main.agent.md` — hosted skill trigger and policy instructions
- `infra/app/blob-policy-connector.bicep` — Blob read and Dataverse update MCP servers
- `infra/app/dataverse-trigger-config.bicep` — Dataverse created-row trigger

See `docs/deploy.md`, `docs/how-it-works.md`, and `docs/troubleshooting.md` for details.
