# Test Data

This directory contains test data and import scripts for the ARCEndOfSale project.

## Quick Start - Import All Test Data

The fastest way to set up all test data is to use the consolidated import script:

```bash
cd data
python import_all_test_data.py --org orgfarmorg
```

This single command will:
1. ✓ Create Account: "Labubu Industries"
2. ✓ Create Product: "Enterprise Campaign Manager (Legacy)" with renewal replacement
3. ✓ Create Quote: "Test Quote - Labubu Industries" with line item
4. ✓ Automatically reprice the quote using PST API
5. ✓ Create an Order from the quote
6. ✓ Activate the Order (Status='Activated')
7. ✓ Generate Assets automatically from the activated order
8. ✓ Refresh pricing decision tables automatically

## Directory Structure

```
data/
├── README.md                          # This file
├── import_all_test_data.py            # Master script - imports everything
├── test_accounts/                     # Account test data
│   ├── README.md                      # Account-specific documentation
│   ├── import_account.py              # Import Labubu Industries account
│   └── Account.json                   # Account data
├── test_products/                     # Product test data
│   ├── README.md                      # Product-specific documentation
│   ├── import_with_replacement_product.py  # Import product with replacement
│   ├── Product2.json                  # Product data
│   ├── PricebookEntry.json            # Pricebook entries
│   ├── ProductSellingModelOption.json # Selling model options
│   └── ProductCategoryProduct.json    # Category associations
├── test_quotes/                       # Quote test data
│   ├── README.md                      # Quote-specific documentation
│   ├── import_quote.py                # Import quote with full workflow
│   ├── import_quote_only.py           # Import quote only (no repricing/orders)
│   ├── Opportunity.json               # Generated - Opportunity data
│   ├── Quote.json                     # Generated - Quote data
│   └── QuoteLineItem.json             # Generated - Line item data
└── test_renewal/                      # Renewal quote test data
    ├── README.md                      # Renewal-specific documentation
    └── create_renewal.py              # Find assets and create renewal quotes
```

## Consolidated Import Script

### Basic Usage

```bash
# Import all test data with defaults
python import_all_test_data.py --org orgfarmorg

# Import with custom quote name and quantity
python import_all_test_data.py --org orgfarmorg --quote-name "Q4 Renewal" --quantity 25

# Skip decision table refresh (faster, but may need manual refresh later)
python import_all_test_data.py --org orgfarmorg --skip-dt-refresh

# Use a different replacement product
python import_all_test_data.py --org orgfarmorg --replacement-product "My Product Name"
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--org` | *required* | Salesforce org alias |
| `--quote-name` | `Test Quote - Labubu Industries` | Name for the quote |
| `--quantity` | `15` | Quantity for quote line item |
| `--replacement-product` | `QuantumBit Generative AI License` | Replacement product name |
| `--skip-dt-refresh` | `false` | Skip decision table refresh |

### What Gets Created

**1. Account**
- Name: Labubu Industries
- Status: If already exists, reports existing ID

**2. Product**
- Name: Enterprise Campaign Manager (Legacy)
- ProductCode: ECM-LEGACY
- Price: $1,200/user/year
- Selling Model: Term Annual
- Category: Licenses
- RenewalReplacementProduct: QuantumBit Generative AI License (or custom)
- Status: If already exists, reports existing ID

**3. Quote**
- Name: Test Quote - Labubu Industries (or incremented: " 1", " 2", etc.)
- Account: Labubu Industries
- Product: Enterprise Campaign Manager (Legacy)
- Quantity: 15 (or custom)
- Total: $18,000 (quantity × $1,200)
- Status: Always creates new quote with auto-incremented name
- Automatically repriced using RepriceQuotesPST

**4. Order**
- Created from Quote using CreateOrderFromQuote action
- Status: Activated (automatically set by script)
- Total Amount: $18,000
- OrderItem: Enterprise Campaign Manager (Legacy), Qty 15

**5. Asset**
- Created automatically when Order is activated
- Product: Enterprise Campaign Manager (Legacy)
- Account: Labubu Industries
- Linked via AssetAction and AssetActionSource

**6. Related Records (Auto-Created)**
- Opportunity (parent of Quote)
- AppUsageAssignment (AppUsageType=RevenueLifecycleManagement)
- PricebookEntry for the product
- ProductSellingModelOption
- ProductCategoryProduct

## Individual Import Scripts

You can also run each import script individually if you need more control:

### 1. Import Account Only

```bash
cd test_accounts
python import_account.py --org orgfarmorg
```

See [test_accounts/README.md](./test_accounts/README.md) for details.

### 2. Import Product Only

```bash
cd test_products
python import_with_replacement_product.py --org orgfarmorg
```

