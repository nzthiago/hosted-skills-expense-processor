#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "azure-storage-blob>=12.19",
#     "azure-identity>=1.16",
# ]
# ///
"""Prepare the deployed policy library."""

from __future__ import annotations

import argparse
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient
from _cloud import resolve_blob_account_url

POLICY_CONTAINER = "policies"
REPO_ROOT = Path(__file__).resolve().parent.parent


def seed_policies(credential: DefaultAzureCredential) -> None:
    account_url = resolve_blob_account_url()
    if not account_url:
        raise SystemExit("Could not resolve OUTPUT_STORAGE_ACCOUNT from the azd environment.")

    with ContainerClient(
        account_url=account_url,
        container_name=POLICY_CONTAINER,
        credential=credential,
    ) as container:
        try:
            container.create_container()
        except ResourceExistsError:
            pass

        existing = next(iter(container.list_blob_names()), None)
        if existing:
            print("Policies already exist; skipping seed.")
            return

        policies = sorted((REPO_ROOT / "src" / "policies").glob("*.md"))
        for policy in policies:
            container.upload_blob(policy.name, policy.read_bytes())
        print(f"Seeded {len(policies)} expense policies.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("seed-policies",))
    args = parser.parse_args()

    credential = DefaultAzureCredential(exclude_azure_cli_credential=True)
    try:
        seed_policies(credential)
    finally:
        credential.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
