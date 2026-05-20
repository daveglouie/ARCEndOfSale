# Test Account Data

This directory contains test account data for creating demo/test accounts in Salesforce orgs.

## Labubu Industries Account

A test account for End of Sale and renewal testing scenarios.

**Account Details:**
- **Name:** Labubu Industries

## Usage

### Import with Duplicate Check (Recommended)

Use the Python script to automatically check if the account exists before creating it:

```bash
cd data/test_accounts
python import_account.py --org orgfarmorg
```

This script:
1. Queries for an existing account named "Labubu Industries"
2. If found, reports the existing Account ID and exits
3. If not found, creates the account using the data tree plan
4. Reports the newly created Account ID

**Output when account exists:**
```
Checking if 'Labubu Industries' account already exists in org 'orgfarmorg'...
✓ Account 'Labubu Industries' already exists with ID: 001XXXXXXXXXX
  No action taken.
```

**Output when account doesn't exist:**
```
Checking if 'Labubu Industries' account already exists in org 'orgfarmorg'...
✗ Account does not exist. Creating...
✓ Successfully created account 'Labubu Industries' with ID: 001XXXXXXXXXX
```

### Import Manually (No Duplicate Check)

Import without checking for duplicates:

```bash
cd data/test_accounts
sf data import tree --files Account.json --target-org orgfarmorg
```

**Note:** Manual import will fail if the account already exists and there's a duplicate rule.

### Delete Test Account

```bash
# Delete by Account Name
sf data delete record --sobject Account --where "Name='Labubu Industries'" --target-org orgfarmorg
```

## File Structure

```
data/test_accounts/
├── README.md           # This file
├── import_account.py   # Python script with duplicate checking
└── Account.json        # Account record data
```

## Querying the Account

```bash
# Find the account
sf data query \
  --query "SELECT Id, Name, CreatedDate FROM Account WHERE Name='Labubu Industries'" \
  --target-org orgfarmorg
```

## Adding Related Data

To extend this with related records (Contacts, Opportunities, etc.), create additional JSON files and reference the account:

**Example: Contact.json**
```json
{
  "records": [
    {
      "attributes": {
        "type": "Contact",
        "referenceId": "ContactRef1"
      },
      "FirstName": "John",
      "LastName": "Doe",
      "AccountId": "@AccountRef1"
    }
  ]
}
```

Then update the import script to use a data tree plan that includes both files in the correct order.

## Notes

- The Python script uses `sf data query` with `--json` output for parsing
- Duplicate checking is based on exact Account Name match
- The script exits with status 0 whether the account exists or is created
- For production orgs, consider using External IDs for idempotent imports
