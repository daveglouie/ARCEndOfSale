# ARCEndOfSale

Salesforce Asset and Revenue Lifecycle Management (RLM) project for handling End of Sale scenarios and automatic product replacements during renewals.

## Overview

This project enables automatic product replacement during renewal quotes when legacy products reach end-of-sale. When a renewal quote is created with a product marked for end-of-sale, the system can automatically replace it with the designated replacement product.

### Key Features

- **Product End-of-Sale Tracking**: Custom `RenewalReplacementProduct__c` field on Product2 to specify replacement products
- **Renewal Quote Detection**: Apex utilities to identify renewal quotes based on `OriginalActionType` field
- **Automatic Product Replacement**: Replace legacy products with new products on renewal quotes via Quick Action buttons
- **Lightning Web Component UI**: User-friendly Quick Actions on Quote pages for product replacement
- **Asset Renewal Testing**: Scripts to create renewal quotes from existing assets
- **Test Data Infrastructure**: Complete test data setup for accounts, products, quotes, and assets
- **Decision Table Management**: Scripts to refresh Salesforce Decision Tables after product changes

## Project Structure

```
ARCEndOfSale/
├── README.md                          # This file
├── CLAUDE.md                          # Developer guidance for AI assistants
├── DEPLOYMENT.md                      # Deployment instructions
├── prd/                               # Product Requirements Documents
│   └── PRD_266_Renewals_EndOfSale.md # Main requirements document
├── force-app/main/default/            # Salesforce metadata
│   ├── classes/                       # Apex classes
│   │   ├── QuoteRenewalChecker.*      # Detect renewal quotes
│   │   ├── QuoteRenewalProductReplacer.* # Replace products on renewals
│   │   └── RepriceQuotesPST.*         # Reprice quotes via PST API
│   ├── lwc/quoteRenewalProductReplacer/ # Lightning Web Component for UI
│   ├── quickActions/                  # Quick Actions for Quote page
│   │   ├── Quote.Check_Renewal_Replacement_Products.*
│   │   └── Quote.Replace_Renewal_Products.*
│   ├── objects/Product2/fields/       # Custom Product2 fields
│   │   └── RenewalReplacementProduct__c.field-meta.xml
│   └── layouts/                       # Page layouts with Quick Actions
├── data/                              # Test data and import scripts
│   ├── test_accounts/                 # Account test data
│   ├── test_products/                 # Product test data with renewals
│   ├── test_quotes/                   # Quote test data with line items
│   └── test_renewal/                  # Asset renewal and quote creation
├── scripts/decision_tables/           # Decision table refresh utilities
├── docs/                              # Additional documentation
└── helpful_data_model_files/          # Salesforce object schemas
```

## Getting Started

### Prerequisites

- Salesforce org with Revenue Lifecycle Management (RLM) enabled
- Salesforce CLI (`sf`) installed and configured
- Python 3.x for data import scripts
- Python `requests` library: `pip install requests`

### Quick Start

1. **Deploy Metadata**
   ```bash
   sf project deploy start --target-org your-org-alias
   ```

2. **Import All Test Data (Recommended)**
   ```bash
   cd data
   python import_all_test_data.py --org your-org-alias
   ```

   This single command imports Account, Product, and Quote with all related records.

   **Or import individually:**
   ```bash
   # Import account
   cd data/test_accounts
   python import_account.py --org your-org-alias

   # Import product with replacement
   cd ../test_products
   python import_with_replacement_product.py --org your-org-alias

   # Import quote with line items, automatic repricing, order creation, and asset generation
   cd ../test_quotes
   python import_quote.py --org your-org-alias
   ```

## Core Components

### 1. Custom Fields

**Product2.RenewalReplacementProduct__c**
- Type: Lookup to Product2
- Purpose: Specifies which product should replace this one during renewals
- Location: `force-app/main/default/objects/Product2/fields/`

### 2. Apex Classes

**QuoteRenewalChecker**
- Detects if a Quote is a renewal quote
- Methods:
  - `isRenewalQuote(Id quoteId)` - Check by Quote ID
  - `isRenewalQuote(Quote quote)` - Check by Quote record
  - `areRenewalQuotes(Set<Id>)` - Bulk check multiple quotes
  - `filterRenewalQuotes(List<Quote>)` - Filter list to renewal quotes only

