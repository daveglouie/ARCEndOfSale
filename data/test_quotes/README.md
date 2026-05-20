# Test Quote Data

This directory contains test quote data for creating demo/test quotes with quote line items, automatic repricing, order creation, and asset generation.

## Test Quote - Labubu Industries

A test quote for the "Labubu Industries" account with a line item for "Enterprise Campaign Manager (Legacy)" product. The script automatically reprices the quote, creates an order, activates it, and generates assets.

**Quote Details:**
- **Quote Name:** Test Quote - Labubu Industries
- **Account (via Opportunity):** Labubu Industries
- **QuoteAccountId:** Labubu Industries (set directly on Quote)
- **Quote Start Date:** Today's date (dynamically set)
- **Product:** Enterprise Campaign Manager (Legacy) (ProductCode: ECM-LEGACY)
- **Quantity:** 15
- **Unit Price:** $1,200 (from standard pricebook)
- **Total Price:** $18,000

**Quote Line Item Details:**
- **Start Date:** Today's date (dynamically set)
- **Subscription Term:** 1
- **Period Boundary:** Anniversary

**Related Records Created:**
1. **Opportunity** - Required parent for Quote (named "Opportunity for Test Quote - Labubu Industries")
2. **Quote** - The quote record linked to the Opportunity
3. **QuoteLineItem** - Line item on the quote with the product and quantity
4. **AppUsageAssignment** - Automatically created by Salesforce with AppUsageType=RevenueLifecycleManagement
5. **Order** - Created from the quote and activated (Status=Activated)
6. **OrderItem** - Line items copied from the quote
7. **Asset** - Created automatically when order is activated
8. **AssetAction** - Tracks the asset creation action
9. **AssetActionSource** - Links the asset back to the OrderItem

## Usage

### Import Full Workflow with Repricing, Order Creation, and Assets (Recommended)

Use the full import script to create a quote and complete the entire order-to-asset workflow:

```bash
cd data/test_quotes
python import_quote.py --org orgfarmorg
```

This script:
1. **Finds an available quote name** by checking if the base name exists
2. If the base name exists, automatically appends an incremental number (e.g., " 1", " 2", " 3")
3. **Dynamically looks up required IDs** (no hardcoded values):
   - **Account ID** for "Labubu Industries" (used in Opportunity and Quote)
   - **Standard Pricebook ID** (IsStandard=true, used in Quote)
   - **Product ID** for "Enterprise Campaign Manager (Legacy)"
   - **PricebookEntry ID** (used in QuoteLineItem)
4. Creates the quote with the available name:
   - Verifies dependencies exist (Account, Product, PricebookEntry)
   - Creates JSON files dynamically with looked-up IDs
   - Creates Opportunity → Quote → QuoteLineItem in the correct order
5. **Automatically reprices the quote** using the RepriceQuotesPST Apex class
6. **Creates an order from the quote** using the CreateOrderFromQuote REST API action
7. **Activates the order** by setting Status='Activated'
8. **Waits for asset creation** (5 second delay for asynchronous processing)
9. Reports all created record IDs (Quote, Order, and Asset verification query)

**Key Feature:** All IDs are dynamically looked up from the target org. The static JSON files in this directory use placeholders (e.g., `PLACEHOLDER_ACCOUNT_ID`) that are replaced at runtime, making the script portable across different Salesforce orgs.

**Output when base name is available:**
```
→ Finding available quote name...
✓ Base name is available: 'Test Quote - Labubu Industries'
→ Checking dependencies...
✓ Found Account: Labubu Industries (001XXXXXXXXXXXX)
✓ Found Product: Enterprise Campaign Manager (Legacy) (01tXXXXXXXXXXXX)
...
✓ Import completed successfully!
```

**Output when base name exists (auto-increments):**
```
→ Finding available quote name...
  Quote 'Test Quote - Labubu Industries' already exists, finding next available number...
  → Will use name: 'Test Quote - Labubu Industries 1'
✓ Will create quote with incremented name: 'Test Quote - Labubu Industries 1'
→ Checking dependencies...
...
✓ Import completed successfully!
```

