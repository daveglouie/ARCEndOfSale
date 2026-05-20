# Test Renewal Data

This directory contains scripts for finding assets and creating renewal quotes for testing purposes.

## create_renewal.py

A script that finds assets matching specific criteria and creates renewal quotes from those assets.

### Features

- **Find Assets**: Dynamically looks up assets by Product and Account (no hardcoded IDs)
- **Create Renewal Quotes**: Uses the Salesforce `initiateRenewal` standard action to create renewal quotes from assets
- **Full API Integration**: Uses the Salesforce REST API v67.0

### Usage

#### Find Assets

Find assets where:
- Product: "Enterprise Campaign Manager (Legacy)"
- Account: "Labubu Industries"

```bash
cd data/test_renewal
python create_renewal.py --org orgfarmorg
```

**Output:**
```
============================================================
Find Assets for Renewal Testing
============================================================
Org: orgfarmorg
Product: Enterprise Campaign Manager (Legacy)
Account: Labubu Industries
============================================================

→ Looking up Account ID for 'Labubu Industries'...
✓ Found Account: Labubu Industries (001XXXXXXXXXXXX)

→ Looking up Product ID for 'Enterprise Campaign Manager (Legacy)'...
✓ Found Product: Enterprise Campaign Manager (Legacy) (Code: ECM-LEGACY, ID: 01tXXXXXXXXXXXX)

→ Searching for Assets where Product2Id='...' AND AccountId='...'...
✓ Found 1 asset(s)

========================================================================================================================
Assets for Product: Enterprise Campaign Manager (Legacy) (ECM-LEGACY)
Account: Labubu Industries
========================================================================================================================

Asset ID             Asset Name                               Status          Qty      MRR          Lifecycle Mgmt
------------------------------------------------------------------------------------------------------------------------
02iXXXXXXXXXXXX      Enterprise Campaign Manager (Legacy)     Active          15       $1500.00     Yes
------------------------------------------------------------------------------------------------------------------------

Total Assets: 1

Lifecycle Details:

Asset: Enterprise Campaign Manager (Legacy) (02iXXXXXXXXXXXX)
  Start Date: 2026-05-20T00:00:00.000+0000
  End Date: 2027-05-19T23:59:59.000+0000
  Has Lifecycle Management: True

============================================================
✓ Asset search completed successfully!
============================================================

To create a renewal quote from the first asset, run:
  python create_renewal.py --org orgfarmorg --renew-asset 02iXXXXXXXXXXXX
```

#### Create Renewal Quote

Create a renewal quote from a specific asset:

```bash
cd data/test_renewal
python create_renewal.py --org orgfarmorg --renew-asset 02iVW000000bkzxYAA
```

**Output:**
```
============================================================
Find Assets for Renewal Testing
============================================================
Org: orgfarmorg
Asset ID to Renew: 02iVW000000bkzxYAA
============================================================

→ Creating renewal quote for asset 02iVW000000bkzxYAA...
  Instance URL: https://...
  Calling: POST .../services/data/v67.0/actions/standard/initiateRenewal
  Payload: {
  "inputs": [
    {
      "renewAssetIds": [
        "02iVW000000bkzxYAA"
      ],
      "renewOutputType": "Quote"
    }
  ]
}
✓ Renew Assets action completed

API Response:
[
  {
    "actionName": "initiateRenewal",
    "errors": null,
    "invocationId": null,
    "isSuccess": true,
    "outcome": null,
    "outputValues": {
      "renewRecordId": "0Q0XXXXXXXXXXXX"
    },
    "sortOrder": -1,
    "version": 1
  }
]

✓ Renewal Quote ID: 0Q0XXXXXXXXXXXX

============================================================
✓ Renewal completed successfully!
============================================================

Verify the renewal quote:
  sf data query --query "SELECT Id, Name, Status, AccountId FROM Quote WHERE Id='0Q0XXXXXXXXXXXX'" --target-org orgfarmorg
```

## How It Works

### Dynamic ID Lookups

The script uses SOQL queries to dynamically look up all required IDs:

1. **Account ID**: Queries for account by name "Labubu Industries"
2. **Product ID**: Queries for product by name "Enterprise Campaign Manager (Legacy)"
3. **Asset IDs**: Queries for assets matching the account and product

No IDs are hardcoded, making the script portable across different Salesforce orgs.

### Renewal API

The script uses the Salesforce standard action `initiateRenewal`:

**Endpoint**: `/services/data/v67.0/actions/standard/initiateRenewal`

**Request Body**:
```json
{
  "inputs": [
    {
      "renewAssetIds": ["<asset-id>"],
      "renewOutputType": "Quote"
    }
  ]
}
```

**Response**:
```json
[
  {
    "actionName": "initiateRenewal",
    "isSuccess": true,
    "outputValues": {
      "renewRecordId": "<quote-id>"
    }
  }
]
```

## Prerequisites

The script requires:

1. **Python 3.6+**
2. **requests library**: `pip install requests`
3. **Salesforce CLI**: `sf` command must be available
4. **Authenticated Org**: Org must be authenticated via `sf org login`

### Required Salesforce Data

To find assets, you need:

1. **Account "Labubu Industries"**
   ```bash
   cd ../test_accounts
   python import_account.py --org orgfarmorg
   ```

2. **Product "Enterprise Campaign Manager (Legacy)"**
   ```bash
   cd ../test_products
   python import_with_replacement_product.py --org orgfarmorg
   ```

3. **Assets created from orders**
   ```bash
   cd ../test_quotes
   python import_quote.py --org orgfarmorg
   ```
   (Assets are created when orders are activated)

## API Documentation

- **Renew Assets Action**: https://developer.salesforce.com/docs/atlas.en-us.revenue_lifecycle_management_dev_guide.meta/revenue_lifecycle_management_dev_guide/actions_obj_renew_assets.htm
- **Salesforce Standard Actions**: https://developer.salesforce.com/docs/atlas.en-us.api_action.meta/api_action/

## Troubleshooting

**Error: "Account 'Labubu Industries' not found"**
- Create the account first: `cd ../test_accounts && python import_account.py --org orgfarmorg`

**Error: "Product 'Enterprise Campaign Manager (Legacy)' not found"**
- Create the product first: `cd ../test_products && python import_with_replacement_product.py --org orgfarmorg`

**Error: "No assets found"**
- Assets are created when orders are activated
- Run: `cd ../test_quotes && python import_quote.py --org orgfarmorg`

**Error: "requests library not installed"**
- Install it: `pip install requests`

**Error: HTTP 404 on API call**
- Ensure you're using API version v67.0
- Verify the org has Revenue Lifecycle Management enabled
- Check that the action name is `initiateRenewal`
