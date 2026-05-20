# Test Product Data

This directory contains SFDX Data Tree JSON files for creating test products with related records.

## Enterprise Campaign Manager (Legacy)

A test product for End of Sale scenarios.

**Product Details:**
- **Name:** Enterprise Campaign Manager (Legacy)
- **Product Code:** ECM-LEGACY
- **Family:** Software
- **Price:** $1,200/user/year
- **Selling Model:** Term Annual (Yearly)
- **Category:** Licenses
- **Renewal Replacement Product:** QuantumBit Generative AI License (automatically looked up)

**Related Records Created:**
1. **Product2** - The product record
2. **PricebookEntry** - Standard price book entry at $1,200 with ProductSellingModel="Term Annual"
3. **ProductSellingModelOption** - Links to "Term Annual" selling model
4. **ProductCategoryProduct** - Associates with "Licenses" category

## Usage

### Import with Renewal Replacement Product (Recommended)

Use the Python script to automatically lookup and set the renewal replacement product:

```bash
cd data/test_products
python import_with_replacement_product.py --org orgfarmorg
```

This script:
1. **Checks if the product already exists** by querying for ProductCode='ECM-LEGACY'
2. If product exists, reports the existing Product2 ID and exits (no duplicate created)
3. If product doesn't exist:
   - **Dynamically looks up ProductSellingModel ID** for "Term Annual" (no hardcoded IDs)
   - **Dynamically looks up Standard Pricebook ID** (no hardcoded IDs)
   - **Dynamically looks up Replacement Product ID** for "QuantumBit Generative AI License" (no hardcoded IDs)
   - Updates `Product2.json` with the looked-up `RenewalReplacementProduct__c` ID
   - Updates `PricebookEntry.json` with looked-up `ProductSellingModelId` and `Pricebook2Id`
   - Imports all records using the data tree plan
   - Automatically refreshes the Price_Book_Entry_Decision_Table_v2 decision table

**Key Feature:** All IDs are dynamically looked up from the target org, making the script portable across different Salesforce orgs without manual ID updates. The JSON files use placeholders (e.g., `PLACEHOLDER_REPLACEMENT_PRODUCT`) that are replaced at runtime.

**Output when product exists:**
```
→ Checking if product already exists...
✓ Product 'Enterprise Campaign Manager (Legacy)' already exists with ID: 01tXXXXXXXXXXX
  ProductCode: ECM-LEGACY
  No action taken.
```

**Output when product doesn't exist:**
```
→ Checking if product already exists...
✗ Product does not exist. Creating...
✓ Found replacement product: 'QuantumBit Generative AI License' (ID: 01tXXXXXXXXXXX)
...
✓ Import completed successfully!
```

**Custom replacement product:**
```bash
python import_with_replacement_product.py --org orgfarmorg --replacement-product "My Product Name"
```

**Skip decision table refresh:**
```bash
python import_with_replacement_product.py --org orgfarmorg --skip-dt-refresh
```

**Custom decision tables to refresh:**
```bash
python import_with_replacement_product.py --org orgfarmorg --decision-tables "Table1,Table2,Table3"
```

### Import All Records (Manual)

```bash
cd data/test_products
sf data import tree --plan enterprise-campaign-manager-plan.json --target-org orgfarmorg
```

**Note:** Manual import won't set the renewal replacement product unless you manually edit `Product2.json` first.

### Import Individual Objects

```bash
# Product only
sf data import tree --files Product2.json --target-org orgfarmorg

# Product + Price Book Entry
sf data import tree --files Product2.json,PricebookEntry.json --target-org orgfarmorg
```

### Delete Test Data

```bash
# Delete by Product Code
sf data delete record --sobject Product2 --where "ProductCode='ECM-LEGACY'" --target-org orgfarmorg
```

## File Structure

```
data/test_products/
├── README.md                                  # This file
├── import_with_replacement_product.py         # Python script to import with lookup
├── enterprise-campaign-manager-plan.json      # Data import plan
├── Product2.json                              # Product records
├── PricebookEntry.json                        # Price book entries
├── ProductSellingModelOption.json             # Selling model options
└── ProductCategoryProduct.json                # Category associations
```

## Data Plan Format

