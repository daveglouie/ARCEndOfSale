#!/usr/bin/env python3
"""
Import test quote with quote line item, automatic repricing, order creation, and asset generation.

This script:
1. Checks if dependencies exist (Account, Product, PricebookEntry)
2. Looks up necessary IDs dynamically
3. Finds an available quote name (appends number if duplicate exists)
4. Creates Opportunity, Quote, and QuoteLineItem
5. Automatically reprices the quote using RepriceQuotesPST Apex class
6. Creates an order from the quote using CreateOrderFromQuote action
7. Activates the order (sets Status='Activated') to trigger asset creation
8. Uses standard Salesforce Data Tree format

If a quote with the same name already exists, the script automatically appends
an incremental number (e.g., "Test Quote 1", "Test Quote 2") to find an
available name.

Note: AppUsageAssignment with AppUsageType=RevenueLifecycleManagement is
automatically created by Salesforce when the Quote is inserted, so it is
NOT included in the data import plan.

Usage:
    python import_quote.py --org orgfarmorg
    python import_quote.py --org orgfarmorg --quote-name "Custom Quote" --quantity 25
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import date
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


def query_record(org_alias, sobject, where_clause, fields="Id"):
    """Query for a single record."""
    query = f"SELECT {fields} FROM {sobject} WHERE {where_clause} LIMIT 1"
    command = f'sf data query --query "{query}" --target-org {org_alias} --json'

    try:
        output = run_sf_command(command)
        result = json.loads(output)

        if result.get('status') == 0 and result.get('result'):
            records = result['result'].get('records', [])
            if records:
                return records[0]

        return None
    except Exception as e:
        print(f"Error querying {sobject}: {e}")
        return None


def check_dependencies(org_alias):
    """Check if required records exist and return their IDs."""
    print("→ Checking dependencies...")

    # Check for Account
    account = query_record(org_alias, "Account", "Name = 'Labubu Industries'", "Id, Name")
    if not account:
        print("✗ Account 'Labubu Industries' not found")
        print("  Run: cd ../test_accounts && python import_account.py --org " + org_alias)
        return None
    print(f"✓ Found Account: {account['Name']} ({account['Id']})")

    # Check for Product
    product = query_record(org_alias, "Product2", "ProductCode = 'ECM-LEGACY'", "Id, Name, ProductCode")
    if not product:
        print("✗ Product 'Enterprise Campaign Manager (Legacy)' not found")
        print("  Run: cd ../test_products && python import_with_replacement_product.py --org " + org_alias)
        return None
    print(f"✓ Found Product: {product['Name']} ({product['Id']})")

    # Check for PricebookEntry
    pricebook_entry = query_record(
        org_alias,
        "PricebookEntry",
        f"Product2Id = '{product['Id']}' AND Pricebook2.IsStandard = true AND IsActive = true",
        "Id, UnitPrice, Pricebook2Id"
    )
    if not pricebook_entry:
        print(f"✗ PricebookEntry not found for product {product['Id']}")
        print("  Ensure the product has a standard pricebook entry")
        return None
    print(f"✓ Found PricebookEntry: {pricebook_entry['Id']} (Price: ${pricebook_entry['UnitPrice']})")

    # Get current user ID
    user = query_record(org_alias, "User", "Username != null", "Id, Name")
    if not user:
        print("✗ Could not get current user")
        return None
    print(f"✓ Current User: {user['Name']} ({user['Id']})")

    return {
        'account_id': account['Id'],
        'account_name': account['Name'],
        'product_id': product['Id'],
        'product_name': product['Name'],
        'pricebook_entry_id': pricebook_entry['Id'],
        'pricebook_id': pricebook_entry['Pricebook2Id'],
        'unit_price': pricebook_entry['UnitPrice'],
        'user_id': user['Id']
    }


def find_available_quote_name(org_alias, base_quote_name):
    """
    Find an available quote name by appending incremental numbers if duplicates exist.

    Returns:
        Tuple of (available_name, is_original) where is_original indicates if the base name was available
    """
    # Check if base name is available
    quote = query_record(org_alias, "Quote", f"Name = '{base_quote_name}'", "Id, Name")
    if not quote:
        return base_quote_name, True

    # Base name exists, find the next available numbered version
    print(f"  Quote '{base_quote_name}' already exists, finding next available number...")

    counter = 1
    while True:
        numbered_name = f"{base_quote_name} {counter}"
        quote = query_record(org_alias, "Quote", f"Name = '{numbered_name}'", "Id, Name")

        if not quote:
            print(f"  → Will use name: '{numbered_name}'")
            return numbered_name, False

        counter += 1

        # Safety check to prevent infinite loop
        if counter > 1000:
            raise Exception("Too many existing quotes with similar names (>1000)")


def create_opportunity_json(deps, opp_name):
    """Create Opportunity.json."""
    return {
        "records": [
            {
                "attributes": {
                    "type": "Opportunity",
                    "referenceId": "OpportunityRef1"
                },
                "Name": opp_name,
                "AccountId": deps['account_id'],
                "StageName": "Prospecting",
                "CloseDate": "2026-12-31"
            }
        ]
    }


def create_quote_json(deps, quote_name):
    """Create Quote.json with the necessary data."""
    # Get today's date in YYYY-MM-DD format
    today = date.today().isoformat()

    return {
        "records": [
            {
                "attributes": {
                    "type": "Quote",
                    "referenceId": "QuoteRef1"
                },
                "Name": quote_name,
                "OpportunityId": "@OpportunityRef1",
                "Pricebook2Id": deps['pricebook_id'],
                "QuoteAccountId": deps['account_id'],
                "StartDate": today
            }
        ]
    }


def create_quote_plan():
    """Create data import plan."""
    files = [
        {
            "sobject": "Opportunity",
            "files": ["Opportunity.json"],
            "saveRefs": True,
            "resolveRefs": False
        },
        {
            "sobject": "Quote",
            "files": ["Quote.json"],
            "saveRefs": True,
            "resolveRefs": True
        },
        {
            "sobject": "QuoteLineItem",
            "files": ["QuoteLineItem.json"],
            "saveRefs": False,
            "resolveRefs": True
        }
    ]

    return files


def create_quote_line_item_json(deps, quantity):
    """Create QuoteLineItem.json."""
    # Get today's date in YYYY-MM-DD format
    today = date.today().isoformat()

    return {
        "records": [
            {
                "attributes": {
                    "type": "QuoteLineItem",
                    "referenceId": "QuoteLineItemRef1"
                },
                "QuoteId": "@QuoteRef1",
                "Product2Id": deps['product_id'],
                "PricebookEntryId": deps['pricebook_entry_id'],
                "Quantity": quantity,
                "UnitPrice": deps['unit_price'],
                "StartDate": today,
                "SubscriptionTerm": 1,
                "PeriodBoundary": "Anniversary"
            }
        ]
    }




def import_data(org_alias, plan_file):
    """Import data using sf data import tree."""
    try:
        print(f"\n→ Importing quote data from plan: {plan_file}")
        result = subprocess.run(
            ["sf", "data", "import", "tree", "--plan", str(plan_file), "--target-org", org_alias, "--json"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse JSON result to extract Quote ID
        import_result = json.loads(result.stdout)

        # Display the table output (reconstruct from JSON)
        if import_result.get('status') == 0 and import_result.get('result'):
            results = import_result.get('result', [])
            if results:
                print("Import Results")
                print("┌" + "─" * 19 + "┬" + "─" * 15 + "┬" + "─" * 20 + "┐")
                print("│ Reference ID      │ Type          │ ID                 │")
                print("├" + "─" * 19 + "┼" + "─" * 15 + "┼" + "─" * 20 + "┤")

                quote_id = None
                for res in results:
                    ref_id = res.get('refId', '')
                    sobject_type = res.get('type', '')
                    record_id = res.get('id', '')
                    print(f"│ {ref_id:<17} │ {sobject_type:<13} │ {record_id:<18} │")

                    # Capture the Quote ID
                    if sobject_type == 'Quote':
                        quote_id = record_id

                print("└" + "─" * 19 + "┴" + "─" * 15 + "┴" + "─" * 20 + "┘")

        print("\n✓ Quote import completed successfully")
        return quote_id

    except subprocess.CalledProcessError as e:
        print(f"✗ Error importing quote:")
        print(e.stdout)
        print(e.stderr)
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"✗ Error parsing import result: {e}")
        return None


def reprice_quote(org_alias, quote_id):
    """Reprice the quote using RepriceQuotesPST Apex class."""
    try:
        print(f"\n→ Repricing quote {quote_id}...")

        apex_code = f"""
