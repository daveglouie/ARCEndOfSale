# Decision Table Refresh Skill

Use this skill when the user needs to refresh Salesforce Decision Tables. Decision Tables are Business Rules Engine (BRE) objects that cache data for Revenue Cloud features.

## When to Use This Skill

Trigger this skill when the user mentions:
- "refresh decision table"
- "refresh decision tables" 
- "update decision table"
- "decision table is stale"
- "decision table needs refresh"
- "DT refresh"
- "pricing/rating not working" (after data changes)

## Quick Reference

### Refresh a Single Table
```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables DecisionTableName
```

### Refresh Multiple Tables
```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables "Table1,Table2,Table3"
```

### Incremental Refresh
```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables DecisionTableName \
  --incremental
```

### Load from File
```bash
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables-file config/decision_tables.txt
```

## Finding Decision Table Names

```bash
# List all active decision tables
sf data query \
  --query "SELECT DeveloperName, MasterLabel, Status FROM DecisionTable WHERE Status = 'Active'" \
  --target-org orgfarmorg
```

## Common Decision Table Categories

### Pricing Tables
- `Attribute_Based_Adjustment_Decision_Table`
- `Bundle_Based_Adjustment_Decision_Table`
- `Price_Book_Entry_V2`
- `Price_Book_Entry_For_Unit_Price_V2`

### Rating Tables
- `Asset_Action_Source_Entries_Decision_Table_V2`
- `Asset_Rate_Card_Entry_Resolution_V2`
- `Asset_Rate_Decision_Table_V2`

### Product Qualification
- `RLM_ProductQualification`
- `RLM_ProductCategoryQualification`
- `RLM_CostBookEntries`

## When to Refresh

Refresh decision tables after:
1. Product data changes (adds, updates, attribute changes)
2. Pricing changes (price books, price adjustments)
3. Rate card changes (rate schedules, usage resources)
4. Bulk data loads (SFDMU, CSV imports)
5. Initial org setup or sandbox refresh

## Refresh Types

- **Full Refresh** (default): Rebuilds entire table from scratch
  - Use after: Major changes, initial setup, data migrations
  - Slower but guaranteed consistency

- **Incremental Refresh** (`--incremental`): Updates only changed records
  - Use after: Minor routine updates
  - Faster but requires table to be in good state

## Script Details

**Location**: `scripts/decision_tables/refresh_decision_table_standalone.py`

**Requirements**:
- Python 3.6+
- Salesforce CLI (sf) authenticated to target org
- `requests` library: `pip install requests`
- User permission: "Manage Decision Tables"

**Options**:
- `--org`: Salesforce org alias (required)
- `--tables`: Comma-separated table names (one of --tables or --tables-file required)
- `--tables-file`: Path to file with table names (one of --tables or --tables-file required)
- `--incremental`: Perform incremental vs full refresh (optional)
- `--api-version`: Salesforce API version, default 62.0 (optional)

## Full Documentation

See `docs/decision-tables-guide.md` for:
- Detailed troubleshooting
- Advanced usage examples
- Integration with CI/CD
- API documentation
- Monitoring refresh status

## Example Workflow

```bash
# 1. Find decision tables that need refresh
sf data query \
  --query "SELECT DeveloperName FROM DecisionTable WHERE Status = 'Active' AND UsageType = 'DefaultPricing'" \
  --target-org orgfarmorg

# 2. Create a file with the table names
cat > pricing_tables.txt <<EOF
Attribute_Based_Adjustment_Decision_Table
Bundle_Based_Adjustment_Decision_Table
Price_Book_Entry_V2
EOF

# 3. Refresh all tables from the file
python scripts/decision_tables/refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables-file pricing_tables.txt

# 4. Verify refresh (check logs or test pricing)
```

## Troubleshooting

**"The requested resource does not exist"**
- Decision table name is wrong
- Verify with: `sf data query --query "SELECT DeveloperName FROM DecisionTable WHERE DeveloperName LIKE '%TableName%'" --target-org orgfarmorg`

**"Decision Table refresh failed"**
- Data integrity issues
- Try full refresh instead of incremental
- Check decision table in Setup UI for errors

**Script fails with authentication error**
- Verify SF CLI auth: `sf org display --target-org orgfarmorg`
- Re-authenticate if needed: `sf org login web --alias orgfarmorg`

## Notes for Claude

When helping users refresh decision tables:

1. **Always ask which org** - The script requires `--org` parameter
2. **Suggest appropriate refresh type** - Full for major changes, incremental for minor
3. **Provide table names** - Help user query for decision table names if unknown
4. **Explain context** - Tell user why refresh is needed after their data changes
5. **Show verification** - Suggest how to verify refresh completed successfully
6. **Handle errors gracefully** - Walk through troubleshooting if refresh fails

Common scenarios:
- After deploying new products → Refresh product qualification tables
- After price book changes → Refresh pricing decision tables  
- After rate card updates → Refresh rating decision tables
- After bulk data load → Refresh all relevant tables

Always reference the full guide in `docs/decision-tables-guide.md` for complex scenarios.
