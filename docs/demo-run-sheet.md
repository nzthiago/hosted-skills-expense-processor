# Dataverse expense processor demo run sheet

## Demo objective

Show three new Dataverse Expense Request rows flowing directly through the hosted skill and being
updated in place as:

- `Approved`
- `Needs Review`
- `Flagged`

The business flow is Dataverse connector trigger -> hosted skill -> Dataverse row update. There is
no business Storage Queue or Event Grid subscription.

## Before the session

Complete these checks 30-60 minutes before presenting:

1. Confirm the `dataverse-expense-request-created` trigger is `Enabled`.
2. Confirm Function `main` has a `connectorTrigger` binding.
3. Confirm the Dataverse and Blob connections report `Connected`.
4. Run the full demo once and retain the successfully processed rows as fallback rows.
5. Open the `Expense Requests` table with these columns visible:
   - Expense ID
   - Description
   - Amount
   - Category
   - Decision
   - Reason
   - Policy applied
   - Processed on
6. Keep two browser tabs ready:
   - Dataverse Expense Requests table
   - Azure Function Application Insights transaction search
7. Keep a terminal open at the repository root with Azure CLI authentication already active.
8. Configure the external Python environment:

   ```powershell
   $env:UV_PROJECT_ENVIRONMENT = Join-Path $HOME ".cache\hosted-skills-expense-processor"
   uv sync --project src
   ```

## Primary run: 12 minutes

| Time | Presenter action | Talk track / expected result |
| --- | --- | --- |
| 0:00-0:45 | Show the Expense Requests table. | Point out that Dataverse is both the entry point and system of record. The output columns are initially empty. |
| 0:45-1:45 | Show the three policy files or summarize their thresholds. | Explain that policy is externalized in Markdown and read at runtime rather than embedded in the prompt. |
| 1:45-2:30 | Run the demo command below. | The script creates all three rows immediately, then waits for Dataverse updates. Capture the three row IDs shown in the terminal. |
| 2:30-4:00 | Refresh Dataverse and locate the three new Expense IDs. | Show that all input rows exist and their output fields are blank while the connector polling cycle runs. |
| 4:00-6:30 | Explain the architecture while waiting. | Dataverse polls for created rows, invokes Function `main` directly, the skill reads the appropriate policy through Blob MCP, then calls the table-pinned Dataverse update tool. |
| 6:30-8:30 | Refresh the table every 30-45 seconds. | Rows should begin receiving Decision, Reason, Policy applied, and Processed on values. Avoid rapid refreshes. |
| 8:30-10:30 | Open each completed row. | Show `Approved` for airfare, `Needs Review` for the client dinner, and `Flagged` for the workstation. Tie each result to its policy rule. |
| 10:30-11:30 | Return to the list view. | Emphasize that the original rows were updated in place; no result queue or duplicate output record was created. |
| 11:30-12:00 | Close on extensibility. | Explain that changing a policy document changes future decisions without redeploying the hosted skill. |

Run from the repository root:

```powershell
uv run --project src --no-sync python scripts\demo_dataverse.py `
  --scenario all --timeout-minutes 15
```

Expected scenarios:

| Expense | Policy | Expected decision |
| --- | --- | --- |
| $450 standard airfare | `travel-policy.md` | `Approved` |
| $450 client dinner | `meals-entertainment-policy.md` | `Needs Review` |
| $5,000 workstation | `equipment-software-policy.md` | `Flagged` |

The final rows should contain a reason of at most 90 characters and a compact UTC processing
timestamp in `YYYYMMDDTHHMMSSZ` format.

## Presenter checkpoints

Use these checkpoints to decide whether to continue live or switch to fallback:

- **By 2:30:** all three row IDs must be printed and visible in Dataverse.
- **By 7:30:** at least one row should have a populated Decision.
- **By 10:00:** all three rows should be complete.
- If no row is complete by 7:30, start the fallback rather than waiting silently.

## Fallback: pre-processed rows

Use this when connector polling, authentication, model access, or the venue network delays the
live run.

1. Leave the newly created rows visible to prove live Dataverse ingestion worked.
2. Say: "The connector is asynchronous and the polling cycle is delayed in this environment, so
   I’ll use the validated run from the pre-demo check to show the completed output."
3. Filter the table to the three retained fallback Expense IDs.
4. Open each fallback row and show:
   - the original input fields
   - the expected decision
   - the policy filename
   - the generated reason
   - the processing timestamp
5. Return to the architecture and reiterate that the same source row was updated.
6. If useful, open Application Insights and show a prior successful
   `POST /runtime/webhooks/connector` invocation.

Do not manually populate the live demo rows during the presentation. A clearly labeled prior
successful run is more credible than manufacturing a success state.

## Fast fallback: one scenario

If time is short but the service is healthy, run only the Approved scenario:

```powershell
uv run --project src --no-sync python scripts\demo_dataverse.py `
  --scenario approved --timeout-minutes 10
```

Then use retained rows to show `Needs Review` and `Flagged`.

## Recovery commands

Refresh the direct trigger configuration after a Function key or hostname change:

```powershell
./infra/scripts/configure-dataverse-trigger.ps1
```

Confirm the Function binding:

```powershell
$resourceGroup = azd env get-value AZURE_RESOURCE_GROUP_NAME
$functionName = azd env get-value AZURE_FUNCTION_NAME

az functionapp function show `
  --resource-group $resourceGroup `
  --name $functionName `
  --function-name main `
  --query "config.bindings"
```

If rows exist but remain unprocessed, check Application Insights in this order:

1. Was `POST /runtime/webhooks/connector` invoked?
2. Did policy Blob MCP calls succeed?
3. Did `commondataservice_PatchItem_V2` run?
4. Does the exception identify connection authorization, table, row ID, or item fields?

## Close

"Dataverse is the intake channel and the system of record. The hosted skill applies policy from
governed documents and writes the explainable result back to the same business row, without
introducing a business queue or Event Grid hop."
