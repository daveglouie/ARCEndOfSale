#!/usr/bin/env python3
"""
Import test product data with dynamic lookups for renewal replacement, pricebook, and selling model.

This script:
1. Checks if the product already exists (by ProductCode='ECM-LEGACY')
2. If exists, reports the existing Product2 ID and exits (no duplicate created)
3. If not exists:
   - Dynamically looks up ProductSellingModel ID for "Term Annual"
   - Dynamically looks up Standard Pricebook ID (no hardcoded IDs)
   - Looks up the Product2 ID for the replacement product by name
   - Updates Product2.json with the RenewalReplacementProduct__c field
   - Updates PricebookEntry.json with ProductSellingModelId and Pricebook2Id
   - Imports the data using sf data import tree
   - Refreshes relevant decision tables to pick up the new product

The script is idempotent - safe to run multiple times without creating duplicates.
All IDs are dynamically looked up from the target org, making the script portable across orgs.

Usage:
    python import_with_replacement_product.py --org orgfarmorg
    python import_with_replacement_product.py --org orgfarmorg --replacement-product "QuantumBit Generative AI License"
    python import_with_replacement_product.py --org orgfarmorg --skip-dt-refresh
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def query_product_id(org_alias, product_name):
    """
    Query Salesforce for a Product2 ID by name.

    Args:
        org_alias: Salesforce org alias
        product_name: Product name to search for

    Returns:
        Product2 ID or None if not found
    """
    query = f"SELECT Id, Name FROM Product2 WHERE Name = '{product_name}'"

    try:
        result = subprocess.run(
            ["sf", "data", "query", "--query", query, "--target-org", org_alias, "--json"],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        records = data.get("result", {}).get("records", [])

        if not records:
            print(f"✗ Product not found: '{product_name}'")
            return None

        product_id = records[0]["Id"]
        print(f"✓ Found replacement product: '{product_name}' (ID: {product_id})")
        return product_id

    except subprocess.CalledProcessError as e:
        print(f"✗ Error querying for product: {e.stderr}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"✗ Error parsing query result: {e}")
        return None


def update_product_json(product_file, replacement_product_id):
    """
    Update the Product2.json file to include RenewalReplacementProduct__c field.

    Args:
        product_file: Path to Product2.json
        replacement_product_id: Product2 ID to set as replacement
    """
    try:
        with open(product_file, 'r') as f:
            data = json.load(f)

        # Add RenewalReplacementProduct__c to the product record
        if data.get("records") and len(data["records"]) > 0:
            data["records"][0]["RenewalReplacementProduct__c"] = replacement_product_id
            print(f"✓ Updated Product2.json with RenewalReplacementProduct__c = {replacement_product_id}")
        else:
            print("✗ No records found in Product2.json")
            return False

        # Write updated file
        with open(product_file, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    except Exception as e:
        print(f"✗ Error updating Product2.json: {e}")
        return False


def query_product_selling_model_id(org_alias, selling_model_name):
    """
    Query for ProductSellingModel ID by name.

    Args:
        org_alias: Salesforce org alias
        selling_model_name: Name of the selling model (e.g., "Term Annual")

    Returns:
        ProductSellingModel ID or None
    """
    query = f"SELECT Id FROM ProductSellingModel WHERE Name = '{selling_model_name}'"

    try:
        result = subprocess.run(
            ["sf", "data", "query", "--query", query, "--target-org", org_alias, "--json"],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        records = data.get("result", {}).get("records", [])

        if records:
            print(f"✓ Found ProductSellingModel '{selling_model_name}': {records[0]['Id']}")
            return records[0]["Id"]

        print(f"✗ ProductSellingModel '{selling_model_name}' not found")
        return None

    except subprocess.CalledProcessError as e:
        print(f"✗ Error querying for ProductSellingModel: {e.stderr}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"✗ Error parsing query result: {e}")
        return None


def update_pricebook_entry_json(pricebook_entry_file, selling_model_id, pricebook_id):
    """
    Update the PricebookEntry.json file to include ProductSellingModelId and Pricebook2Id.

    Args:
        pricebook_entry_file: Path to PricebookEntry.json
        selling_model_id: ProductSellingModel ID
        pricebook_id: Standard Pricebook2 ID
    """
    try:
        with open(pricebook_entry_file, 'r') as f:
            data = json.load(f)

        if data.get("records") and len(data["records"]) > 0:
            data["records"][0]["ProductSellingModelId"] = selling_model_id
            data["records"][0]["Pricebook2Id"] = pricebook_id
            print(f"✓ Updated PricebookEntry.json with ProductSellingModelId = {selling_model_id}")
            print(f"✓ Updated PricebookEntry.json with Pricebook2Id = {pricebook_id}")
        else:
            print("✗ No records found in PricebookEntry.json")
            return False

        with open(pricebook_entry_file, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    except Exception as e:
        print(f"✗ Error updating PricebookEntry.json: {e}")
        return False


def query_standard_pricebook_id(org_alias):
    """
    Query for the standard pricebook ID.

    Args:
        org_alias: Salesforce org alias

    Returns:
        Standard Pricebook2 ID or None
    """
    query = "SELECT Id FROM Pricebook2 WHERE IsStandard = true"

    try:
        result = subprocess.run(
            ["sf", "data", "query", "--query", query, "--target-org", org_alias, "--json"],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        records = data.get("result", {}).get("records", [])

        if records:
            print(f"✓ Found Standard Pricebook: {records[0]['Id']}")
            return records[0]["Id"]

        print("✗ Standard Pricebook not found")
        return None

    except subprocess.CalledProcessError as e:
        print(f"✗ Error querying for Standard Pricebook: {e.stderr}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"✗ Error parsing query result: {e}")
        return None


def product_exists(org_alias, product_code):
    """
    Check if a product with the given ProductCode already exists.

    Args:
        org_alias: Salesforce org alias
        product_code: Product code to search for

    Returns:
        Tuple of (exists: bool, product_id: str or None, product_name: str or None)
    """
    query = f"SELECT Id, Name, ProductCode FROM Product2 WHERE ProductCode = '{product_code}'"

    try:
        result = subprocess.run(
            ["sf", "data", "query", "--query", query, "--target-org", org_alias, "--json"],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)
        records = data.get("result", {}).get("records", [])

        if records:
            return True, records[0]["Id"], records[0]["Name"]

        return False, None, None

    except subprocess.CalledProcessError as e:
        print(f"✗ Error checking for existing product: {e.stderr}")
        return False, None, None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"✗ Error parsing query result: {e}")
        return False, None, None


def import_data(org_alias, plan_file):
    """
    Import data using sf data import tree.

    Args:
        org_alias: Salesforce org alias
        plan_file: Path to the data import plan JSON
    """
    try:
        print(f"\n→ Importing data from plan: {plan_file}")
        result = subprocess.run(
            ["sf", "data", "import", "tree", "--plan", str(plan_file), "--target-org", org_alias],
            capture_output=True,
            text=True,
            check=True
        )

        print(result.stdout)
        print("✓ Data import completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Error importing data:")
        print(e.stdout)
        print(e.stderr)
        return False


def refresh_decision_tables(org_alias, decision_tables):
    """
    Refresh decision tables using the refresh script.

    Args:
        org_alias: Salesforce org alias
        decision_tables: List of decision table names to refresh

    Returns:
        True if all refreshes succeeded, False otherwise
    """
    if not decision_tables:
        print("\n→ No decision tables to refresh")
        return True

    print(f"\n→ Refreshing {len(decision_tables)} decision table(s)...")

    # Find the refresh script
    script_dir = Path(__file__).parent
    refresh_script = script_dir.parent.parent / "scripts" / "decision_tables" / "refresh_decision_table_standalone.py"

    if not refresh_script.exists():
        print(f"✗ Decision table refresh script not found at: {refresh_script}")
        print("  Skipping decision table refresh.")
        return False

    try:
        # Build command
        tables_arg = ",".join(decision_tables)
        cmd = [
            sys.executable,
            str(refresh_script),
            "--org", org_alias,
            "--tables", tables_arg
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print(result.stdout)
        print("✓ Decision table refresh completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Error refreshing decision tables:")
        print(e.stdout)
        print(e.stderr)
        print("  Warning: Data was imported but decision tables may be stale.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Import test product with renewal replacement product lookup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import with default replacement product and refresh decision tables
  python import_with_replacement_product.py --org orgfarmorg

  # Import with custom replacement product
  python import_with_replacement_product.py --org orgfarmorg --replacement-product "My Product Name"

  # Import without refreshing decision tables
  python import_with_replacement_product.py --org orgfarmorg --skip-dt-refresh

  # Import and refresh custom decision tables
  python import_with_replacement_product.py --org orgfarmorg --decision-tables "Table1,Table2,Table3"
        """
    )

    parser.add_argument(
        "--org",
        required=True,
        help="Salesforce org alias (as configured in SF CLI)"
    )
    parser.add_argument(
        "--replacement-product",
        default="QuantumBit Generative AI License",
        help="Name of the replacement product to lookup (default: QuantumBit Generative AI License)"
    )
    parser.add_argument(
        "--plan",
        default="enterprise-campaign-manager-plan.json",
        help="Data import plan file (default: enterprise-campaign-manager-plan.json)"
    )
    parser.add_argument(
        "--decision-tables",
        default="Price_Book_Entry_Decision_Table_v2",
        help="Comma-separated list of decision tables to refresh after import (default: Price_Book_Entry_Decision_Table_v2)"
    )
    parser.add_argument(
        "--skip-dt-refresh",
        action="store_true",
        help="Skip decision table refresh after import"
    )

    args = parser.parse_args()

    # Get script directory
    script_dir = Path(__file__).parent
    product_file = script_dir / "Product2.json"
    plan_file = script_dir / args.plan

    # Verify files exist
    if not product_file.exists():
        print(f"✗ Product2.json not found at: {product_file}")
        sys.exit(1)

    if not plan_file.exists():
        print(f"✗ Plan file not found at: {plan_file}")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"Import Test Product with Renewal Replacement")
    print(f"{'='*60}")
    print(f"Org: {args.org}")
    print(f"Replacement Product: {args.replacement_product}")
    print(f"{'='*60}\n")

    # Step 1: Check if product already exists
    print("→ Checking if product already exists...")
    exists, existing_id, existing_name = product_exists(args.org, "ECM-LEGACY")

    if exists:
        print(f"✓ Product '{existing_name}' already exists with ID: {existing_id}")
        print("  ProductCode: ECM-LEGACY")
        print("  No action taken.")
        print(f"\n{'='*60}")
        print(f"✓ Product already exists - skipping import")
        print(f"{'='*60}")
        return

    print("✗ Product does not exist. Creating...")

    # Step 2: Look up ProductSellingModel ID for "Term Annual"
    print("\n→ Looking up ProductSellingModel 'Term Annual'...")
    selling_model_id = query_product_selling_model_id(args.org, "Term Annual")
    if not selling_model_id:
        print("\n✗ Failed to find ProductSellingModel 'Term Annual'. Aborting.")
        sys.exit(1)

    # Step 3: Look up Standard Pricebook ID
    print("\n→ Looking up Standard Pricebook...")
    pricebook_id = query_standard_pricebook_id(args.org)
    if not pricebook_id:
        print("\n✗ Failed to find Standard Pricebook. Aborting.")
        sys.exit(1)

    # Step 4: Look up replacement product ID
    print(f"\n→ Looking up replacement product '{args.replacement_product}'...")
    replacement_id = query_product_id(args.org, args.replacement_product)
    if not replacement_id:
        print("\n✗ Failed to find replacement product. Aborting.")
        sys.exit(1)

    # Step 5: Update Product2.json with replacement product ID
    print("\n→ Updating Product2.json...")
    if not update_product_json(product_file, replacement_id):
        print("\n✗ Failed to update Product2.json. Aborting.")
        sys.exit(1)

    # Step 6: Update PricebookEntry.json with ProductSellingModelId and Pricebook2Id
    print("\n→ Updating PricebookEntry.json...")
    pricebook_entry_file = script_dir / "PricebookEntry.json"
    if not update_pricebook_entry_json(pricebook_entry_file, selling_model_id, pricebook_id):
        print("\n✗ Failed to update PricebookEntry.json. Aborting.")
        sys.exit(1)

    # Step 7: Import the data
    if not import_data(args.org, plan_file):
        print("\n✗ Data import failed.")
        sys.exit(1)

    # Step 8: Refresh decision tables
    if not args.skip_dt_refresh:
        decision_tables = [dt.strip() for dt in args.decision_tables.split(",") if dt.strip()]
        if decision_tables:
            refresh_success = refresh_decision_tables(args.org, decision_tables)
            if not refresh_success:
                print("\n⚠ Warning: Decision table refresh encountered errors.")
                print("  The product data was imported successfully, but decision tables may need manual refresh.")
        else:
            print("\n→ No decision tables specified for refresh")
    else:
        print("\n→ Skipping decision table refresh (--skip-dt-refresh flag set)")

    print(f"\n{'='*60}")
    print(f"✓ Import completed successfully!")
    print(f"{'='*60}")
    print(f"\nVerify the data:")
    print(f"  sf data query --query \"SELECT Id, Name, RenewalReplacementProduct__c FROM Product2 WHERE ProductCode='ECM-LEGACY'\" --target-org {args.org}")
    if not args.skip_dt_refresh:
        print(f"\nDecision tables refreshed:")
        for dt in decision_tables:
            print(f"  - {dt}")


if __name__ == "__main__":
    main()