Options:
- `--replacement-product "Product Name"` - Custom replacement product
- `--skip-dt-refresh` - Skip decision table refresh
- `--decision-tables "Table1,Table2"` - Custom decision tables to refresh

See [test_products/README.md](./test_products/README.md) for details.

### 3. Import Quote Only

```bash
cd test_quotes
python import_quote.py --org orgfarmorg
```

Options:
- `--quote-name "My Quote"` - Custom quote name
- `--quantity 25` - Custom quantity

See [test_quotes/README.md](./test_quotes/README.md) for details.

### 4. Create Renewal Quotes

```bash
cd test_renewal

# Find assets eligible for renewal
python create_renewal.py --org orgfarmorg

# Create a renewal quote from a specific asset
python create_renewal.py --org orgfarmorg --renew-asset 02iXXXXXXXXXXXX
```

The renewal script:
- Dynamically finds assets by Account ("Labubu Industries") and Product ("Enterprise Campaign Manager (Legacy)")
- Uses the Salesforce `initiateRenewal` standard action to create renewal quotes
- No hardcoded IDs - all lookups are dynamic

See [test_renewal/README.md](./test_renewal/README.md) for details.

## Import Behavior

### Idempotent vs Auto-Increment

- **Account**: Idempotent - checks if exists, reports ID if found
- **Product**: Idempotent - checks if exists, reports ID if found
- **Quote**: Auto-increment - always creates new quote with incremented name

This design allows you to:
- Run the consolidated script multiple times
- Create multiple test quotes without manual cleanup
- Maintain consistent account and product data

### Dependencies

The import order is critical due to Salesforce relationships:

```
Account (independent)
   ↓
Product (independent) → requires QuantumBit Product for replacement
   ↓
Quote (depends on Account + Product)
   ↓
   ├─ Opportunity (parent, links to Account)
   ├─ AppUsageAssignment (auto-created)
   └─ QuoteLineItem (requires Product + PricebookEntry)
```

The consolidated script ensures correct ordering automatically.

## Verifying Imported Data

### Quick Verification Queries

```bash
# Verify account
sf data query --query "SELECT Id, Name FROM Account WHERE Name='Labubu Industries'" --target-org orgfarmorg

# Verify product with replacement
sf data query --query "SELECT Id, Name, ProductCode, RenewalReplacementProduct__r.Name FROM Product2 WHERE ProductCode='ECM-LEGACY'" --target-org orgfarmorg

# Verify quotes
sf data query --query "SELECT Id, Name, Status, TotalPrice FROM Quote WHERE Name LIKE 'Test Quote - Labubu Industries%' ORDER BY CreatedDate DESC" --target-org orgfarmorg

# Verify quote line items
sf data query --query "SELECT Id, Quote.Name, Product2.Name, Quantity, UnitPrice, TotalPrice FROM QuoteLineItem WHERE Quote.Name LIKE 'Test Quote%' ORDER BY CreatedDate DESC" --target-org orgfarmorg

# Verify app usage assignment
sf data query --query "SELECT Id, RecordId, AppUsageType FROM AppUsageAssignment WHERE Record.Name LIKE 'Test Quote%'" --target-org orgfarmorg

# Verify orders created from quotes
sf data query --query "SELECT Id, OrderNumber, Status, TotalAmount FROM Order WHERE Quote.Name LIKE 'Test Quote - Labubu Industries%' ORDER BY CreatedDate DESC" --target-org orgfarmorg

# Verify order items
sf data query --query "SELECT Id, Order.OrderNumber, Product2.Name, Quantity, UnitPrice, TotalPrice FROM OrderItem WHERE Order.Quote.Name LIKE 'Test Quote%' ORDER BY CreatedDate DESC" --target-org orgfarmorg

# Verify assets created from orders
sf data query --query "SELECT AssetAction.AssetId, AssetAction.Asset.Name, AssetAction.Asset.Product2.Name, AssetAction.Asset.Status FROM AssetActionSource WHERE ReferenceEntityItemId IN (SELECT Id FROM OrderItem WHERE Order.Quote.Name LIKE 'Test Quote - Labubu Industries%') ORDER BY CreatedDate DESC" --target-org orgfarmorg
```

### Complete Quote Structure Query

```bash
sf data query --query "SELECT Id, Name, Status, Account.Name, QuoteAccount.Name, TotalPrice, (SELECT Id, Product2.Name, Quantity, UnitPrice, TotalPrice FROM QuoteLineItems) FROM Quote WHERE Name LIKE 'Test Quote - Labubu Industries%' ORDER BY CreatedDate DESC LIMIT 1" --target-org orgfarmorg
```

## Deleting Test Data

### Delete All Test Data

