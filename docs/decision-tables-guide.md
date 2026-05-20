# Decision Table Refresh Guide

This guide explains how to refresh Salesforce Decision Tables in this project. Decision Tables are Business Rules Engine (BRE) objects that store decision logic for Revenue Cloud features like pricing, rating, and qualification rules.

## What is Decision Table Refresh?

Decision Tables in Salesforce cache data from related objects (Products, Price Books, etc.) for performance. When source data changes, the decision table must be **refreshed** to pick up those changes.

### Types of Refresh

1. **Full Refresh** - Rebuilds the entire decision table from scratch
   - Use when: Major data changes, initial setup, or structural changes
   - Slower but guaranteed to be in sync

2. **Incremental Refresh** - Updates only changed records since last refresh
   - Use when: Minor data updates, routine maintenance
   - Faster but requires decision table to already be in good state

## Quick Start

### Refresh a Single Decision Table

```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables Asset_Action_Source_Entries_Decision_Table_V2
```

### Refresh Multiple Decision Tables

```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables "Table1,Table2,Table3"
```

### Incremental Refresh

```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables MyDecisionTable \
  --incremental
```

### Load from File

Create a file with decision table names (one per line):

```
# decision_tables.txt
Asset_Action_Source_Entries_Decision_Table_V2
Asset_Rate_Card_Entry_Resolution_V2
Asset_Rate_Decision_Table_V2
```

Then refresh:

```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables-file decision_tables.txt
```

## Script Options

| Option | Required | Description |
|--------|----------|-------------|
| `--org` | Yes | Salesforce org alias (SF CLI alias, e.g., `orgfarmorg`) |
| `--tables` | * | Comma-separated decision table API names |
| `--tables-file` | * | Path to file with decision table names |
| `--incremental` | No | Perform incremental refresh (default: full refresh) |
| `--api-version` | No | Salesforce API version (default: 62.0) |

*Either `--tables` or `--tables-file` must be provided

## Common Decision Tables

### Pricing Decision Tables
```
Attribute_Based_Adjustment_Decision_Table
Bundle_Based_Adjustment_Decision_Table
Price_Book_Entry_For_Unit_Price_V2
Price_Book_Entry_V2
```

### Rating Decision Tables
```
Asset_Action_Source_Entries_Decision_Table_V2
Asset_Rate_Card_Entry_Resolution_V2
Asset_Rate_Decision_Table_V2
```

### Product Qualification
```
RLM_ProductQualification
RLM_ProductCategoryQualification
RLM_CostBookEntries
```

## Finding Decision Table Names

### Method 1: Query via SOQL

```bash
sf data query \
  --query "SELECT Id, DeveloperName, MasterLabel, Status FROM DecisionTable WHERE Status = 'Active'" \
  --target-org orgfarmorg
```

### Method 2: Setup UI

1. Navigate to **Setup > Business Rules Engine > Decision Tables**
2. View the list of decision tables
3. Click on a table to see its **API Name** (DeveloperName)

### Method 3: Via Script (list all active)

```bash
# Use the query to get JSON output
sf data query \
  --query "SELECT DeveloperName FROM DecisionTable WHERE Status = 'Active'" \
  --target-org orgfarmorg \
  --json | jq -r '.result.records[].DeveloperName'
```

## When to Refresh Decision Tables

Refresh decision tables after:

1. **Product Changes**
   - Adding/modifying products
   - Changing product attributes
   - Updating product categories

2. **Pricing Changes**
   - Adding/updating price book entries
   - Modifying price adjustments
   - Changing pricing rules

3. **Rate Card Changes**
   - Updating rate cards
   - Modifying rate schedules
   - Changing usage resources

4. **Data Loads**
   - After bulk data imports
   - After SFDMU data plan execution
   - After CSV uploads

5. **Initial Setup**
   - After deploying decision table metadata
   - After org provisioning
   - After cloning/refreshing a sandbox

## Troubleshooting

### Error: "The requested resource does not exist"

**Cause**: Decision table name is incorrect or table doesn't exist

**Solution**: Verify the table name with SOQL query:
```bash
sf data query \
  --query "SELECT DeveloperName FROM DecisionTable WHERE DeveloperName LIKE '%YourTableName%'" \
  --target-org orgfarmorg
```

### Error: "No response received for Decision Table"

**Cause**: API timeout or connectivity issue

**Solution**: 
1. Check org connectivity: `sf org open --target-org orgfarmorg`
2. Try again with a single table first
3. Check Salesforce system status

### Error: "Decision Table refresh failed"

**Cause**: Data integrity issues or missing required fields

**Solution**:
1. Check decision table status in Setup UI
2. Review decision table error logs
3. Try a full refresh instead of incremental
4. Verify source data integrity

### Script exits with "sf: command not found"

**Cause**: Salesforce CLI not installed or not in PATH

**Solution**: Install SF CLI:
```bash
npm install -g @salesforce/cli
```

## Advanced Usage

### Batch Refresh Script

Create a shell script to refresh all pricing tables:

```bash
#!/bin/bash
# refresh_all_pricing.sh

python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables "Attribute_Based_Adjustment_Decision_Table,Bundle_Based_Adjustment_Decision_Table,Price_Book_Entry_V2" \
  && echo "✓ All pricing tables refreshed"
```

Make it executable:
```bash
chmod +x refresh_all_pricing.sh
./refresh_all_pricing.sh
```

### Integration with CI/CD

Add to your deployment script after data loads:

```yaml
# Example GitHub Actions workflow
- name: Deploy Data
  run: |
    sf data import tree --plan data/plan.json --target-org ${{ secrets.ORG_ALIAS }}

- name: Refresh Decision Tables
  run: |
    python scripts/decision_tables/refresh_decision_table_standalone.py \
      --org ${{ secrets.ORG_ALIAS }} \
      --tables-file config/decision_tables.txt
```

### Monitoring Refresh Status

Query decision table refresh history:

```bash
sf data query \
  --query "SELECT DecisionTableName, Status, RefreshType, StartTime, EndTime FROM DecisionTableRefreshLog ORDER BY StartTime DESC LIMIT 10" \
  --target-org orgfarmorg
```

## Requirements

- **Python 3.6+**
- **Salesforce CLI** (sf) installed and authenticated
- **requests** library: `pip install requests`
- **Org access**: User must have "Manage Decision Tables" permission

## Script Location

- **Standalone script**: `scripts/decision_tables/refresh_decision_table_standalone.py`
- **CumulusCI version**: `scripts/decision_tables/refresh_decision_table.py` (requires CumulusCI)

## API Documentation

This script uses the Salesforce REST API:
- Endpoint: `/services/data/v{version}/actions/standard/refreshDecisionTable`
- Method: POST
- Docs: [Salesforce Decision Table API](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_ConnectApi_DecisionTable.htm)

## Support

For issues or questions:
1. Check this guide and troubleshooting section
2. Review Salesforce Decision Table documentation
3. Check logs for detailed error messages
4. Verify org permissions and connectivity
