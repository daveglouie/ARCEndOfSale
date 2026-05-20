# Deployment Guide: End of Sale Product Replacement

## Overview

This package contains metadata for deploying the End of Sale product replacement feature, including:
- Custom `RenewalReplacementProduct__c` field on Product2
- Apex classes for renewal detection and product replacement
- Lightning Web Component for user interface
- Quick Actions on Quote pages
- Automatic quote repricing after replacement

## What's Included

### 1. Custom Field
- **API Name**: `Product2.RenewalReplacementProduct__c`
- **Label**: Renewal Replacement Product
- **Type**: Lookup to Product2
- **Description**: Lookup to the Product that should be used when renewing this product. Used for End of Sale scenarios where a product is being replaced.
- **Relationship Name**: RenewalReplacementProducts
- **Delete Constraint**: SetNull

### 2. Apex Classes (API Version 67.0)
- **QuoteRenewalChecker**: Detects renewal quotes based on `OriginalActionType` field
- **QuoteRenewalProductReplacer**: Replaces products on renewal quotes
- **RepriceQuotesPST**: Reprices quotes using PST API
- **Test Classes**: Complete test coverage for all classes

### 3. Lightning Web Component
- **quoteRenewalProductReplacer**: User interface for product replacement
  - Implements `@api invoke()` method for Quick Action support
  - Displays toast notifications for success/error states
  - Calls Apex methods with proper error handling

### 4. Quick Actions
- **Quote.Check_Renewal_Replacement_Products**: Quick Action on Quote pages
- **Quote.Replace_Renewal_Products**: Alternative Quick Action with different label
- Both invoke the same LWC component

### 5. Page Layouts Modified
1. **Product2-Product Layout**
   - Added field to Product Information section (right column)

2. **Product2-RLM Product Layout**
   - Added field to Product Information section (right column)

3. **Quote-RLM Quote Layout**
   - Added Quick Actions to platformActionList
   - "Check Renewal Replacement Products" button
   - "Replace Renewal Products" button

**Note**: The related list for products that reference this product (`RenewalReplacementProducts__r`) must be added manually through the UI due to Salesforce limitations with self-lookup related lists in metadata. See "Post-Deployment Steps" below for instructions.

### 6. Profiles
- **Admin Profile**: Field permissions set to editable and readable

## Deployment Instructions

### Option 1: Deploy to Org (Recommended)
```bash
# Deploy all metadata
sf project deploy start --target-org orgfarmorg

# Or deploy specific metadata
sf project deploy start --target-org orgfarmorg --manifest manifest/package.xml
```

### Option 2: Deploy Using Manifest
```bash
sf project deploy start --target-org orgfarmorg --manifest manifest/package.xml
```

### Option 3: Deploy Individual Components
```bash
# Deploy the custom field
sf project deploy start --target-org orgfarmorg --metadata CustomField:Product2.RenewalReplacementProduct__c

# Deploy Apex classes
sf project deploy start --target-org orgfarmorg --metadata "ApexClass:QuoteRenewalChecker,ApexClass:QuoteRenewalProductReplacer,ApexClass:RepriceQuotesPST"

# Deploy Lightning Web Component
sf project deploy start --target-org orgfarmorg --metadata "LightningComponentBundle:quoteRenewalProductReplacer"

# Deploy Quick Actions
sf project deploy start --target-org orgfarmorg --metadata "QuickAction:Quote.Check_Renewal_Replacement_Products,QuickAction:Quote.Replace_Renewal_Products"

# Deploy the layouts
sf project deploy start --target-org orgfarmorg --metadata "Layout:Product2-Product Layout,Layout:Product2-RLM Product Layout,Layout:Quote-RLM Quote Layout"

# Deploy profile permissions
sf project deploy start --target-org orgfarmorg --metadata "Profile:Admin"
```

## Post-Deployment Steps

1. **Verify Field Visibility**
   - Navigate to Setup > Object Manager > Product2 > Fields & Relationships
   - Confirm `RenewalReplacementProduct__c` field exists

2. **Check Page Layouts**
   - Navigate to Setup > Object Manager > Product2 > Page Layouts
   - Open each layout and verify the field appears in the Product Information section

3. **Add Related List (Manual Step Required)**
   - Due to Salesforce limitations with self-lookup relationships in metadata, the related list must be added manually
   - Navigate to Setup > Object Manager > Product2 > Page Layouts
   - For each layout (Product Layout, RLM Product Layout):
     - Click Edit
     - Scroll to the Related Lists section
     - Find "Products (Renewal Replacement Product)" or "RenewalReplacementProducts__r" in the available list
     - Drag it onto the layout
     - Configure the columns to show: Name, Family, Product Code
     - Click Save

4. **Verify Profile Permissions**
   - Navigate to Setup > Users > Profiles
   - For each profile, verify field-level security is enabled for `RenewalReplacementProduct__c`

5. **Test the Field**
   - Navigate to any Product2 record
   - Edit the record and verify the "Renewal Replacement Product" lookup field is available
   - Save a test value and verify the related list appears on the referenced product