```bash
# Delete all test quotes (cascades to opportunities and line items)
sf data query --query "SELECT Id FROM Quote WHERE Name LIKE 'Test Quote - Labubu Industries%'" --target-org orgfarmorg --json | \
  jq -r '.result.records[].Id' | \
  xargs -I {} sf data delete record --sobject Quote --record-id {} --target-org orgfarmorg

# Delete test product
sf data delete record --sobject Product2 --where "ProductCode='ECM-LEGACY'" --target-org orgfarmorg

# Delete test account
sf data delete record --sobject Account --where "Name='Labubu Industries'" --target-org orgfarmorg
```

### Delete Individual Records

```bash
# Delete specific quote
sf data delete record --sobject Quote --where "Name='Test Quote - Labubu Industries 1'" --target-org orgfarmorg

# Delete by ID
sf data delete record --sobject Quote --record-id 0Q0XXXXXXXXXXXX --target-org orgfarmorg
```

## Troubleshooting

### Common Issues

**Script fails with "Account not found"**
- Run account import first: `cd test_accounts && python import_account.py --org orgfarmorg`
- Or use the consolidated script which handles ordering

**Script fails with "Product not found"**
- Run product import first: `cd test_products && python import_with_replacement_product.py --org orgfarmorg`
- Ensure the replacement product exists in the org

**Script fails with "PricebookEntry not found"**
- The product import should create the pricebook entry
- Verify the product was imported successfully
- Check that the standard pricebook exists

**Decision table refresh fails**
- Install Python requests library: `pip install requests`
- Use `--skip-dt-refresh` to skip and refresh manually later
- Check the decision table name is correct

**Quote import succeeds but QuoteLineItem creation fails**
- Check that the product has an active pricebook entry
- Verify the product is active (IsActive=true)
- Ensure you have permission to create QuoteLineItems

### Getting Help

For detailed troubleshooting:
- Account issues: See [test_accounts/README.md](./test_accounts/README.md)
- Product issues: See [test_products/README.md](./test_products/README.md)
- Quote issues: See [test_quotes/README.md](./test_quotes/README.md)
- Renewal issues: See [test_renewal/README.md](./test_renewal/README.md)
- General deployment: See [../DEPLOYMENT.md](../DEPLOYMENT.md)

## Examples

### Example 1: First-Time Setup

```bash
# Import all test data for the first time
cd data
python import_all_test_data.py --org myorg

# Result:
# ✓ Account created: Labubu Industries
# ✓ Product created: Enterprise Campaign Manager (Legacy)
# ✓ Quote created: Test Quote - Labubu Industries
```

### Example 2: Create Additional Test Quotes

```bash
# Create another quote (auto-increments to "Test Quote - Labubu Industries 1")
python import_all_test_data.py --org myorg

# Create with custom quantity
python import_all_test_data.py --org myorg --quantity 50

# Create with custom name
python import_all_test_data.py --org myorg --quote-name "Q3 Renewal" --quantity 30
```

### Example 3: Different Replacement Product

```bash
# Use a different replacement product
python import_all_test_data.py --org myorg --replacement-product "My New Product"

# Note: "My New Product" must already exist in the org
```

### Example 4: Fast Import (Skip Decision Tables)

```bash
# Skip decision table refresh for faster import
python import_all_test_data.py --org myorg --skip-dt-refresh

# Manually refresh decision tables later if needed
cd ../scripts/decision_tables
python refresh_decision_table_standalone.py --org myorg --tables Price_Book_Entry_Decision_Table_v2
```

## Notes

- All scripts use dynamic ID lookup - no hardcoded IDs
- Scripts are safe to run multiple times
- Account and Product are idempotent (check before creating)
- Quotes auto-increment names (always create new)
- Decision table refresh happens automatically unless `--skip-dt-refresh` is used
- All imports validate dependencies before proceeding

## Next Steps

After importing test data:

1. **Verify the data** using the queries above
2. **Test product replacement** using the Apex classes
3. **Create additional quotes** by re-running the script
4. **Create renewal quotes** from existing assets using the renewal script
5. **Explore the data model** in Salesforce UI

See the [main project README](../README.md) for workflows using this test data.

## Renewal Quote Workflow

After importing test data and creating orders/assets, you can test the renewal workflow:

1. **Find assets eligible for renewal**:
   ```bash
   cd test_renewal
   python create_renewal.py --org orgfarmorg
   ```

2. **Create a renewal quote from an asset**:
   ```bash
   python create_renewal.py --org orgfarmorg --renew-asset <asset-id>
   ```

3. **Verify the renewal quote**:
   ```bash
   sf data query --query "SELECT Id, Name, Status, TotalPrice FROM Quote WHERE Name='Renewal Quote'" --target-org orgfarmorg
   ```

The renewal script uses the Salesforce `initiateRenewal` standard action (API v67.0) to create renewal quotes from assets with lifecycle management enabled.
