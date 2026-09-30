#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Create Dataverse expense requests and wait for the hosted skill decisions."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import setup_dataverse_schema  # noqa: E402

DEFAULT_TABLE = "hep_expenserequests"
DEFAULT_TIMEOUT_MINUTES = 15
DEFAULT_POLL_SECONDS = 15

SCENARIOS = {
    "approved": {
        "description": "Round-trip airfare for customer workshop",
        "amount": "450",
        "currency": "USD",
        "vendor": "Contoso Travel",
        "category": "travel",
        "submitted_by": "demo@contoso.com",
        "expected": "Approved",
    },
    "review": {
        "description": "Client dinner after quarterly planning meeting",
        "amount": "450",
        "currency": "USD",
        "vendor": "Fabrikam Grill",
        "category": "meals and entertainment",
        "submitted_by": "demo@contoso.com",
        "expected": "Needs Review",
    },
    "flagged": {
        "description": "High-end workstation and accessories",
        "amount": "5000",
        "currency": "USD",
        "vendor": "Adventure Works Hardware",
        "category": "equipment and software",
        "submitted_by": "demo@contoso.com",
        "expected": "Flagged",
    },
}


def _azd_value(key: str, environment: str | None) -> str | None:
    azd_path = shutil.which("azd")
    if azd_path is None:
        return None
    command = [azd_path, "env", "get-value", key, "-C", str(ROOT), "--no-prompt"]
    if environment:
        command.extend(["--environment", environment])
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or not value or "key not found" in value.lower():
        return None
    return value


def _environment_url(args: argparse.Namespace) -> str:
    url = args.environment_url or _azd_value(
        "DATAVERSE_ENVIRONMENT_URL",
        args.azd_environment,
    )
    environment_id = args.environment_id or _azd_value(
        "DATAVERSE_ENVIRONMENT_ID",
        args.azd_environment,
    )
    environment_name = args.environment_name or _azd_value(
        "DATAVERSE_ENVIRONMENT_NAME",
        args.azd_environment,
    )
    if url:
        return url.rstrip("/")
    if environment_id or environment_name:
        return setup_dataverse_schema.resolve_environment_url(
            environment_id=environment_id,
            environment_name=environment_name,
        )
    raise RuntimeError(
        "Set --environment-url, --environment-id, or --environment-name, "
        "or select an azd environment containing Dataverse settings."
    )


def _create_row(
    environment_url: str,
    token: str,
    table_name: str,
    values: dict[str, str],
) -> str:
    response = setup_dataverse_schema._request(
        environment_url,
        token,
        "POST",
        table_name,
        body=values,
    )
    primary_key = f"{table_name.removesuffix('s')}id"
    row_id = response.get(primary_key) if isinstance(response, dict) else None
    if not isinstance(row_id, str) or not row_id:
        raise RuntimeError("Dataverse created the row but did not return its row ID.")
    return row_id


def _read_row(
    environment_url: str,
    token: str,
    table_name: str,
    row_id: str,
) -> dict[str, Any]:
    columns = "hep_expenseid,hep_decision,hep_reason,hep_policyapplied,hep_processedon"
    response = setup_dataverse_schema._request(
        environment_url,
        token,
        "GET",
        f"{table_name}({row_id})?$select={columns}",
    )
    if not isinstance(response, dict):
        raise RuntimeError("Dataverse returned an unexpected row response.")
    return response


def _wait_for_decision(
    environment_url: str,
    token: str,
    auth_source: str,
    table_name: str,
    row_id: str,
    timeout_minutes: int,
    poll_seconds: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_minutes * 60
    while True:
        try:
            row = _read_row(environment_url, token, table_name, row_id)
        except RuntimeError as exc:
            if "failed with HTTP 401" not in str(exc):
                raise
            token = setup_dataverse_schema._acquire_dataverse_access_token(
                environment_url,
                auth_source,
            )
            row = _read_row(environment_url, token, table_name, row_id)
        if row.get("hep_decision"):
            return row
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timed out waiting for Dataverse row {row_id} to be updated."
            )
        time.sleep(poll_seconds)


def _expense_id(label: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"EXP-DV-{timestamp}-{label.upper()}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=(*SCENARIOS, "all"),
        default="all",
        help="Demo outcome to submit. Default: all three outcomes.",
    )
    parser.add_argument("--environment-url")
    parser.add_argument("--environment-id")
    parser.add_argument("--environment-name")
    parser.add_argument("--azd-environment")
    parser.add_argument(
        "--table",
        default=None,
        help=f"Dataverse entity set name. Default: {DEFAULT_TABLE}",
    )
    parser.add_argument(
        "--auth-source",
        choices=("auto", "pac", "azure-cli"),
        default="auto",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=DEFAULT_TIMEOUT_MINUTES,
    )
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--no-wait", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    environment_url = _environment_url(args)
    table_name = (
        args.table
        or _azd_value("DATAVERSE_TABLE_NAME", args.azd_environment)
        or DEFAULT_TABLE
    )
    token = setup_dataverse_schema._acquire_dataverse_access_token(
        environment_url,
        args.auth_source,
    )
    labels = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    created_rows = []
    failures = 0

    print(f"Dataverse environment: {environment_url}")
    print(f"Expense Request table: {table_name}")
    for label in labels:
        scenario = SCENARIOS[label]
        expense_id = _expense_id(label)
        values = {
            "hep_expenseid": expense_id,
            "hep_description": scenario["description"],
            "hep_amount": scenario["amount"],
            "hep_currency": scenario["currency"],
            "hep_vendor": scenario["vendor"],
            "hep_category": scenario["category"],
            "hep_submittedby": scenario["submitted_by"],
        }
        row_id = _create_row(environment_url, token, table_name, values)
        print(f"\nCreated {label} request: {expense_id}")
        print(f"Dataverse row ID: {row_id}")
        created_rows.append((label, scenario, row_id))

    if args.no_wait:
        return 0

    for label, scenario, row_id in created_rows:
        row = _wait_for_decision(
            environment_url,
            token,
            args.auth_source,
            table_name,
            row_id,
            args.timeout_minutes,
            args.poll_seconds,
        )
        actual = row.get("hep_decision")
        expected = scenario["expected"]
        print(f"Decision: {actual}")
        print(f"Policy: {row.get('hep_policyapplied')}")
        print(f"Reason: {row.get('hep_reason')}")
        print(f"Processed: {row.get('hep_processedon')}")
        if actual != expected:
            failures += 1
            print(f"Expected: {expected}", file=sys.stderr)

    if failures:
        raise RuntimeError(f"{failures} demo scenario(s) returned an unexpected result.")
    if not args.no_wait:
        print("\nDemo complete: Dataverse rows were updated with all requested outcomes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
