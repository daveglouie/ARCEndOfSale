#!/usr/bin/env python3
"""
Import Account test data with duplicate checking.

This script creates the "Labubu Industries" account only if it doesn't already exist.

Usage:
    python import_account.py --org <org-alias>

Examples:
    python import_account.py --org orgfarmorg
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_sf_command(command, capture_output=True):
    """Run an sf CLI command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result.stdout if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        raise


def account_exists(org_alias, account_name):
    """Check if an account with the given name already exists."""
    query = f"SELECT Id, Name FROM Account WHERE Name = '{account_name}' LIMIT 1"
    command = f'sf data query --query "{query}" --target-org {org_alias} --json'

    try:
        output = run_sf_command(command)
        result = json.loads(output)

        if result.get('status') == 0 and result.get('result'):
            records = result['result'].get('records', [])
            if records:
                return True, records[0]['Id']

        return False, None
    except Exception as e:
        print(f"Error checking for existing account: {e}")
        return False, None


def import_account(org_alias, account_json_path):
    """Import the account using sf data import tree."""
    command = f'sf data import tree --files {account_json_path} --target-org {org_alias} --json'

    try:
        output = run_sf_command(command)
        result = json.loads(output)

        if result.get('status') == 0:
            # The result can be a dict with 'result' key or a list directly
            import_result = result.get('result', result)

            # Handle both formats: {"result": [...]} or direct list
            if isinstance(import_result, list):
                results = import_result
            elif isinstance(import_result, dict):
                results = import_result.get('results', [])
            else:
                results = []

            if results and len(results) > 0:
                # Find the Account result
                for res in results:
                    if res.get('refId') == 'AccountRef1':
                        return res['id']

        raise Exception(f"Import failed: {result}")
    except Exception as e:
        print(f"Error importing account: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Import Labubu Industries account with duplicate checking'
    )
    parser.add_argument(
        '--org',
        required=True,
        help='Salesforce org alias'
    )

    args = parser.parse_args()
    org_alias = args.org

    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    account_json = script_dir / 'Account.json'

    if not account_json.exists():
        print(f"ERROR: Account.json not found at {account_json}")
        sys.exit(1)

    print(f"Checking if 'Labubu Industries' account already exists in org '{org_alias}'...")

    exists, account_id = account_exists(org_alias, 'Labubu Industries')

    if exists:
        print(f"✓ Account 'Labubu Industries' already exists with ID: {account_id}")
        print("  No action taken.")
        return

    print("✗ Account does not exist. Creating...")

    try:
        account_id = import_account(org_alias, account_json)
        print(f"✓ Successfully created account 'Labubu Industries' with ID: {account_id}")
    except Exception as e:
        print(f"✗ Failed to create account: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
