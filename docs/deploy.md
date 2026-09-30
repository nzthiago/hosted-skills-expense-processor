# Deploy

## Prepare Dataverse

Install project dependencies and create the schema:

```powershell
uv sync --project src
uv run --project src --no-sync python scripts/setup_dataverse_schema.py `
  --environment-url https://<organization>.crm.dynamics.com
```

The setup command is idempotent. It verifies existing publisher, solution, table, ownership, and
column metadata rather than silently accepting incompatible customizations.

## Configure the azd environment

```powershell
azd env new
azd env set DATAVERSE_ENVIRONMENT_URL https://<organization>.crm.dynamics.com
```

Alternatively set `DATAVERSE_ENVIRONMENT_ID` or `DATAVERSE_ENVIRONMENT_NAME`. The postdeploy script
uses Dataverse Global Discovery to resolve those values to the connector dataset URL.

## Deploy

```powershell
azd up
```

The interactive postprovision hook opens the Connector Namespace portal. Authorize the Dataverse
connection with an account that can read and update the Expense Request table, wait until the
connection reports **Connected**, and return to the terminal.

The postdeploy hook configures the Dataverse `GetOnNewItems_V2` callback directly to the hosted
skill's `main` connector trigger.

## Verify

```powershell
azd env get-values
uv run --project src --no-sync python scripts/demo_dataverse.py --scenario all
```

Expected outputs include non-empty values for:

- `DATAVERSE_CONNECTION_ID`
- `DATAVERSE_MCP_SERVER_URL`
- `DATAVERSE_TABLE_NAME`
- `POLICY_MCP_SERVER_URL`

## Reconfigure without reprovisioning

After changing the Dataverse environment or redeploying the Function app:

```powershell
./infra/scripts/postdeploy.ps1
```

On macOS/Linux:

```bash
./infra/scripts/postdeploy.sh
```

## Cleanup

```powershell
azd down --purge
```

This deletes Azure resources. It does not delete the unmanaged Dataverse solution or table.