6. **Verify Quick Actions on Quote Pages**
   - Navigate to a Quote record page
   - Verify "Check Renewal Replacement Products" and "Replace Renewal Products" buttons appear
   - If buttons don't appear, check:
     - Quick Actions are deployed
     - Quote page layout includes the Quick Actions in platformActionList
     - User has permission to execute Lightning Web Components

7. **Test the Quick Actions**
   - Create a renewal quote (see test_renewal documentation)
   - Click "Replace Renewal Products" button
   - Verify success toast message appears
   - Refresh the page and verify products were replaced

8. **Run Apex Tests**
   ```bash
   sf apex run test --test-level RunLocalTests --target-org orgfarmorg
   ```
   - Verify all tests pass with sufficient code coverage

## Additional Profile Configuration

The provided deployment only includes the Admin profile. To add this field to other profiles:

### Manual Method
1. Setup > Users > Profiles > [Profile Name]
2. Field-Level Security > Product2
3. Find `Renewal Replacement Product` and set to `Visible` and `Editable`

### Metadata Method
Create additional profile metadata files in `force-app/main/default/profiles/` following the pattern in `Admin.profile-meta.xml`, then deploy:
```bash
sf project deploy start --target-org orgfarmorg --metadata "Profile:YourProfileName"
```

## Rollback Instructions

To remove this field:
```bash
# Delete the custom field (this will also remove it from layouts and profiles)
sf project delete source --target-org orgfarmorg --metadata CustomField:Product2.RenewalReplacementProduct__c
```

**Warning**: Deleting the field will permanently delete all data stored in it. Backup data first if needed.

## File Structure

```
force-app/main/default/
├── classes/                           # Apex classes
│   ├── QuoteRenewalChecker.cls
│   ├── QuoteRenewalChecker.cls-meta.xml
│   ├── QuoteRenewalCheckerTest.cls
│   ├── QuoteRenewalCheckerTest.cls-meta.xml
│   ├── QuoteRenewalProductReplacer.cls
│   ├── QuoteRenewalProductReplacer.cls-meta.xml
│   ├── QuoteRenewalProductReplacerTest.cls
│   ├── QuoteRenewalProductReplacerTest.cls-meta.xml
│   ├── RepriceQuotesPST.cls
│   └── RepriceQuotesPST.cls-meta.xml
├── lwc/                               # Lightning Web Components
│   └── quoteRenewalProductReplacer/
│       ├── quoteRenewalProductReplacer.js
│       ├── quoteRenewalProductReplacer.html
│       └── quoteRenewalProductReplacer.js-meta.xml
├── quickActions/                      # Quick Actions
│   ├── Quote.Check_Renewal_Replacement_Products.quickAction-meta.xml
│   └── Quote.Replace_Renewal_Products.quickAction-meta.xml
├── objects/Product2/
│   └── fields/
│       └── RenewalReplacementProduct__c.field-meta.xml
├── layouts/
│   ├── Product2-Product Layout.layout-meta.xml
│   ├── Product2-RLM Product Layout.layout-meta.xml
│   └── Quote-RLM Quote Layout.layout-meta.xml
└── profiles/
    └── Admin.profile-meta.xml

manifest/
└── package.xml
```

## Validation Before Deployment

Run validation to check for errors without deploying:
```bash
sf project deploy validate --target-org orgfarmorg --manifest manifest/package.xml
```

## Troubleshooting

### Issue: "Field does not exist on Layout"
- Ensure the field is deployed before the layout
- Deploy in this order: Field → Profiles → Layouts

### Issue: "Insufficient Privileges"
- Verify you have Customize Application permission
- Check that the target org allows custom fields on Product2

### Issue: "Related List not showing"
- Verify the relationship name `RenewalReplacementProducts__r` matches the field's relationshipName
- Check that there are related records that reference the current product

### Issue: "Quick Actions not appearing on Quote page"
- Verify Quick Actions are deployed: `sf project retrieve start --target-org orgfarmorg --metadata "QuickAction:Quote.*"`
- Check Quote page layout includes Quick Actions in platformActionList
- Verify LWC component is deployed: `sf project retrieve start --target-org orgfarmorg --metadata "LightningComponentBundle:quoteRenewalProductReplacer"`
- Clear browser cache and refresh

### Issue: "Quick Action button does nothing"
- Open browser Developer Console (F12) and check for JavaScript errors
- Verify the LWC implements `@api invoke()` method
- Check that Apex method `QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote` has `@AuraEnabled` annotation
- Verify result classes have `@AuraEnabled` on all public properties

### Issue: "Product replacement fails silently"
- Check if the quote is actually a renewal quote (`OriginalActionType = 'Renew'`)
- Verify replacement product exists and has active pricebook entry
- Check Apex debug logs for detailed error messages
- Ensure user has permission to delete and create QuoteLineItems

### Issue: "Tests failing after deployment"
- Run tests individually to identify failing test:
  ```bash
  sf apex run test --tests QuoteRenewalCheckerTest --target-org orgfarmorg
  sf apex run test --tests QuoteRenewalProductReplacerTest --target-org orgfarmorg
  ```
- Check that test data setup is correct
- Verify API version compatibility (should be 67.0)