**QuoteRenewalProductReplacer**
- Replaces products on renewal quotes with their designated replacements
- Methods:
  - `@AuraEnabled replaceProductsOnRenewalQuote(Id quoteId)` - Replace products on one quote (called from LWC)
  - `replaceProductsOnRenewalQuotes(Set<Id>)` - Bulk replace on multiple quotes
- Returns detailed results showing what was replaced
- Automatically reprices the quote after replacement

**RepriceQuotesPST**
- Reprices quotes using Place Sales Transaction (PST) API
- Invocable method that can be called from Flow, Process Builder, or Apex
- Method:
  - `repriceQuotesPST(List<String> quoteIds)` - Reprice one or more quotes
- Forces repricing with full configuration and validation

### 3. Lightning Web Component

**quoteRenewalProductReplacer**
- User interface for the product replacement feature
- Automatically invoked when Quick Action button is clicked
- Displays success/error messages with toast notifications
- Shows number of products replaced and asks user to refresh page
- Location: `force-app/main/default/lwc/quoteRenewalProductReplacer/`

### 4. Quick Actions

**Quote.Check_Renewal_Replacement_Products**
- Label: "Check Renewal Replacement Products"
- Same LWC component as Replace action (both check and optionally replace)
- Accessible from Quote record page

**Quote.Replace_Renewal_Products**
- Label: "Replace Renewal Products"
- Invokes `quoteRenewalProductReplacer` LWC component
- Accessible from Quote record page
- Location: `force-app/main/default/quickActions/`

### 5. Test Data Scripts

All test data scripts support idempotent or incremental creation:

- **test_accounts**: Creates "Labubu Industries" account (idempotent)
- **test_products**: Creates "Enterprise Campaign Manager (Legacy)" product with renewal replacement (idempotent)
- **test_quotes**: Creates quotes with line items, automatically reprices them, creates orders, activates orders, and generates assets (auto-increments names)
- **test_renewal**: Finds assets and creates renewal quotes using Salesforce Renew Assets API

See individual README files in each data directory for detailed usage.

## Common Workflows

### Set Up End-of-Sale Product

1. Create or identify the replacement product
2. Update the legacy product's `RenewalReplacementProduct__c` field to point to the replacement
3. Refresh pricing decision tables:
   ```bash
   python scripts/decision_tables/refresh_decision_table_standalone.py \
     --org your-org-alias \
     --tables Price_Book_Entry_Decision_Table_v2
   ```

### Process Renewal Quote (UI - Recommended)

1. Navigate to a renewal Quote record in Salesforce
2. Click the "Replace Renewal Products" button (Quick Action)
3. The component will:
   - Check if the quote is a renewal quote
   - Replace products with their renewal replacements
   - Automatically reprice the quote
   - Display success message with count of products replaced
4. Refresh the page to see updated line items

### Process Renewal Quote (Programmatically)

```apex
// Check if quote is a renewal
Id quoteId = '0Q0XXXXXXXXXXXX';
Boolean isRenewal = QuoteRenewalChecker.isRenewalQuote(quoteId);

if (isRenewal) {
    // Replace products with end-of-sale replacements
    QuoteRenewalProductReplacer.ReplacementResult result = 
        QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote(quoteId);
    
    System.debug('Products Replaced: ' + result.productsReplaced);
    for (QuoteRenewalProductReplacer.ReplacementDetail detail : result.replacements) {
        System.debug('Replaced: ' + detail.originalProductName + 
                     ' → ' + detail.replacementProductName);
    }
    
    // Note: Repricing happens automatically in replaceProductsOnRenewalQuote
}
```

### Create and Test Renewal Quote

```bash
# 1. Create test data (account, product, quote, order, asset)
cd data
python import_all_test_data.py --org your-org-alias

# 2. Find assets available for renewal
cd test_renewal
python create_renewal.py --org your-org-alias

# 3. Create a renewal quote from an asset
python create_renewal.py --org your-org-alias --renew-asset 02iXXXXXXXXXXXXXXX

# 4. Navigate to the renewal quote in Salesforce and test the Quick Action
```

### Create Test Data End-to-End

