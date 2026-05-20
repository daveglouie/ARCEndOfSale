# Decision Table Scripts

This directory contains Python scripts for managing Salesforce Decision Tables.

## Scripts

### `refresh_decision_table_standalone.py`

Standalone script to refresh Salesforce Decision Tables without requiring CumulusCI.

**Usage:**
```bash
python refresh_decision_table_standalone.py --org orgfarmorg --tables DecisionTableName
```

**Features:**
- Refresh single or multiple decision tables
- Support for full and incremental refresh
- Load table names from file
- Detailed error reporting
- No CumulusCI dependency

**Requirements:**
- Python 3.6+
- Salesforce CLI (sf) authenticated
- `requests` library: `pip install requests`

See `../../docs/decision-tables-guide.md` for complete documentation.

### `refresh_decision_table.py`

CumulusCI-based task for refreshing decision tables within CumulusCI workflows.

**Usage:**
```bash
cci task run refresh_decision_table --org beta -o developerNames "Table1,Table2"
```

**Requirements:**
- CumulusCI installed
- Project configured in `cumulusci.yml`

**Note:** This script is copied from the RLMBaseDev project and requires CumulusCI infrastructure.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install requests
   ```

2. **Authenticate with Salesforce:**
   ```bash
   sf org login web --alias orgfarmorg
   ```

3. **Refresh a decision table:**
   ```bash
   python refresh_decision_table_standalone.py --org orgfarmorg --tables MyDecisionTable
   ```

## Common Use Cases

### After Product Data Load
```bash
python refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables "RLM_ProductQualification,RLM_ProductCategoryQualification"
```

### After Pricing Changes
```bash
python refresh_decision_table_standalone.py \
  --org orgfarmorg \
  --tables "Price_Book_Entry_V2,Attribute_Based_Adjustment_Decision_Table" \
  --incremental
```

### Batch Refresh from File
```bash
# Create list of tables
cat > tables.txt <<EOF
Asset_Action_Source_Entries_Decision_Table_V2
Asset_Rate_Card_Entry_Resolution_V2
Asset_Rate_Decision_Table_V2
EOF

# Refresh all
python refresh_decision_table_standalone.py --org orgfarmorg --tables-file tables.txt
```

## Documentation

- **Full Guide:** `../../docs/decision-tables-guide.md`
- **Skill Definition:** `../../.cursor/skills/decision-tables.md`
- **CLAUDE.md:** See Development Commands > Decision Table Refresh

## Troubleshooting

**Import Error: No module named 'requests'**
```bash
pip install requests
```

**Authentication Error**
```bash
sf org display --target-org orgfarmorg
# If expired, re-authenticate:
sf org login web --alias orgfarmorg
```

**Decision Table Not Found**
```bash
# List all active tables
sf data query \
  --query "SELECT DeveloperName FROM DecisionTable WHERE Status = 'Active'" \
  --target-org orgfarmorg
```

## Contributing

When adding new decision table scripts:
1. Follow the existing pattern in `refresh_decision_table_standalone.py`
2. Update this README
3. Update `docs/decision-tables-guide.md`
4. Update `.cursor/skills/decision-tables.md`
