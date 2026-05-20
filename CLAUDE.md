# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ARCEndOfSale - Project working with Salesforce Asset and Revenue Lifecycle Management (RLM) objects.

## Repository Layout

```
ARCEndOfSale/
├── .claude/                          # Claude Code configuration
│   └── settings.local.json          # Local Claude settings
├── .cursor/                          # Cursor IDE configuration
├── .gus/                            # GUS plugin cache and audit logs
│   └── audit/                       # GUS operation audit logs
├── CLAUDE.md                        # This file - guidance for Claude Code
├── DEPLOYMENT.md                    # Deployment guide for Salesforce metadata
├── sfdx-project.json                # Salesforce DX project configuration
├── .forceignore                     # Files to ignore in Salesforce deployments
├── force-app/main/default/          # Salesforce metadata (fields, layouts, profiles, classes)
│   ├── classes/                     # Apex classes (API Version 67.0)
│   │   ├── QuoteRenewalChecker.*    # Utility to detect renewal quotes
│   │   ├── QuoteRenewalCheckerTest.* # Test class
│   │   ├── QuoteRenewalProductReplacer.*  # Replace products on renewal quotes
│   │   ├── QuoteRenewalProductReplacerTest.* # Test class
│   │   ├── RepriceQuotesPST.*       # Reprice quotes using PST API
│   │   └── *.cls-meta.xml           # Meta files (all set to apiVersion 67.0)
│   ├── lwc/                         # Lightning Web Components
│   │   └── quoteRenewalProductReplacer/  # UI for product replacement
│   │       ├── quoteRenewalProductReplacer.js
│   │       ├── quoteRenewalProductReplacer.html
│   │       └── quoteRenewalProductReplacer.js-meta.xml
│   ├── quickActions/                # Quick Actions for Quote page
│   │   ├── Quote.Check_Renewal_Replacement_Products.quickAction-meta.xml
│   │   └── Quote.Replace_Renewal_Products.quickAction-meta.xml
│   ├── objects/Product2/fields/     # Custom fields on Product2
│   │   └── RenewalReplacementProduct__c.field-meta.xml
│   ├── layouts/                     # Page layout modifications
│   │   ├── Product2-Product Layout.layout-meta.xml
│   │   ├── Product2-RLM Product Layout.layout-meta.xml
│   │   └── Quote-RLM Quote Layout.layout-meta.xml  # Has Quick Actions
│   └── profiles/                    # Profile field permissions
│       └── Admin.profile-meta.xml
├── manifest/                        # Deployment manifests
│   └── package.xml                  # Package manifest for deployment
├── scripts/decision_tables/         # Decision Table refresh scripts
│   ├── refresh_decision_table_standalone.py  # Standalone refresh script
│   └── refresh_decision_table.py    # CumulusCI-based version
├── docs/                            # Project documentation
│   └── decision-tables-guide.md     # Decision Table refresh guide
├── data/                            # Test data and import scripts
│   ├── README.md                    # Test data overview
│   ├── import_all_test_data.py      # Master import script
│   ├── test_accounts/               # Account test data
│   │   ├── README.md
│   │   ├── import_account.py
│   │   └── Account.json
│   ├── test_products/               # Test product data (SFDX Data Tree format)
│   │   ├── README.md
│   │   ├── import_with_replacement_product.py
│   │   ├── enterprise-campaign-manager-plan.json
│   │   └── *.json                   # Product, PricebookEntry, etc.
│   ├── test_quotes/                 # Quote test data
│   │   ├── README.md
│   │   ├── import_quote.py          # Creates quote, order, assets
│   │   └── *.json                   # Generated files
│   └── test_renewal/                # Asset renewal and renewal quote creation
│       ├── README.md
│       └── create_renewal.py        # Find assets, create renewal quotes
├── .cursor/skills/                  # Claude Code skill definitions
│   └── decision-tables.md           # Decision Table refresh skill
├── helpful_data_model_files/        # Salesforce object describe outputs
│   ├── Asset_describe.json          # Asset object schema (76 fields)
│   ├── AssetAction_describe.json    # AssetAction schema (39 fields)
│   ├── AssetActionSource_describe.json  # AssetActionSource schema (45 fields)
│   ├── AssetStatePeriod_describe.json   # AssetStatePeriod schema (28 fields)
│   ├── AppUsageAssignment_describe.json # AppUsageAssignment schema (10 fields)
│   ├── Product2_describe.json       # Product2 schema (57 fields)
│   ├── Quote_describe.json          # Quote schema (104 fields)
│   ├── QuoteLineItem_describe.json  # QuoteLineItem schema (97 fields)
│   ├── QuoteLineDetail_describe.json # QuoteLineDetail schema (22 fields)
│   ├── asset_example_rlm_generated.json # Example Asset record
│   └── object_descriptions_summary.md   # Human-readable summary
└── prd/                             # Product Requirements Documents
    └── PRD_266_Renewals_ EndOfSale.md  # Main PRD for this feature
```