**Option 1: Use Consolidated Script (Recommended)**
```bash
# Import everything in one command
cd data
python import_all_test_data.py --org orgfarmorg

# With custom parameters
python import_all_test_data.py --org orgfarmorg \
  --quote-name "Q1 Renewal" \
  --quantity 25 \
  --skip-dt-refresh
```

**Option 2: Import Individually**
```bash
# 1. Create account
cd data/test_accounts
python import_account.py --org orgfarmorg

# 2. Create product with replacement
cd ../test_products
python import_with_replacement_product.py --org orgfarmorg

# 3. Create quote with product
cd ../test_quotes
python import_quote.py --org orgfarmorg --quantity 15
```

**Verify the data:**
```bash
sf data query \
  --query "SELECT Id, Name, (SELECT Product2.Name, Quantity FROM QuoteLineItems) FROM Quote WHERE Name LIKE 'Test Quote%' ORDER BY CreatedDate DESC LIMIT 1" \
  --target-org orgfarmorg
```

## Documentation

- **[CLAUDE.md](./CLAUDE.md)**: Development guidance and commands
- **[DEPLOYMENT.md](./DEPLOYMENT.md)**: Deployment instructions and troubleshooting
- **[PRD](./prd/PRD_266_Renewals_EndOfSale.md)**: Product requirements and business rules
- **[Decision Tables Guide](./docs/decision-tables-guide.md)**: Decision table refresh documentation
- **[Data Model Files](./helpful_data_model_files/)**: Salesforce object schemas

### Data Model Reference

Key Salesforce objects used in this project:
- **Product2**: Products with renewal replacement configuration
- **Quote**: Renewal quotes with `OriginalActionType = 'Renew'`
- **QuoteLineItem**: Line items on quotes
- **AppUsageAssignment**: Auto-created with `AppUsageType = 'RevenueLifecycleManagement'`
- **Opportunity**: Required parent for quotes
- **Account**: Account associated with quotes

See `helpful_data_model_files/` for complete field definitions and relationships.

## Development

### Working with Apex Classes

```bash
# Deploy Apex classes
sf project deploy start --metadata ApexClass --target-org your-org-alias

# Run tests
sf apex run test --test-level RunLocalTests --target-org your-org-alias

# Execute anonymous Apex
sf apex run --target-org your-org-alias --file script.apex
```

### Working with Decision Tables

```bash
# Refresh a single decision table
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org your-org-alias \
  --tables Price_Book_Entry_Decision_Table_v2

# Refresh multiple tables
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org your-org-alias \
  --tables "Table1,Table2,Table3"

# Incremental refresh (faster)
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org your-org-alias \
  --tables Price_Book_Entry_Decision_Table_v2 \
  --incremental
```

### Querying Test Data

```bash
# Find all test accounts
sf data query --query "SELECT Id, Name FROM Account WHERE Name LIKE '%Labubu%'" --target-org your-org-alias

# Find products with replacements
sf data query --query "SELECT Id, Name, RenewalReplacementProduct__r.Name FROM Product2 WHERE RenewalReplacementProduct__c != null" --target-org your-org-alias

# Find renewal quotes
sf data query --query "SELECT Id, Name, OriginalActionType, (SELECT Product2.Name FROM QuoteLineItems) FROM Quote WHERE OriginalActionType = 'Renew'" --target-org your-org-alias
```

## User Interface

### Quick Actions on Quote Page

Two Quick Action buttons are available on Quote record pages:

1. **Check Renewal Replacement Products**
   - Checks if products need replacement
   - Shows informational messages
   - Performs replacement if needed

2. **Replace Renewal Products**
   - Same functionality as Check button
   - Different label for clarity

Both buttons:
- Automatically detect if quote is a renewal quote
- Replace legacy products with designated replacements
- Automatically reprice the quote after replacement
- Display toast notifications with results
- Ask user to manually refresh page to see changes

### Using the Quick Actions

1. Navigate to a Quote record page in Salesforce
2. Look for the action buttons in the highlights panel or action menu
3. Click "Replace Renewal Products"
4. Wait for the success message (e.g., "Replaced 1 product(s) on renewal quote...")
5. Refresh the page to see updated line items

**Note:** The Quick Actions only work on renewal quotes (where `OriginalActionType = 'Renew'`). For non-renewal quotes, you'll see a warning message.

## Testing

### Test Coverage