**Result:** Multiple quotes can be created with incremented names:
- Test Quote - Labubu Industries
- Test Quote - Labubu Industries 1
- Test Quote - Labubu Industries 2
- etc.

### Import Quote Only (No Repricing, No Order Creation)

Use the simplified import script to create just the quote without any post-processing:

```bash
cd data/test_quotes
python import_quote_only.py --org orgfarmorg
```

This script:
1. Creates Opportunity → Quote → QuoteLineItem
2. Sets all quote line item fields (StartDate, SubscriptionTerm, PeriodBoundary)
3. Skips repricing, order creation, and asset generation
4. Useful for testing quote creation in isolation

### Custom Options

```bash
# Custom quote name (works with both scripts)
python import_quote.py --org orgfarmorg --quote-name "My Custom Quote"
python import_quote_only.py --org orgfarmorg --quote-name "My Custom Quote"

# Custom quantity (works with both scripts)
python import_quote.py --org orgfarmorg --quantity 25
python import_quote_only.py --org orgfarmorg --quantity 25

# Both custom options
python import_quote.py --org orgfarmorg --quote-name "Q2 Renewal Quote" --quantity 50
python import_quote_only.py --org orgfarmorg --quote-name "Q2 Renewal Quote" --quantity 50
```

## Prerequisites

The following records must exist before running the import:

1. **Account "Labubu Industries"**
   ```bash
   cd ../test_accounts
   python import_account.py --org orgfarmorg
   ```

2. **Product "Enterprise Campaign Manager (Legacy)" (ProductCode: ECM-LEGACY)**
   ```bash
   cd ../test_products
   python import_with_replacement_product.py --org orgfarmorg
   ```

The script will check for these dependencies and provide helpful error messages if they're missing.

## Delete Test Data

```bash
# Delete a specific quote (also deletes opportunity and quote line items via cascade)
sf data delete record --sobject Quote --where "Name='Test Quote - Labubu Industries'" --target-org orgfarmorg

# Delete all test quotes for Labubu Industries
sf data query --query "SELECT Id FROM Quote WHERE Name LIKE 'Test Quote - Labubu Industries%'" --target-org orgfarmorg --json | \
  jq -r '.result.records[].Id' | \
  xargs -I {} sf data delete record --sobject Quote --record-id {} --target-org orgfarmorg
```

## File Structure

After running the script, you'll see:

```
data/test_quotes/
├── README.md              # This file
├── import_quote.py        # Full workflow: quote + repricing + order + assets
├── import_quote_only.py   # Simplified: quote only, no repricing/orders
├── Opportunity.json       # Generated - Opportunity record
├── Quote.json             # Generated - Quote record (with StartDate)
├── QuoteLineItem.json     # Generated - Quote line item (with StartDate, SubscriptionTerm, PeriodBoundary)
└── quote-plan.json        # Generated - Data import plan

Note: AppUsageAssignment is NOT included in the files above because it's
automatically created by Salesforce when the Quote is inserted.
```

**Note:** The JSON files are generated dynamically by the script based on looked-up IDs, so they will have the correct IDs for your org.

## Querying the Quote

```bash
# Find the quote with account and opportunity info
sf data query \
  --query "SELECT Id, Name, Status, AccountId, QuoteAccountId, Account.Name, QuoteAccount.Name, Opportunity.Name FROM Quote WHERE Name='Test Quote - Labubu Industries'" \
  --target-org orgfarmorg

# Verify AppUsageAssignment was auto-created
sf data query \
  --query "SELECT Id, RecordId, AppUsageType FROM AppUsageAssignment WHERE Record.Name='Test Quote - Labubu Industries'" \
  --target-org orgfarmorg

# Find quote line items with product details and subscription fields
sf data query \
  --query "SELECT Id, Product2.Name, Quantity, UnitPrice, TotalPrice, StartDate, SubscriptionTerm, PeriodBoundary FROM QuoteLineItem WHERE Quote.Name='Test Quote - Labubu Industries'" \
  --target-org orgfarmorg

# Get the full quote with all related data
sf data query \
  --query "SELECT Id, Name, Status, TotalPrice, (SELECT Id, Product2.Name, Quantity, UnitPrice FROM QuoteLineItems) FROM Quote WHERE Name='Test Quote - Labubu Industries'" \
  --target-org orgfarmorg
```

