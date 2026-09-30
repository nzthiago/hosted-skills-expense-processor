# How it works

## End-to-end flow

1. A user or system creates an `Expense Request` row in Dataverse.
2. The Connector Namespace `GetOnNewItems_V2` trigger polls the configured entity set every five
   minutes.
3. The connector invokes the hosted skill's `main` Function through its `connectorTrigger`
   binding.
4. The skill reads each created row and its Dataverse GUID directly from the connector payload.
5. The skill lists the policy library and reads the category-specific Markdown through its
   least-privilege Blob MCP server.
6. The model applies the first matching policy rule.
7. The skill calls `commondataservice_PatchItem_V2` exactly once to update the original
   Dataverse row.

There is no Storage Queue, normalized intake Blob, or Event Grid subscription in the business
workflow.

## Decisions

The policy files use the same three labels written to `hep_decision`:

- `Approved`
- `Needs Review`
- `Flagged`

The update also sets `hep_reason`, `hep_policyapplied`, and `hep_processedon`.

## Connector boundaries

The Connector Namespace exposes two MCP servers:

- **Expense policy reader:** only Blob `ListFolder_V4` and `GetFileContentByPath_V2`, pinned to the
  policy storage account/container.
- **Expense Dataverse updater:** only `PatchItem_V2`, pinned to the environment and
  `hep_expenserequests` entity set. The model supplies only the source row GUID and output fields.

The Dataverse connection must be authorized by a user who can read and update the Expense Request
table. The connector's access policies permit the Connector Namespace and Function identities to
use that connection.

The trigger polls for created rows only. The skill updates only the GUID delivered for each created
row.
