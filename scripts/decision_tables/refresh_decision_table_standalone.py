#!/usr/bin/env python3
"""
Standalone Decision Table Refresh Script

This script refreshes Salesforce Decision Tables using the Salesforce REST API.
It can perform full or incremental refreshes on one or more decision tables.

Usage:
    python refresh_decision_table_standalone.py --org orgfarmorg --tables Asset_Action_Source_Entries_Decision_Table_V2
    python refresh_decision_table_standalone.py --org orgfarmorg --tables "Table1,Table2,Table3" --incremental
    python refresh_decision_table_standalone.py --org orgfarmorg --tables-file decision_tables.txt
"""

import argparse
import json
import subprocess
import sys
import requests


class DecisionTableRefresh:
    """Refresh Salesforce Decision Tables via REST API"""

    def __init__(self, org_alias, api_version="62.0"):
        self.org_alias = org_alias
        self.api_version = api_version
        self.access_token = None
        self.instance_url = None

    def _get_org_credentials(self):
        """Get access token and instance URL from SF CLI"""
        try:
            result = subprocess.run(
                ["sf", "org", "display", "--target-org", self.org_alias, "--json"],
                capture_output=True,
                text=True,
                check=True
            )
            org_info = json.loads(result.stdout)
            self.access_token = org_info["result"]["accessToken"]
            self.instance_url = org_info["result"]["instanceUrl"]
            print(f"✓ Connected to org: {self.instance_url}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error getting org credentials: {e.stderr}")
            sys.exit(1)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Error parsing org info: {e}")
            sys.exit(1)

    def refresh_decision_table(self, developer_name, is_incremental=False):
        """
        Refresh a single decision table

        Args:
            developer_name: API name of the decision table
            is_incremental: If True, performs incremental refresh; if False, full refresh
        """
        if not self.access_token or not self.instance_url:
            self._get_org_credentials()

        url = f"{self.instance_url}/services/data/v{self.api_version}/actions/standard/refreshDecisionTable"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [
                {
                    "decisionTableApiName": developer_name,
                    "isIncremental": is_incremental
                }
            ]
        }

        refresh_type = "incremental" if is_incremental else "full"
        print(f"\n→ Refreshing '{developer_name}' ({refresh_type})...")

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Handle response (can be list or dict)
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            elif isinstance(result, list):
                print(f"  ✗ Empty response for '{developer_name}'")
                return False

            success = result.get("isSuccess", False)
            if success:
                print(f"  ✓ Success: {result.get('outputValues', {}).get('Status', 'Completed')}")
                return True
            else:
                print(f"  ✗ Failed to refresh '{developer_name}'")
                errors = result.get("errors", [])
                for error in errors:
                    if isinstance(error, dict):
                        print(f"    Error: {error.get('message', 'Unknown error')}")
                    else:
                        print(f"    Error: {error}")
                return False

        except requests.exceptions.HTTPError as e:
            print(f"  ✗ HTTP Error: {e}")
            print(f"    Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def refresh_multiple(self, developer_names, is_incremental=False):
        """
        Refresh multiple decision tables

        Args:
            developer_names: List of decision table API names
            is_incremental: If True, performs incremental refresh on all tables

        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0

        print(f"Refreshing {len(developer_names)} decision table(s)...")

        for name in developer_names:
            name = name.strip()
            if not name:
                continue

            if self.refresh_decision_table(name, is_incremental):
                success_count += 1
            else:
                failure_count += 1

        print(f"\n{'='*60}")
        print(f"Results: {success_count} succeeded, {failure_count} failed")
        print(f"{'='*60}")

        return success_count, failure_count


def load_tables_from_file(filepath):
    """Load decision table names from a file (one per line or comma-separated)"""
    tables = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Support both newline-separated and comma-separated
                    if ',' in line:
                        tables.extend([t.strip() for t in line.split(',') if t.strip()])
                    else:
                        tables.append(line)
        return tables
    except FileNotFoundError:
        print(f"✗ Error: File '{filepath}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Refresh Salesforce Decision Tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Refresh a single table (full refresh)
  python refresh_decision_table_standalone.py --org orgfarmorg --tables MyDecisionTable

  # Refresh multiple tables (comma-separated)
  python refresh_decision_table_standalone.py --org orgfarmorg --tables "Table1,Table2,Table3"

  # Incremental refresh
  python refresh_decision_table_standalone.py --org orgfarmorg --tables MyDecisionTable --incremental

  # Load tables from a file
  python refresh_decision_table_standalone.py --org orgfarmorg --tables-file decision_tables.txt
        """
    )

    parser.add_argument(
        "--org",
        required=True,
        help="Salesforce org alias (as configured in SF CLI)"
    )
    parser.add_argument(
        "--tables",
        help="Decision table API name(s). Comma-separated for multiple tables."
    )
    parser.add_argument(
        "--tables-file",
        help="Path to file containing decision table names (one per line or comma-separated)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Perform incremental refresh instead of full refresh"
    )
    parser.add_argument(
        "--api-version",
        default="62.0",
        help="Salesforce API version (default: 62.0)"
    )

    args = parser.parse_args()

    # Validate input
    if not args.tables and not args.tables_file:
        parser.error("Either --tables or --tables-file must be specified")

    if args.tables and args.tables_file:
        parser.error("Cannot specify both --tables and --tables-file")

    # Load decision table names
    if args.tables_file:
        tables = load_tables_from_file(args.tables_file)
    else:
        tables = [t.strip() for t in args.tables.split(',') if t.strip()]

    if not tables:
        print("✗ Error: No decision tables specified")
        sys.exit(1)

    # Perform refresh
    refresher = DecisionTableRefresh(args.org, args.api_version)
    success_count, failure_count = refresher.refresh_multiple(tables, args.incremental)

    # Exit with non-zero status if any failures
    sys.exit(0 if failure_count == 0 else 1)


if __name__ == "__main__":
    main()