- **QuoteRenewalChecker**: 100% coverage with unit tests for all methods
- **QuoteRenewalProductReplacer**: 100% coverage with integration tests

### Running Tests

```bash
# Run all tests
sf apex run test --test-level RunLocalTests --target-org your-org-alias

# Run specific test class
sf apex run test --tests QuoteRenewalCheckerTest --target-org your-org-alias
```

### End-to-End Testing Workflow

1. **Set up test data:**
   ```bash
   cd data
   python import_all_test_data.py --org orgfarmorg
   ```

2. **Create a renewal quote:**
   ```bash
   cd test_renewal
   python create_renewal.py --org orgfarmorg --renew-asset <asset-id>
   ```

3. **Test the UI:**
   - Navigate to the renewal quote in Salesforce
   - Click "Replace Renewal Products" button
   - Verify success message appears
   - Refresh the page
   - Verify line item product has been replaced

4. **Verify programmatically:**
   ```bash
   sf data query \
     --query "SELECT Id, Name, (SELECT Product2.Name, Product2.RenewalReplacementProduct__c FROM QuoteLineItems) FROM Quote WHERE Id='<quote-id>'" \
     --target-org orgfarmorg
   ```

## Troubleshooting

### Common Issues

**Product not replaced on renewal quote**
- Verify the product has `RenewalReplacementProduct__c` set
- Check that the quote has `OriginalActionType = 'Renew'`
- Ensure the replacement product has an active pricebook entry

**Decision table refresh fails**
- Verify the decision table name is correct
- Check that Python `requests` library is installed
- Ensure you have access to the decision table in your org

**Test data import fails**
- Check that dependencies are created in order (Account → Product → Quote)
- Verify standard pricebook entries exist for products
- Ensure required fields are populated

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed troubleshooting steps.

## Architecture Notes

### Renewal Detection

Quotes are identified as renewals based on the `OriginalActionType` field:
- **Value**: `'Renew'`
- **Field Type**: Read-only picklist (set by Salesforce CPQ/RLM)
- **Cannot be set manually**: Must be set through Salesforce renewal process

### Product Replacement Flow

1. User clicks "Replace Renewal Products" Quick Action on Quote page
2. LWC component `invoke()` method is called with Quote `recordId`
3. Component calls `QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote(quoteId)`
4. Apex logic:
   - Check if Quote is a renewal (`OriginalActionType = 'Renew'`)
   - Query all QuoteLineItems for the Quote
   - For each line item, check if Product2 has `RenewalReplacementProduct__c` set
   - If replacement exists, delete old QuoteLineItem and create new one with replacement product (Product2Id is not updateable)
   - Automatically reprice the quote using `RepriceQuotesPST`
5. Return detailed results to LWC showing what was replaced
6. LWC displays success toast with count of products replaced
7. User manually refreshes page to see updated line items

### AppUsageAssignment Auto-Creation

When a Quote is created, Salesforce automatically creates an `AppUsageAssignment` record with:
- `RecordId`: Quote ID
- `AppUsageType`: `'RevenueLifecycleManagement'`

This record cannot be created manually without causing a duplicate error.

## Contributing

When making changes to this project:

1. Update relevant documentation (README, CLAUDE.md, etc.)
2. Add/update test coverage for Apex classes
3. Test data scripts should be idempotent or auto-increment
4. Refresh decision tables after product/pricing changes
5. Update the PRD if business requirements change

## Resources

### Salesforce Documentation

- [Quote Object Reference](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quote.htm)
- [Revenue Cloud - Renewals](https://help.salesforce.com/s/articleView?id=ind.qocal_renew_assets.htm&type=5)
- [Asset Lifecycle Management](https://help.salesforce.com/s/articleView?id=ind.qocal_asset_lifecycle.htm&type=5)

### Internal Documentation

- [Product Requirements Document](./prd/PRD_266_Renewals_EndOfSale.md)
- [Decision Tables Guide](./docs/decision-tables-guide.md)
- [Object Descriptions Summary](./helpful_data_model_files/object_descriptions_summary.md)

## License

Internal Salesforce project - see your organization's licensing policies.

## Contact

For questions about this project, see the PRD or consult your Salesforce development team.

---

**Last Updated**: 2026-05-20  
**Salesforce API Version**: 67.0
