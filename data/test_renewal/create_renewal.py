#!/usr/bin/env python3
"""
Find assets for renewal testing and optionally create renewal quotes.

This script finds assets where:
- Product2.Name = 'Enterprise Campaign Manager (Legacy)'
- Account.Name = 'Labubu Industries'

All IDs are looked up dynamically - no hardcoded values.

Can also invoke the Salesforce Renewal API to create a renewal quote from an asset.

API Documentation:
https://developer.salesforce.com/docs/atlas.en-us.revenue_lifecycle_management_dev_guide.meta/revenue_lifecycle_management_dev_guide/connect_resources_assets_renew.htm

Usage:
    python create_renewal.py --org orgfarmorg
    python create_renewal.py --org orgfarmorg --renew-asset 02iVW000000bkzxYAA
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


def query_records(org_alias, query):
    """Execute a SOQL query and return the results."""
    command = f'sf data query --query "{query}" --target-org {org_alias} --json'

    try:
        output = run_sf_command(command)
        result = json.loads(output)

        if result.get('status') == 0 and result.get('result'):
            records = result['result'].get('records', [])
            return records

        return []
    except Exception as e:
        print(f"Error executing query: {e}")
        return []


def find_assets(org_alias):
    """Find assets matching the criteria."""
    print("→ Looking up Account ID for 'Labubu Industries'...")

    # Query for Account
    account_query = "SELECT Id, Name FROM Account WHERE Name = 'Labubu Industries' LIMIT 1"
    accounts = query_records(org_alias, account_query)

    if not accounts:
        print("✗ Account 'Labubu Industries' not found")
        return None

    account_id = accounts[0]['Id']
    account_name = accounts[0]['Name']
    print(f"✓ Found Account: {account_name} ({account_id})")

    print("\n→ Looking up Product ID for 'Enterprise Campaign Manager (Legacy)'...")

    # Query for Product
    product_query = "SELECT Id, Name, ProductCode FROM Product2 WHERE Name = 'Enterprise Campaign Manager (Legacy)' LIMIT 1"
    products = query_records(org_alias, product_query)

    if not products:
        print("✗ Product 'Enterprise Campaign Manager (Legacy)' not found")
        return None

    product_id = products[0]['Id']
    product_name = products[0]['Name']
    product_code = products[0].get('ProductCode', 'N/A')
    print(f"✓ Found Product: {product_name} (Code: {product_code}, ID: {product_id})")

    print(f"\n→ Searching for Assets where Product2Id='{product_id}' AND AccountId='{account_id}'...")

    # Query for Assets
    asset_query = f"""
        SELECT Id, Name, AccountId, Account.Name, Product2Id, Product2.Name,
               Status, Quantity, CurrentMrr, LifecycleStartDate, LifecycleEndDate,
               HasLifecycleManagement
        FROM Asset
        WHERE Product2Id = '{product_id}'
        AND AccountId = '{account_id}'
    """

    assets = query_records(org_alias, asset_query)

    if not assets:
        print("✗ No assets found matching the criteria")
        print(f"  Product: {product_name}")
        print(f"  Account: {account_name}")
        return None

    print(f"✓ Found {len(assets)} asset(s)\n")

    return {
        'account_id': account_id,
        'account_name': account_name,
        'product_id': product_id,
        'product_name': product_name,
        'product_code': product_code,
        'assets': assets
    }


def renew_asset(org_alias, asset_id):
    """
    Create a renewal quote from an asset using the Salesforce Renew Assets action.

    Uses the standard action: /services/data/v67.0/actions/standard/renewAssets

    API Documentation:
    https://developer.salesforce.com/docs/atlas.en-us.revenue_lifecycle_management_dev_guide.meta/revenue_lifecycle_management_dev_guide/actions_obj_renew_assets.htm

    Returns the renewal quote ID if successful, None otherwise.
    """
    print(f"\n→ Creating renewal quote for asset {asset_id}...")

    try:
        # Get org details (instance URL and access token)
        auth_command = f'sf org display --target-org {org_alias} --json'
        auth_output = run_sf_command(auth_command)
        auth_data = json.loads(auth_output)

        instance_url = auth_data['result']['instanceUrl']
        access_token = auth_data['result']['accessToken']

        print(f"  Instance URL: {instance_url}")

        # Prepare the REST API request
        import requests

        # Use the standard initiateRenewal action
        url = f"{instance_url}/services/data/v67.0/actions/standard/initiateRenewal"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Request body for initiateRenewal action
        # Required parameters: renewAssetIds (array) and renewOutputType
        payload = {
            "inputs": [
                {
                    "renewAssetIds": [asset_id],
                    "renewOutputType": "Quote"  # Create a Quote (other option might be "Order")
                }
            ]
        }

        print(f"  Calling: POST {url}")
        print(f"  Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            result_data = response.json()
            print(f"✓ Renew Assets action completed")
            print(f"\nAPI Response:")
            print(json.dumps(result_data, indent=2))

            if result_data and len(result_data) > 0:
                output = result_data[0]
                if output.get('isSuccess'):
                    output_values = output.get('outputValues', {})

                    # Try different possible field names for the quote/renewal record ID
                    quote_id = (output_values.get('renewRecordId') or
                               output_values.get('quoteId') or
                               output_values.get('renewalQuoteId') or
                               output_values.get('QuoteId') or
                               (output_values.get('quoteIds', [None])[0] if output_values.get('quoteIds') else None))

                    if quote_id:
                        print(f"\n✓ Renewal Quote ID: {quote_id}")
                        return quote_id
                    else:
                        print(f"\n⚠ Warning: Quote ID not found in output")
                        print(f"  Output values: {output_values}")
                        return None
                else:
                    errors = output.get('errors', [])
                    print(f"\n✗ Action failed:")
                    for error in errors:
                        print(f"  Error: {error.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"\n⚠ Warning: Empty response from action")
                return None
        else:
            print(f"\n✗ Error: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    except ImportError:
        print("✗ Error: 'requests' library not installed")
        print("  Install with: pip install requests")
        return None
    except Exception as e:
        print(f"✗ Error creating renewal quote: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_assets(result):
    """Display asset information in a formatted table."""
    assets = result['assets']

    print("=" * 120)
    print(f"Assets for Product: {result['product_name']} ({result['product_code']})")
    print(f"Account: {result['account_name']}")
    print("=" * 120)

    # Header
    print(f"\n{'Asset ID':<20} {'Asset Name':<40} {'Status':<15} {'Qty':<8} {'MRR':<12} {'Lifecycle Mgmt'}")
    print("-" * 120)

    # Rows
    for asset in assets:
        asset_id = asset.get('Id', '')
        asset_name = (asset.get('Name', '') or '')[:39]  # Truncate long names
        status = asset.get('Status') or 'N/A'
        quantity = asset.get('Quantity') or 0
        mrr = asset.get('CurrentMrr') or 0
        has_lifecycle = 'Yes' if asset.get('HasLifecycleManagement') else 'No'

        print(f"{asset_id:<20} {asset_name:<40} {status:<15} {quantity:<8.0f} ${mrr:<11.2f} {has_lifecycle}")

    print("-" * 120)
    print(f"\nTotal Assets: {len(assets)}")
    print("\nLifecycle Details:")
    for asset in assets:
        print(f"\nAsset: {asset.get('Name')} ({asset.get('Id')})")
        print(f"  Start Date: {asset.get('LifecycleStartDate', 'N/A')}")
        print(f"  End Date: {asset.get('LifecycleEndDate', 'N/A')}")
        print(f"  Has Lifecycle Management: {asset.get('HasLifecycleManagement')}")


def main():
    parser = argparse.ArgumentParser(
        description='Find assets for renewal testing and optionally create renewal quotes'
    )
    parser.add_argument('--org', required=True, help='Salesforce org alias')
    parser.add_argument('--renew-asset', dest='renew_asset', help='Asset ID to renew (creates a renewal quote)')

    args = parser.parse_args()
    org_alias = args.org

    print(f"{'='*60}")
    print(f"Find Assets for Renewal Testing")
    print(f"{'='*60}")
    print(f"Org: {org_alias}")

    # If user specified a specific asset to renew, do that instead
    if args.renew_asset:
        asset_id = args.renew_asset
        print(f"Asset ID to Renew: {asset_id}")
        print(f"{'='*60}\n")

        # Create renewal quote
        quote_id = renew_asset(org_alias, asset_id)

        if quote_id:
            print(f"\n{'='*60}")
            print(f"✓ Renewal completed successfully!")
            print(f"{'='*60}")
            print(f"\nVerify the renewal quote:")
            print(f"  sf data query --query \"SELECT Id, Name, Status, AccountId FROM Quote WHERE Id='{quote_id}'\" --target-org {org_alias}")
        else:
            print(f"\n{'='*60}")
            print(f"✗ Renewal failed")
            print(f"{'='*60}")
            sys.exit(1)

        return

    # Otherwise, find and display assets
    print(f"Product: Enterprise Campaign Manager (Legacy)")
    print(f"Account: Labubu Industries")
    print(f"{'='*60}\n")

    # Find assets
    result = find_assets(org_alias)

    if not result:
        print("\n✗ No assets found. You may need to:")
        print("  1. Create an account: cd ../test_accounts && python import_account.py --org " + org_alias)
        print("  2. Create a product: cd ../test_products && python import_with_replacement_product.py --org " + org_alias)
        print("  3. Create a quote and order: cd ../test_quotes && python import_quote.py --org " + org_alias)
        print("  4. Assets are created when an order is activated")
        sys.exit(1)

    # Display results
    display_assets(result)

    print(f"\n{'='*60}")
    print(f"✓ Asset search completed successfully!")
    print(f"{'='*60}")

    # Show how to renew
    if result['assets']:
        first_asset_id = result['assets'][0].get('Id')
        print(f"\nTo create a renewal quote from the first asset, run:")
        print(f"  python create_renewal.py --org {org_alias} --renew-asset {first_asset_id}")


if __name__ == '__main__':
    main()