### Directory Purposes

- **force-app/main/default/** - Salesforce metadata for deployment (custom fields, page layouts, profiles)
- **manifest/** - Package manifests for deploying metadata to Salesforce orgs
- **scripts/decision_tables/** - Python scripts for refreshing Salesforce Decision Tables
- **docs/** - Documentation including decision table refresh guide
- **data/test_products/** - Test product data files (SFDX Data Tree JSON format)
- **helpful_data_model_files/** - Reference this for Salesforce object schemas when writing queries or data manipulation code
- **prd/** - Reference this for business requirements, user stories, and acceptance criteria
- **.claude/** - Claude Code configuration (automatically managed)
- **.cursor/skills/** - Skill definitions for Claude Code automation
- **.gus/** - GUS plugin data (automatically managed)

## Product Requirements Document (PRD)

**IMPORTANT:** The product requirements document is located in `./prd/PRD_266_Renewals_ EndOfSale.md`. Always reference this PRD to understand:
- Feature requirements and business logic
- User stories and acceptance criteria
- Business rules and constraints
- Expected behavior and workflows

When implementing features or writing code, consult the PRD first to ensure alignment with product requirements.

## Salesforce Data Models

**IMPORTANT:** When writing code that interacts with Salesforce objects, always reference the data model files in `./helpful_data_model_files/` to understand field names, types, relationships, and API constraints.

### Available Data Model Files

Located in `./helpful_data_model_files/`:

1. **Asset_describe.json** - Complete Asset object schema (76 fields, 192 child relationships)
   - Key fields: Id, Name, Status, CurrentMrr, CurrentQuantity, Product2Id, AccountId, ContactId, LifecycleStartDate, LifecycleEndDate, HasLifecycleManagement

2. **AssetStatePeriod_describe.json** - Asset State Period schema (28 fields)
   - Tracks asset states over time periods
   - Key fields: AssetId (parent), StartDate, EndDate, Quantity, Amount, Mrr, SegmentIdentifier

3. **AssetAction_describe.json** - Asset Action schema (39 fields)
   - Records actions taken on assets (renewals, amendments, cancellations)
   - Key fields: AssetId (parent), Type, CategoryEnum, ActionDate, MrrChange, QuantityChange, TotalAmount

4. **AssetActionSource_describe.json** - Asset Action Source schema (45 fields)
   - Source records that triggered asset actions
   - Key fields: AssetActionId (parent), ExternalReference, ReferenceEntityItemId, ProductAmount, StartDate, EndDate

5. **AppUsageAssignment_describe.json** - Application Usage Assignment schema (10 fields)
   - Links assets to usage records
   - Key fields: AssetId (parent), RecordId, AppUsageType

6. **Product2_describe.json** - Product object schema (57 fields)
   - Product catalog and definitions
   - Key fields: Id, Name, ProductCode, Family, IsActive, Description

7. **Quote_describe.json** - Quote object schema (104 fields)
   - Sales quotes and proposals
   - Key fields: Id, Name, OpportunityId, AccountId, Status, TotalPrice, ExpirationDate

8. **QuoteLineItem_describe.json** - Quote Line Item schema (97 fields)
   - Line items on quotes
   - Key fields: Id, QuoteId (parent), Product2Id, Quantity, UnitPrice, ListPrice, TotalPrice

9. **QuoteLineDetail_describe.json** - Quote Line Detail schema (22 fields)
   - Detailed breakdown/segments of quote line items
   - Key fields: Id, QuoteLineItemId (parent), Name, Quantity, TotalPrice, ReferenceDate

10. **asset_example_rlm_generated.json** - Example asset record with RLM data

11. **object_descriptions_summary.md** - Human-readable summary of all objects and relationships

### Object Relationships

- Asset (parent) → AssetActions, AssetStatePeriods, AppUsageAssignments (children)
- AssetAction (parent) → AssetActionSources (children)
- Product2 (parent) → Assets (children via Product2Id)
- Quote (parent) → QuoteLineItems (children)
- QuoteLineItem (parent) → QuoteLineDetails (children)
- QuoteLineItem (child) → Quote (parent via QuoteId), Product2 (via Product2Id)
- QuoteLineDetail (child) → QuoteLineItem (parent via QuoteLineItemId)

### When to Reference Data Model Files

**Always consult the describe files when:**

1. **Writing SOQL queries** - Verify exact field names (case-sensitive), queryable fields, and parent/child relationship names
2. **Creating or updating records** - Check required fields, field types, picklist values, and validation constraints
3. **Working with relationships** - Confirm relationship field names (e.g., `AssetId` vs `Asset__c`) and cardinality
4. **Determining field capabilities** - Check if fields are createable, updateable, filterable, or calculated/formula fields
5. **Understanding data types** - Verify field types (string, number, date, reference) and length limits before processing
6. **Mapping between objects** - Identify foreign key fields and lookup relationships

**How to use the files:**

- **Quick reference**: Start with `object_descriptions_summary.md` for field lists and relationships
- **Detailed validation**: Open the specific `*_describe.json` file to check:
  - Field properties: `type`, `length`, `nillable`, `createable`, `updateable`
  - Picklist values: `picklistValues` array
  - Relationship details: `referenceTo`, `relationshipName`, `childRelationships`
  - Field help text and labels: `inlineHelpText`, `label`
- **Example data**: Reference `asset_example_rlm_generated.json` to see real record structure

**Important notes:**
- Salesforce API names are case-sensitive - always use exact field names from describe files
- Custom fields end with `__c`, custom objects with `__c`, standard fields are camelCase
- Not all fields are writeable - check `createable` and `updateable` properties before attempting DML

## Development Commands

### Salesforce CLI Commands

**Target Org**: `orgfarmorg`

#### Deploy Metadata
```bash
# Deploy all metadata
sf project deploy start --target-org orgfarmorg

# Deploy using manifest
sf project deploy start --target-org orgfarmorg --manifest manifest/package.xml

# Validate without deploying
sf project deploy validate --target-org orgfarmorg --manifest manifest/package.xml

# Deploy specific metadata types
sf project deploy start --target-org orgfarmorg --metadata "CustomField:Product2.RenewalReplacementProduct__c"
```

#### Retrieve Metadata
```bash
# Retrieve specific object layouts
sf project retrieve start --target-org orgfarmorg --metadata "Layout:Product2-*"

# Retrieve object describe information
sf sobject describe --sobject Product2 --target-org orgfarmorg --json > ./helpful_data_model_files/Product2_describe.json
```

#### Query Data
```bash
# Execute SOQL query
sf data query --query "SELECT Id, Name, RenewalReplacementProduct__c FROM Product2 LIMIT 10" --target-org orgfarmorg
```

#### Load Test Data
```bash
# Import test product data with renewal replacement + auto-refresh Price_Book_Entry_Decision_Table_v2 (Recommended)
cd data/test_products
python import_with_replacement_product.py --org orgfarmorg

# Import without decision table refresh
python import_with_replacement_product.py --org orgfarmorg --skip-dt-refresh

# Import with custom decision tables
python import_with_replacement_product.py --org orgfarmorg --decision-tables "Table1,Table2"

# Or import manually without renewal replacement (not recommended)
sf data import tree --plan enterprise-campaign-manager-plan.json --target-org orgfarmorg

# Delete test data
sf data delete record --sobject Product2 --where "ProductCode='ECM-LEGACY'" --target-org orgfarmorg

# Verify data
sf data query \
  --query "SELECT Id, Name, RenewalReplacementProduct__r.Name FROM Product2 WHERE ProductCode='ECM-LEGACY'" \
  --target-org orgfarmorg
```

See `data/test_products/README.md` for details on test data structure.

#### Decision Table Refresh
```bash
# Refresh a single decision table
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables DecisionTableName

# Refresh multiple tables
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables "Table1,Table2,Table3"

# Incremental refresh (faster, for minor changes)
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables DecisionTableName \
  --incremental

# List all active decision tables
sf data query \
  --query "SELECT DeveloperName, MasterLabel FROM DecisionTable WHERE Status = 'Active'" \
  --target-org orgfarmorg
```

See `DEPLOYMENT.md` for detailed deployment instructions and troubleshooting.
See `docs/decision-tables-guide.md` for comprehensive decision table refresh documentation.

## Common Development Patterns and Pitfalls

### Working with Salesforce Metadata

**When deploying Quick Actions:**
- Always deploy in this order: Apex → LWC → Quick Actions → Layouts
- Verify deployment success before testing in UI
- Clear browser cache after LWC deployment

**When updating page layouts:**
- Always retrieve current layout from org first to avoid overwriting manual changes
- Quick Actions go in `<platformActionList>`, not `<quickActionList>`
- Use `<actionType>QuickAction</actionType>` for Quick Actions
- Use `<sortOrder>` to control button display order

**When working with LWC as Quick Actions:**
```javascript
export default class MyComponent extends LightningElement {
    @api recordId;  // Auto-populated by framework
    
    // REQUIRED for Quick Actions
    @api
    invoke() {
        // This is called when button is clicked
        // recordId is already set at this point
        this.doWork();
    }
}
```

**LWC component metadata for Quick Actions:**
```xml
<targets>
    <target>lightning__RecordAction</target>  <!-- Correct -->
</targets>
<!-- Do NOT use lightning__QuickAction - it's not valid -->
```

**Quick Action metadata structure:**
```xml
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionSubtype>Action</actionSubtype>
    <label>My Action</label>
    <lightningWebComponent>myComponent</lightningWebComponent>  <!-- No c: prefix -->
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <type>LightningWebComponent</type>  <!-- Not LightningComponent -->
</QuickAction>
```

### Working with QuoteLineItem

**Product2Id is NOT updateable**
- Common error: Attempting `UPDATE qli SET Product2Id = newProductId`
- Correct pattern:
  1. Query existing QuoteLineItem with all needed fields
  2. Create NEW QuoteLineItem with new PricebookEntryId (which references new product)
  3. Copy relevant fields (Quantity, Discount, StartDate, etc.)
  4. INSERT new QuoteLineItem
  5. DELETE old QuoteLineItem
- Always query PricebookEntry for replacement product in same Pricebook2Id as quote

**Fields to preserve when replacing QuoteLineItem:**
```apex
QuoteLineItem newQli = new QuoteLineItem(
    QuoteId = oldQli.QuoteId,
    PricebookEntryId = replacementPbe.Id,  // New product's pricebook entry
    Quantity = oldQli.Quantity,
    Discount = oldQli.Discount,
    Description = oldQli.Description,
    StartDate = oldQli.StartDate,
    PeriodBoundary = oldQli.PeriodBoundary,
    PeriodBoundaryDay = oldQli.PeriodBoundaryDay,
    PeriodBoundaryStartMonth = oldQli.PeriodBoundaryStartMonth,
    SubscriptionTerm = oldQli.SubscriptionTerm
    // Do NOT copy: UnitPrice (comes from PricebookEntry)
);
```

### Working with Apex and LWC Integration

**Apex method signature for LWC:**
```apex
@AuraEnabled
public static MyReturnType myMethod(Id recordId) {
    // Method logic
    return result;
}
```

**Return type classes MUST have @AuraEnabled on ALL properties:**
```apex
public class MyReturnType {
    @AuraEnabled public String field1;
    @AuraEnabled public Integer field2;
    @AuraEnabled public List<Detail> details;  // Inner classes need it too
}

public class Detail {
    @AuraEnabled public String name;
    @AuraEnabled public Id recordId;
}
```

**Common error:** Forgetting `@AuraEnabled` on inner class properties
- LWC will receive `undefined` for those fields
- No error thrown, just silent failure
- Always check all levels of nested classes

### Repricing Quotes

**After modifying QuoteLineItems, always reprice:**
```apex
List<String> quoteIds = new List<String>{ String.valueOf(quoteId) };
RepriceQuotesPST.repriceQuotesPST(quoteIds);
```

**Note:** RepriceQuotesPST is already integrated into `QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote()`, so calling it separately is unnecessary when using that method.

### Testing Renewal Quotes

**Cannot create renewal quotes directly**
- Must use Salesforce's renewal process
- `OriginalActionType` is read-only, cannot be set via DML
- Use test script: `python create_renewal.py --org orgfarmorg --renew-asset <asset-id>`
- Script uses Salesforce standard action: `/services/data/v67.0/actions/standard/initiateRenewal`

**Creating test assets for renewal:**
1. Create Account, Product, Quote, QuoteLineItem
2. Create Order from Quote (use CreateOrderFromQuote action)
3. Activate Order (set Status='Activated')
4. Assets are auto-created when Order is activated
5. Use `create_renewal.py` to create renewal quote from asset

### Decision Table Refresh

**When to refresh:**
- After creating/updating Products
- After creating/updating PricebookEntries
- After modifying pricing rules
- After test data imports (unless using `--skip-dt-refresh`)

**Common tables to refresh:**
- `Price_Book_Entry_Decision_Table_v2` - After product/pricing changes
- `RLM_ProductQualification` - After product data loads
- `RLM_ProductCategoryQualification` - After category associations

**Performance tip:** Use `--incremental` for minor changes (much faster)

### API Version Consistency

**Current project standard: API Version 67.0**
- All Apex classes: `<apiVersion>67.0</apiVersion>` in meta.xml files
- LWC components: `<apiVersion>67.0</apiVersion>` in meta.xml files
- REST API calls in Python scripts: `/services/data/v67.0/...`

**When updating API versions:**
- Update ALL Apex class meta.xml files
- Update ALL LWC component meta.xml files
- Update Python scripts that call REST APIs
- Test thoroughly, especially Quote/Order/Asset functionality

### Debugging Tips

**LWC not responding to button click:**
1. Open browser DevTools (F12) → Console tab
2. Check for error: "t.invoke is not a function" → Missing `@api invoke()` method
3. Check for "Cannot read property 'X' of undefined" → Missing `@AuraEnabled` on Apex return type
4. Look for Apex errors in console → Check method signature and annotations

**Quick Action not appearing on page:**
1. Verify Quick Action is deployed: `sf project retrieve start --metadata "QuickAction:Quote.*"`
2. Check page layout has action in `platformActionList`
3. Clear browser cache
4. Check if button is in overflow menu (•••) instead of main area

**Product replacement fails silently:**
1. Check Debug Logs in Salesforce Setup
2. Verify quote is actually a renewal: `SELECT OriginalActionType FROM Quote WHERE Id = '...'`
3. Check replacement product has active PricebookEntry in quote's pricebook
4. Verify user has permissions for QuoteLineItem DML operations

**Test data import fails:**
1. Check dependencies are created in order: Account → Product → Quote
2. Verify standard pricebook exists (required for PricebookEntry)
3. Check that referenced products exist (e.g., replacement product)
4. Look for "requests" library errors → Run `pip install requests`

## Architecture

### Core Components

1. **Custom Field: Product2.RenewalReplacementProduct__c**
   - Lookup relationship to Product2 (self-referencing)
   - Specifies which product should replace this one during renewals
   - Located: `force-app/main/default/objects/Product2/fields/`

2. **Apex Classes (API Version 67.0)**
   - **QuoteRenewalChecker**: Detects renewal quotes by checking `OriginalActionType = 'Renew'`
   - **QuoteRenewalProductReplacer**: Replaces products on renewal quotes
     - `@AuraEnabled` method for LWC integration
     - Returns `ReplacementResult` with `@AuraEnabled` properties
     - Automatically calls `RepriceQuotesPST` after replacement
   - **RepriceQuotesPST**: Reprices quotes using Place Sales Transaction API
   - Located: `force-app/main/default/classes/`

3. **Lightning Web Component**
   - **quoteRenewalProductReplacer**: UI for product replacement
   - **CRITICAL**: Must implement `@api invoke()` method for Quick Action support
   - Uses `@api recordId` to receive Quote ID from framework
   - Displays toast notifications via `ShowToastEvent`
   - Located: `force-app/main/default/lwc/quoteRenewalProductReplacer/`

4. **Quick Actions**
   - **Quote.Check_Renewal_Replacement_Products**
   - **Quote.Replace_Renewal_Products**
   - Type: `LightningWebComponent` (not `LightningComponent`)
   - Uses `<lightningWebComponent>` tag (no `c:` namespace prefix)
   - Located: `force-app/main/default/quickActions/`

5. **Page Layouts**
   - Quick Actions added to `platformActionList` (NOT `quickActionList`)
   - Located: `force-app/main/default/layouts/`

### Product Replacement Flow

1. User clicks Quick Action button on Quote page
2. Salesforce framework calls LWC's `invoke()` method with `recordId`
3. LWC calls `QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote(quoteId)`
4. Apex logic:
   - Checks if quote is renewal (`OriginalActionType = 'Renew'`)
   - Queries QuoteLineItems and related Product2 records
   - For products with `RenewalReplacementProduct__c` set:
     - **IMPORTANT**: `Product2Id` is NOT updateable on QuoteLineItem
     - Must DELETE old QuoteLineItem and CREATE new one with replacement product
     - Preserves fields: Quantity, Discount, StartDate, PeriodBoundary, etc.
   - Automatically reprices quote via `RepriceQuotesPST`
5. Returns `ReplacementResult` to LWC with counts and details
6. LWC displays success toast, user refreshes page manually

### Key Technical Constraints

**QuoteLineItem.Product2Id is NOT updateable**
- Cannot use `UPDATE` statement to change the product
- Must use DELETE old + INSERT new pattern
- Copy all relevant fields from old to new QuoteLineItem
- Query PricebookEntry for replacement product in same pricebook

**Quick Action Requirements**
- LWC must implement `@api invoke()` method
- Quick Action metadata uses `type: LightningWebComponent`
- Use `<lightningWebComponent>` tag (not `<lightningComponent>`)
- No namespace prefix on component name (e.g., `quoteRenewalProductReplacer` not `c:quoteRenewalProductReplacer`)
- Add to `platformActionList` in layout (not `quickActionList`)

**Apex @AuraEnabled Requirements**
- Method must have `@AuraEnabled` annotation
- Return type classes must have `@AuraEnabled` on ALL public properties
- Example:
  ```apex
  public class ReplacementResult {
      @AuraEnabled public Boolean isRenewalQuote;
      @AuraEnabled public Integer productsReplaced;
      // ... all properties need @AuraEnabled
  }
  ```

### Renewal Quote Detection

Quotes are identified as renewals based on the `OriginalActionType` field:
- **Value**: `'Renew'`
- **Field Type**: Read-only picklist (set by Salesforce RLM)
- **Cannot be set manually**: Must be set through Salesforce renewal process
- Use `QuoteRenewalChecker.isRenewalQuote(quoteId)` to check

### Test Data Scripts

Located in `data/` directory:
- **test_accounts**: Creates "Labubu Industries" account (idempotent)
- **test_products**: Creates products with renewal replacements (idempotent)
- **test_quotes**: Creates quotes with line items, orders, and assets (auto-increments)
- **test_renewal**: Finds assets and creates renewal quotes via Salesforce API

Use `python import_all_test_data.py --org orgfarmorg` for complete setup.

## Salesforce Object Reference Documentation

### When to Reference Official Documentation

**Consult the Salesforce documentation when you need to understand:**

1. **Business logic and field purpose** - What a field is used for in Salesforce's data model (e.g., "What does CurrentMrr represent?")
2. **Standard Salesforce behavior** - How Salesforce automatically populates or calculates fields
3. **Best practices** - Salesforce-recommended patterns for using objects (e.g., Asset lifecycle management)
4. **Feature capabilities** - Understanding Revenue Cloud features like amendments, renewals, and cancellations
5. **Field semantics** - The intended meaning and usage of standard fields beyond just their data type
6. **Revenue Cloud-specific fields** - Additional fields and behaviors specific to Revenue Lifecycle Management

**Use the describe files (above) for technical details** like exact field names, types, and API constraints.  
**Use this documentation for conceptual understanding** of how Salesforce intends the objects to be used.

### Documentation Links

Official Salesforce documentation for understanding field purposes, best practices, and use cases:

- [Asset](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asset.htm)
- [AssetAction](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_assetaction.htm)
- [AssetActionSource](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_assetactionsource.htm)
- [AssetStatePeriod](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_assetstateperiod.htm)
- [AppUsageAssignment](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_appusageassignment.htm)
- [Product2] (https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_product2.htm)
- [Quote] (https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quote.htm)
- [QuoteLineItem] (https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quotelineitem.htm)

There are also additional fields, specific to Revenue Cloud, defined in these help topics:
- [Quote] (https://developer.salesforce.com/docs/atlas.en-us.revenue_lifecycle_management_dev_guide.meta/revenue_lifecycle_management_dev_guide/quote_and_order_capture_fields_on_quote.htm)
- [QuoteLineItem] (https://developer.salesforce.com/docs/atlas.en-us.revenue_lifecycle_management_dev_guide.meta/revenue_lifecycle_management_dev_guide/quote_and_order_capture_fields_on_quote_line_item.htm)

The overall Revenue Cloud amendments, renewals, and cancellations feature is documented here: https://help.salesforce.com/s/articleView?id=ind.qocal_asset_lifecycle.htm&type=5
Documentation for general procedures for renewing assets is documented here: https://help.salesforce.com/s/articleView?id=ind.qocal_renew_assets.htm&type=5

## Workflow for Common Modifications

### Adding a New Field to Quote or QuoteLineItem

1. **Check field capabilities first:**
   ```bash
   # Check if field exists and is updateable
   sf sobject describe --sobject QuoteLineItem --target-org orgfarmorg --json | jq '.result.fields[] | select(.name=="FieldName")'
   ```

2. **For custom fields, create field metadata:**
   - Create XML in `force-app/main/default/objects/Quote/fields/` or `QuoteLineItem/fields/`
   - Deploy field before updating layouts

3. **Update page layouts to show field:**
   - Retrieve current layout from org: `sf project retrieve start --metadata "Layout:Quote-RLM Quote Layout"`
   - Add field to appropriate `<layoutSection>`
   - Deploy layout

4. **Update Apex classes if using field in code:**
   - Add field to SOQL queries
   - Update DML operations if needed
   - Run tests to verify

### Modifying Quick Actions

1. **For button label changes:**
   - Edit `<label>` in Quick Action metadata XML
   - Redeploy: `sf project deploy start --metadata "QuickAction:Quote.MyAction"`

2. **For functionality changes:**
   - Modify LWC JavaScript (quoteRenewalProductReplacer.js)
   - Test locally if possible
   - Deploy: `sf project deploy start --metadata "LightningComponentBundle:quoteRenewalProductReplacer"`
   - Clear browser cache and test

3. **For new Quick Actions:**
   - Create Quick Action XML in `force-app/main/default/quickActions/`
   - Create or reuse LWC component
   - Deploy both: Quick Action and LWC
   - Retrieve layout, add to `platformActionList`, redeploy layout

### Updating Product Replacement Logic

1. **Modify Apex class:**
   - Edit `QuoteRenewalProductReplacer.cls`
   - Ensure `@AuraEnabled` annotations remain
   - Update tests in `QuoteRenewalProductReplacerTest.cls`

2. **Run tests:**
   ```bash
   sf apex run test --tests QuoteRenewalProductReplacerTest --target-org orgfarmorg --result-format human
   ```

3. **Deploy:**
   ```bash
   sf project deploy start --metadata "ApexClass:QuoteRenewalProductReplacer,ApexClass:QuoteRenewalProductReplacerTest" --target-org orgfarmorg
   ```

4. **Test in UI:**
   - Create test renewal quote: `cd data/test_renewal && python create_renewal.py --org orgfarmorg --renew-asset <id>`
   - Navigate to renewal quote
   - Click Quick Action button
   - Verify behavior

### Adding New Test Data

1. **For new products:**
   - Add to `data/test_products/` directory
   - Update or create new import script
   - Include PricebookEntry and ProductSellingModelOption
   - Document in README

2. **For new accounts:**
   - Add to `data/test_accounts/` directory
   - Make import script idempotent (check if exists first)

3. **For new quotes:**
   - Use existing `import_quote.py` with parameters
   - Or create new script in `data/test_quotes/`
   - Ensure dependencies (Account, Product) exist first

### Updating README Files

**After major changes, update:**
1. `README.md` - Main project overview
2. `CLAUDE.md` - This file (development guidance)
3. `DEPLOYMENT.md` - Deployment instructions
4. `data/*/README.md` - Relevant data directory READMEs

**Use this pattern:**
- Main README: User-facing, high-level workflows
- CLAUDE.md: Developer-facing, technical details and patterns
- DEPLOYMENT.md: Step-by-step deployment and troubleshooting
- Data READMEs: Script usage and data structure

## Session History Lessons Learned

**From this coding session, future Claude instances should know:**

1. **Quick Actions require specific metadata structure**
   - Spent significant time debugging incorrect metadata format
   - Final working structure is documented in "Common Development Patterns" above
   - Always use `type: LightningWebComponent`, not `LightningComponent`

2. **LWC Quick Actions need @api invoke() method**
   - Initial error: "t.invoke is not a function"
   - Solution documented in Architecture section
   - This is non-obvious and not well-documented by Salesforce

3. **Page layout Quick Actions go in platformActionList**
   - Initially tried adding to `quickActionList` (wrong)
   - User manually corrected to `platformActionList`
   - This distinction is critical but subtle

4. **QuoteLineItem.Product2Id is not updateable**
   - Must use DELETE old + INSERT new pattern
   - This is documented in "Working with QuoteLineItem" section
   - Critical constraint for product replacement feature

5. **@AuraEnabled required on ALL return type properties**
   - Initially forgot this on inner classes
   - Added comprehensive documentation in "Working with Apex and LWC Integration"
   - Silent failure mode makes this hard to debug

6. **API version consistency matters**
   - Updated all Apex classes from 62.0 to 67.0
   - Must update meta.xml files, not just class files
   - Documented in "API Version Consistency" section

7. **Deployment order matters**
   - Apex → LWC → Quick Actions → Layouts
   - Dependencies must be deployed first
   - Documented in "Working with Salesforce Metadata"

8. **User feedback loop is critical**
   - User manually fixed layout after initial approach failed
   - Retrieved user's working version and learned correct pattern
   - Always retrieve metadata after user makes manual changes to understand correct approach

9. **Test data workflow is complete**
   - Full end-to-end: Account → Product → Quote → Order → Asset → Renewal Quote
   - `create_renewal.py` script uses standard Salesforce API
   - Documented in test_renewal/README.md

10. **Manual page refresh needed after LWC changes**
    - User modified code to NOT auto-refresh page
    - Toast message now tells user to refresh manually
    - Better UX than unexpected page reload