The `enterprise-campaign-manager-plan.json` orchestrates the import order:

1. **Product2** - Created first (saveRefs: true to capture IDs)
2. **PricebookEntry** - References Product2 via `@Product2Ref1`
3. **ProductSellingModelOption** - References Product2 via `@Product2Ref1`
4. **ProductCategoryProduct** - References Product2 via `@Product2Ref1`

**Note:** The JSON files contain placeholder values that are automatically replaced by the import script with actual IDs from the target org:
- **Product2.json**: `PLACEHOLDER_REPLACEMENT_PRODUCT` → looked up by product name
- **PricebookEntry.json**: `PLACEHOLDER_STANDARD_PRICEBOOK` → looked up by IsStandard=true
- **PricebookEntry.json**: `PLACEHOLDER_TERM_ANNUAL` → looked up by ProductSellingModel name

This makes the data files portable across different Salesforce environments without requiring manual ID updates.

## Prerequisites

The following records must exist in the target org:
- **Standard Pricebook** (always exists - dynamically looked up by script)
- **ProductSellingModel** with Name "Term Annual" (dynamically looked up by script)
- **ProductCategory** with Name "Licenses" (referenced in ProductCategoryProduct.json)
- **QuantumBit Generative AI License** product (or use --replacement-product to specify a different one)
- **Decision tables** for product qualification (if using automatic refresh)
- **Python requests library** for decision table refresh: `pip install requests`

## Adding More Test Products

To add another test product:

1. Copy the JSON files and rename (e.g., `Product2-v2.json`)
2. Update the product details in the new files
3. Update the plan JSON to reference the new files
4. Change `referenceId` values to avoid conflicts (e.g., `Product2Ref2`)

## Querying Created Data

```bash
# Find the product
sf data query \
  --query "SELECT Id, Name, ProductCode FROM Product2 WHERE ProductCode='ECM-LEGACY'" \
  --target-org orgfarmorg

# Find price book entry
sf data query \
  --query "SELECT Id, Product2.Name, UnitPrice FROM PricebookEntry WHERE Product2.ProductCode='ECM-LEGACY' AND Pricebook2.IsStandard=true" \
  --target-org orgfarmorg

# Find selling model option
sf data query \
  --query "SELECT Id, Product2.Name, ProductSellingModel.Name FROM ProductSellingModelOption WHERE Product2.ProductCode='ECM-LEGACY'" \
  --target-org orgfarmorg

# Find category association
sf data query \
  --query "SELECT Id, Product.Name, ProductCategory.Name FROM ProductCategoryProduct WHERE Product.ProductCode='ECM-LEGACY'" \
  --target-org orgfarmorg
```

## Notes

- The data tree format automatically handles parent-child relationships using `@ReferenceId` syntax
- Records are created in the order specified in the plan
- `saveRefs: true` means the ID will be captured for use by child records
- `resolveRefs: true` means this record will use IDs from parent records

## Troubleshooting

**Error: "We couldn't process your request because you don't have access to [Field]"**
- Check field-level security for your user/profile
- Verify the field is createable: `sf sobject describe --sobject [Object] --target-org orgfarmorg`

**Error: "invalid cross reference id"**
- Ensure `saveRefs: true` is set on the parent object in the plan
- Check that `@ReferenceId` matches exactly between parent and child

**Duplicate records created**
- Use external IDs or check for existing records before import
- Consider using UPSERT operations instead of INSERT

**Decision table refresh fails**
- Ensure the decision table refresh script exists at `scripts/decision_tables/refresh_decision_table_standalone.py`
- Verify Python `requests` library is installed: `pip install requests`
- Check decision table names are correct: `sf data query --query "SELECT DeveloperName FROM DecisionTable WHERE Status='Active'" --target-org orgfarmorg`
- Skip refresh if not needed: `python import_with_replacement_product.py --org orgfarmorg --skip-dt-refresh`

**Warning: Decision table refresh encountered errors**
- The product data was imported successfully
- Decision tables may need manual refresh
- Use the decision table refresh script separately: `python ../../scripts/decision_tables/refresh_decision_table_standalone.py --org orgfarmorg --tables "Price_Book_Entry_Decision_Table_v2"`
