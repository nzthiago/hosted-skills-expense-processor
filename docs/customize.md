# Customize

## Change the Dataverse contract

Update these surfaces together:

1. `dataverse/expense-request.schema.json`
2. `src/main.agent.md`
3. the Dataverse MCP `item` schema in `infra/app/blob-policy-connector.bicep`
4. `scripts/demo_dataverse.py`
5. tests and documentation

Run `scripts/setup_dataverse_schema.py` after adding columns. The setup script rejects incompatible
existing definitions instead of changing column types in place.

## Change policy behavior

Edit the Markdown files under `src/policies/` and redeploy, or use `scripts/set_policy.py` to replace
one policy Blob in the deployed environment. Keep the decision labels exactly `Approved`,
`Needs Review`, and `Flagged`.

## Change the polling interval

Edit `recurrenceFrequency` and `recurrenceInterval` in
`infra/app/dataverse-trigger-config.bicep`, then run the postdeploy script. More frequent polling can
increase connector usage.

## Use a different table

Set `DATAVERSE_TABLE_NAME` to the entity set name, such as `hep_expenserequests`. Both the trigger
and `PatchItem_V2` use this plural entity-set name.
