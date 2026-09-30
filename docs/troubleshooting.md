# Troubleshooting

## Dataverse rows remain unprocessed

Check these stages in order:

1. The Dataverse connection reports **Connected** in the Connector Namespace portal.
2. The `dataverse-expense-request-created` trigger config is enabled.
3. The Function app lists `main` with a `connectorTrigger` binding.
4. The Connector Namespace trigger callback URL names `functionName=main`.

Re-run `infra/scripts/postdeploy.ps1` after any Function hostname or key change.

## Dataverse connection is not authorized

Run:

```powershell
./infra/scripts/authorize-dataverse.ps1
```

Authorize with an account that can read and update the Expense Request table. A connection that can
read created rows but cannot update them will start the workflow and then fail at the final tool
call.

## The row is not updated

Confirm:

- `DATAVERSE_MCP_SERVER_URL` and `DATAVERSE_MCP_CLIENT_ID` are set on the Function app
- the Dataverse MCP server exposes `PatchItem_V2`
- the operation is pinned to `hep_expenserequests`
- the connector payload includes `ItemInternalId` or `hep_expenserequestid`
- the authorized Dataverse user has update permission on all four output columns

Search traces for `commondataservice_PatchItem_V2`.

`hep_processedon` is a text column and must use compact ISO 8601 basic UTC format
`YYYYMMDDTHHMMSSZ`. The Dataverse connector rejects colon-separated timestamps for this field.

Keep `hep_reason` at 90 characters or fewer. The connector's current dynamic schema rejects values
over 100 characters even when Dataverse metadata reports a larger column length.

## Demo times out

The Dataverse trigger polls every five minutes. The default demo timeout is 15 minutes. Increase it:

```powershell
uv run --project src --no-sync python scripts/demo_dataverse.py `
  --scenario all --timeout-minutes 25
```

If the Function does not run after one polling interval, troubleshoot the connector trigger rather
than the model or MCP update.

## Schema setup authentication fails

Use one of:

```powershell
pac auth create --environment https://<organization>.crm.dynamics.com
uv run --project src --no-sync python scripts/setup_dataverse_schema.py `
  --environment-url https://<organization>.crm.dynamics.com --auth-source pac
```

or:

```powershell
az login
uv run --project src --no-sync python scripts/setup_dataverse_schema.py `
  --environment-url https://<organization>.crm.dynamics.com --auth-source azure-cli
```
