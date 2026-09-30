from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_schema_contains_input_and_output_columns(self) -> None:
        schema = json.loads(
            (ROOT / "dataverse" / "expense-request.schema.json").read_text(
                encoding="utf-8"
            )
        )
        columns = {
            column["logicalName"]
            for column in schema["table"]["columns"]
        }

        self.assertEqual(schema["table"]["entitySetName"], "hep_expenserequests")
        self.assertTrue(
            {
                "hep_expenseid",
                "hep_amount",
                "hep_decision",
                "hep_reason",
                "hep_policyapplied",
                "hep_processedon",
            }.issubset(columns)
        )

    def test_agent_uses_connector_trigger_and_dataverse_update(self) -> None:
        agent = (ROOT / "src" / "main.agent.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("type: connector_trigger", agent)
        self.assertIn("commondataservice_PatchItem_V2", agent)
        self.assertIn("YYYYMMDDTHHMMSSZ", agent)
        self.assertIn("at most 90 characters", agent)
        self.assertNotIn("queue_trigger", agent)
        self.assertNotIn("blob_trigger", agent)

    def test_mcp_exposes_only_policy_reads_and_dataverse_update(self) -> None:
        config = json.loads((ROOT / "src" / "mcp.json").read_text(encoding="utf-8"))
        tools = {
            tool
            for server in config["servers"].values()
            for tool in server["tools"]
        }

        self.assertIn("commondataservice_PatchItem_V2", tools)
        self.assertNotIn("azurequeues_PutMessage_V2", tools)

    def test_infrastructure_has_dataverse_trigger(self) -> None:
        trigger = (
            ROOT / "infra" / "app" / "dataverse-trigger-config.bicep"
        ).read_text(encoding="utf-8")
        main = (ROOT / "infra" / "main.bicep").read_text(encoding="utf-8")
        postdeploy = (
            ROOT / "infra" / "scripts" / "postdeploy.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn("GetOnNewItems_V2", trigger)
        self.assertIn("DATAVERSE_MCP_SERVER_URL", main)
        self.assertNotIn("storage-queues.bicep", main)
        self.assertNotIn("eventgrid", postdeploy.lower())


if __name__ == "__main__":
    unittest.main()
