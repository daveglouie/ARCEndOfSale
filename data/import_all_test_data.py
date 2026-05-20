#!/usr/bin/env python3
"""
Import all test data in the correct order: Account → Product → Quote

This master script orchestrates the import of all test data components:
1. Account: Labubu Industries
2. Product: Enterprise Campaign Manager (Legacy) with renewal replacement
3. Quote: Test quote with line item for the product

Usage:
    python import_all_test_data.py --org orgfarmorg
    python import_all_test_data.py --org orgfarmorg --quote-name "My Test Quote" --quantity 20
    python import_all_test_data.py --org orgfarmorg --skip-dt-refresh
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_import_script(script_path, org_alias, additional_args=None):
    """
    Run an import script and return success status.

    Args:
        script_path: Path to the Python script to run
        org_alias: Salesforce org alias
        additional_args: List of additional arguments to pass to the script

    Returns:
        True if successful, False otherwise
    """
    cmd = [sys.executable, str(script_path), "--org", org_alias]

    if additional_args:
        cmd.extend(additional_args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Script failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Import all test data: Account, Product, and Quote',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import all test data with defaults
  python import_all_test_data.py --org orgfarmorg

  # Import with custom quote parameters
  python import_all_test_data.py --org orgfarmorg --quote-name "Q4 Renewal" --quantity 25

  # Import without decision table refresh
  python import_all_test_data.py --org orgfarmorg --skip-dt-refresh

  # Custom replacement product
  python import_all_test_data.py --org orgfarmorg --replacement-product "My Replacement Product"
        """
    )

    parser.add_argument(
        '--org',
        required=True,
        help='Salesforce org alias'
    )

    # Account options (none currently, but keeping for future)

    # Product options
    parser.add_argument(
        '--replacement-product',
        default='QuantumBit Generative AI License',
        help='Name of the replacement product (default: QuantumBit Generative AI License)'
    )
    parser.add_argument(
        '--skip-dt-refresh',
        action='store_true',
        help='Skip decision table refresh after product import'
    )

    # Quote options
    parser.add_argument(
        '--quote-name',
        default='Test Quote - Labubu Industries',
        help='Name for the quote (default: Test Quote - Labubu Industries)'
    )
    parser.add_argument(
        '--quantity',
        type=int,
        default=15,
        help='Quantity for quote line item (default: 15)'
    )

    args = parser.parse_args()

    # Get paths
    data_dir = Path(__file__).parent
    account_script = data_dir / 'test_accounts' / 'import_account.py'
    product_script = data_dir / 'test_products' / 'import_with_replacement_product.py'
    quote_script = data_dir / 'test_quotes' / 'import_quote.py'

    # Verify all scripts exist
    missing_scripts = []
    for script_name, script_path in [
        ('Account import', account_script),
        ('Product import', product_script),
        ('Quote import', quote_script)
    ]:
        if not script_path.exists():
            missing_scripts.append(f"{script_name}: {script_path}")

    if missing_scripts:
        print("✗ Missing required import scripts:")
        for missing in missing_scripts:
            print(f"  - {missing}")
        sys.exit(1)

    print("=" * 70)
    print("Import All Test Data")
    print("=" * 70)
    print(f"Org: {args.org}")
    print(f"Replacement Product: {args.replacement_product}")
    print(f"Quote Name: {args.quote_name}")
    print(f"Quantity: {args.quantity}")
    print(f"Skip DT Refresh: {args.skip_dt_refresh}")
    print("=" * 70)
    print()

    # Step 1: Import Account
    print("=" * 70)
    print("STEP 1/3: Import Account (Labubu Industries)")
    print("=" * 70)
    print()

    if not run_import_script(account_script, args.org):
        print("\n✗ Failed to import account. Aborting.")
        sys.exit(1)

    print("\n✓ Account import completed")

    # Step 2: Import Product
    print("\n" + "=" * 70)
    print("STEP 2/3: Import Product (Enterprise Campaign Manager Legacy)")
    print("=" * 70)
    print()

    product_args = ['--replacement-product', args.replacement_product]
    if args.skip_dt_refresh:
        product_args.append('--skip-dt-refresh')

    if not run_import_script(product_script, args.org, product_args):
        print("\n✗ Failed to import product. Aborting.")
        sys.exit(1)

    print("\n✓ Product import completed")

    # Step 3: Import Quote
    print("\n" + "=" * 70)
    print("STEP 3/3: Import Quote with Line Item")
    print("=" * 70)
    print()

    quote_args = [
        '--quote-name', args.quote_name,
        '--quantity', str(args.quantity)
    ]

    if not run_import_script(quote_script, args.org, quote_args):
        print("\n✗ Failed to import quote. Aborting.")
        sys.exit(1)

    print("\n✓ Quote import completed")

    # Final summary
    print("\n" + "=" * 70)
    print("✓ ALL TEST DATA IMPORTED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  1. ✓ Account: Labubu Industries")
    print("  2. ✓ Product: Enterprise Campaign Manager (Legacy)")
    print(f"     → Replacement: {args.replacement_product}")
    print(f"  3. ✓ Quote: {args.quote_name} (or incremented name)")
    print(f"     → Quantity: {args.quantity}")
    print()
    print("Next steps:")
    print("  • View quotes:")
    print(f"    sf data query --query \"SELECT Id, Name, Status, TotalPrice FROM Quote WHERE Name LIKE '{args.quote_name}%'\" --target-org {args.org}")
    print()
    print("  • View quote line items:")
    print(f"    sf data query --query \"SELECT Id, Quote.Name, Product2.Name, Quantity, UnitPrice FROM QuoteLineItem WHERE Quote.Name LIKE '{args.quote_name}%'\" --target-org {args.org}")
    print()
    print("  • Test product replacement:")
    print("    # In Salesforce Anonymous Apex:")
    print("    QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote('QUOTE_ID');")
    print()


if __name__ == '__main__':
    main()