List<String> quoteIds = new List<String>{{'{quote_id}'}};
RepriceQuotesPST.repriceQuotesPST(quoteIds);
System.debug('Quote repriced successfully');
"""

        result = subprocess.run(
            ["sf", "apex", "run", "--target-org", org_alias],
            input=apex_code,
            capture_output=True,
            text=True,
            check=True
        )

        print("✓ Quote repriced successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Error repricing quote:")
        print(e.stderr)
        return False


def create_order_from_quote(org_alias, quote_id):
    """Create an order from the quote using Salesforce REST API."""
    try:
        print(f"\n→ Creating order from quote {quote_id}...")

        # Get the instance URL and access token
        auth_result = subprocess.run(
            ["sf", "org", "display", "--target-org", org_alias, "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        auth_data = json.loads(auth_result.stdout)
        instance_url = auth_data['result']['instanceUrl']
        access_token = auth_data['result']['accessToken']

        # Prepare the REST API request
        import requests

        url = f"{instance_url}/services/data/v62.0/actions/standard/createOrderFromQuote"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Request body following the action's exact input specification
        # The action expects "quoteRecordId" as the input parameter
        payload = {
            "inputs": [
                {
                    "quoteRecordId": quote_id
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            result_data = response.json()
            if result_data and len(result_data) > 0:
                output = result_data[0]
                if output.get('isSuccess'):
                    output_values = output.get('outputValues', {})
                    # The order ID might be under different keys
                    order_id = output_values.get('orderId') or output_values.get('OrderId') or output_values.get('order')
                    if order_id:
                        print(f"✓ Order created successfully: {order_id}")
                        return order_id
                    else:
                        print(f"  Success but order ID not found in output: {output_values}")
                else:
                    errors = output.get('errors', [])
                    for error in errors:
                        print(f"  Error: {error.get('message', 'Unknown error')}")

            print("✓ Order creation completed (check response for details)")
            return None
        else:
            print(f"  Error: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    except ImportError:
        print("✗ Error: 'requests' library not installed")
        print("  Install with: pip install requests")
        return None
    except subprocess.CalledProcessError as e:
        print(f"✗ Error getting org info:")
        print(e.stderr)
        return None
    except Exception as e:
        print(f"✗ Error creating order: {e}")
        return None


def activate_order(org_alias, order_id):
    """Activate the order so that assets are created."""
    try:
        print(f"\n→ Activating order {order_id}...")

        # Update the Order Status to 'Activated'
        command = f'sf data update record --sobject Order --record-id {order_id} --values "Status=Activated" --target-org {org_alias} --json'

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )

        result_data = json.loads(result.stdout)

        if result_data.get('status') == 0:
            print("✓ Order activated successfully")
            print("  Waiting for asset creation (5 seconds)...")
            time.sleep(5)
            print("  Assets should now be created")
            return True
        else:
            print(f"✗ Order activation failed: {result_data}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"✗ Error activating order:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"✗ Error activating order: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Import test quote with line item for Labubu Industries'
    )
    parser.add_argument('--org', required=True, help='Salesforce org alias')
    parser.add_argument('--quote-name', default='Test Quote - Labubu Industries',
                       help='Name for the quote (default: Test Quote - Labubu Industries)')
    parser.add_argument('--quantity', type=int, default=15,
                       help='Quantity for quote line item (default: 15)')

    args = parser.parse_args()
    org_alias = args.org
    quote_name = args.quote_name

    script_dir = Path(__file__).parent

    print(f"{'='*60}")
    print(f"Import Test Quote")
    print(f"{'='*60}")
    print(f"Org: {org_alias}")
    print(f"Base Quote Name: {quote_name}")
    print(f"Quantity: {args.quantity}")
    print(f"{'='*60}\n")

    # Find available quote name (append number if duplicate exists)
    print(f"→ Finding available quote name...")
    final_quote_name, is_original = find_available_quote_name(org_alias, quote_name)

    if not is_original:
        print(f"✓ Will create quote with incremented name: '{final_quote_name}'")
    else:
        print(f"✓ Base name is available: '{final_quote_name}'")

    # Update quote_name to the final name
    quote_name = final_quote_name

    # Check dependencies
    deps = check_dependencies(org_alias)
    if not deps:
        print("\n✗ Missing dependencies. Please create required records first.")
        sys.exit(1)

    # Create Opportunity.json
    opp_json_path = script_dir / "Opportunity.json"
    opp_name = f"Opportunity for {quote_name}"
    opp_data = create_opportunity_json(deps, opp_name)
    with open(opp_json_path, 'w') as f:
        json.dump(opp_data, f, indent=2)
    print(f"\n✓ Created Opportunity.json")

    # Create Quote.json
    quote_json_path = script_dir / "Quote.json"
    quote_data = create_quote_json(deps, quote_name)
    with open(quote_json_path, 'w') as f:
        json.dump(quote_data, f, indent=2)
    print(f"✓ Created Quote.json")

    # Create QuoteLineItem.json
    qli_json_path = script_dir / "QuoteLineItem.json"
    qli_data = create_quote_line_item_json(deps, args.quantity)
    with open(qli_json_path, 'w') as f:
        json.dump(qli_data, f, indent=2)
    print(f"✓ Created QuoteLineItem.json")

    # Create plan
    plan_path = script_dir / "quote-plan.json"
    plan_data = create_quote_plan()
    with open(plan_path, 'w') as f:
        json.dump(plan_data, f, indent=2)
    print(f"✓ Created quote-plan.json")

    # Import the data
    quote_id = import_data(org_alias, plan_path)
    if not quote_id:
        print("\n✗ Quote import failed.")
        sys.exit(1)

    # Reprice the quote
    if not reprice_quote(org_alias, quote_id):
        print("\n⚠ Warning: Quote created but repricing failed.")
        print("  You may need to reprice manually.")
        sys.exit(1)

    # Create order from quote
    order_id = create_order_from_quote(org_alias, quote_id)
    if not order_id:
        print("\n⚠ Warning: Quote created and repriced, but order creation failed.")
        print("  You may need to create the order manually.")
    else:
        # Activate the order to trigger asset creation
        if not activate_order(org_alias, order_id):
            print("\n⚠ Warning: Order created but activation failed.")
            print("  You may need to activate manually.")

    print(f"\n{'='*60}")
    print(f"✓ Import completed successfully!")
    print(f"{'='*60}")
    print(f"\nCreated Quote ID: {quote_id}")
    if order_id:
        print(f"Created Order ID: {order_id}")
    print(f"\nVerify the quote:")
    print(f"  sf data query --query \"SELECT Id, Name, Status FROM Quote WHERE Name='{quote_name}'\" --target-org {org_alias}")
    print(f"\nVerify app usage assignment:")
    print(f"  sf data query --query \"SELECT Id, RecordId, AppUsageType FROM AppUsageAssignment WHERE Record.Name='{quote_name}'\" --target-org {org_alias}")
    print(f"\nVerify quote line items:")
    print(f"  sf data query --query \"SELECT Id, Product2.Name, Quantity, UnitPrice FROM QuoteLineItem WHERE Quote.Name='{quote_name}'\" --target-org {org_alias}")
    if order_id:
        print(f"\nVerify the order:")
        print(f"  sf data query --query \"SELECT Id, OrderNumber, Status, TotalAmount FROM Order WHERE Id='{order_id}'\" --target-org {org_alias}")
        print(f"\nVerify order items:")
        print(f"  sf data query --query \"SELECT Id, Product2.Name, Quantity, UnitPrice FROM OrderItem WHERE OrderId='{order_id}'\" --target-org {org_alias}")
        print(f"\nVerify assets created from order (via OrderItem → AssetActionSource):")
        print(f"  sf data query --query \"SELECT AssetAction.AssetId, AssetAction.Asset.Name, AssetAction.Asset.Product2.Name, AssetAction.Asset.Status, AssetAction.Asset.Quantity, AssetAction.Asset.CurrentMrr FROM AssetActionSource WHERE ReferenceEntityItemId IN (SELECT Id FROM OrderItem WHERE OrderId='{order_id}')\" --target-org {org_alias}")


if __name__ == '__main__':
    main()