## Data Import Order

The script creates records in this specific order (required by Salesforce relationships):

1. **Opportunity** (needs Account)
2. **Quote** (needs Opportunity and Pricebook)
3. **AppUsageAssignment** (automatically created by Salesforce - not in import plan)
4. **QuoteLineItem** (needs Quote, Product, and PricebookEntry)

The data tree plan handles these dependencies using reference IDs:
- `OpportunityRef1` → saved after Opportunity creation
- `QuoteRef1` → references `OpportunityRef1`, saved after Quote creation
- `QuoteLineItemRef1` → references `QuoteRef1`

**Note:** AppUsageAssignment with AppUsageType=RevenueLifecycleManagement is **automatically created** by Salesforce when a Quote is inserted. You do not need to (and cannot) create it manually without triggering a duplicate error.

## Dynamic ID Lookups (No Hardcoded Values)

The script dynamically generates all JSON files at runtime with looked-up IDs. The static JSON files in this directory contain placeholders:

| File | Field | Placeholder | Lookup Method |
|------|-------|-------------|---------------|
| Opportunity.json | Name | PLACEHOLDER_OPPORTUNITY_NAME | Generated from quote name |
| Opportunity.json | AccountId | PLACEHOLDER_ACCOUNT_ID | Query by name "Labubu Industries" |
| Quote.json | Name | PLACEHOLDER_QUOTE_NAME | Auto-incremented from base name |
| Quote.json | Pricebook2Id | PLACEHOLDER_STANDARD_PRICEBOOK | Query WHERE IsStandard=true |
| Quote.json | QuoteAccountId | PLACEHOLDER_ACCOUNT_ID | Query by name "Labubu Industries" |
| Quote.json | StartDate | PLACEHOLDER_TODAY_DATE | date.today().isoformat() |
| QuoteLineItem.json | Product2Id | PLACEHOLDER_PRODUCT_ID | Query by ProductCode='ECM-LEGACY' |
| QuoteLineItem.json | PricebookEntryId | PLACEHOLDER_PRICEBOOK_ENTRY_ID | Query for product's standard pricebook entry |
| QuoteLineItem.json | StartDate | PLACEHOLDER_TODAY_DATE | date.today().isoformat() |
| QuoteLineItem.json | SubscriptionTerm | 1 | Hardcoded value |
| QuoteLineItem.json | PeriodBoundary | Anniversary | Hardcoded value |

These placeholder files are **overwritten** each time the script runs with the actual IDs from your target org, making the script portable across different Salesforce environments.

## Notes

- The script **auto-increments quote names** - running it multiple times creates new quotes with incremented names
- Quote names follow the pattern: base name, then "base name 1", "base name 2", etc.
- The Opportunity is created automatically and named "Opportunity for {QuoteName}"
- The script dynamically looks up the current user and assigns them as the owner
- Quote Status defaults to "Draft" after creation
- All required fields are set automatically based on dependency lookups
- Maximum 1000 quotes with the same base name (safety limit)

## Troubleshooting

**Error: "Account 'Labubu Industries' not found"**
- Create the account first: `cd ../test_accounts && python import_account.py --org orgfarmorg`

**Error: "Product 'Enterprise Campaign Manager (Legacy)' not found"**
- Create the product first: `cd ../test_products && python import_with_replacement_product.py --org orgfarmorg`

**Error: "PricebookEntry not found"**
- Ensure the product has a standard pricebook entry
- Check that the pricebook entry is active

**Error: "Unable to create/update fields: [FieldName]"**
- Check field-level security for your user/profile
- Verify the field is createable: `sf sobject describe --sobject [Object] --target-org orgfarmorg`
