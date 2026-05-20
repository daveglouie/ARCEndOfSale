# Salesforce Object Descriptions Summary

## Files Created
- `Asset_describe.json` (206KB)
- `AssetStatePeriod_describe.json` (59KB)
- `AssetAction_describe.json` (82KB)
- `AssetActionSource_describe.json` (91KB)
- `AppUsageAssignment_describe.json` (21KB)

## Object Overview

### 1. Asset
- **Label:** Asset
- **API Name:** Asset
- **Fields:** 76 fields
- **Child Relationships:** 192
- **Key Fields:**
  - Id, Name, Status, CurrentMrr, CurrentQuantity
  - Product2Id, ProductCode, ProductFamily
  - AccountId, ContactId, OwnerId
  - LifecycleStartDate, LifecycleEndDate
  - HasLifecycleManagement, DoesAutomaticallyRenew

### 2. Asset State Period
- **Label:** Asset State Period
- **API Name:** AssetStatePeriod
- **Fields:** 28 fields
- **Child Relationships:** 12
- **Key Fields:**
  - Id, AssetStatePeriodNumber
  - AssetId (parent reference)
  - StartDate, EndDate
  - Quantity, Amount, Mrr
  - SegmentIdentifier, SegmentType, SegmentName

### 3. Asset Action
- **Label:** Asset Action
- **API Name:** AssetAction
- **Fields:** 39 fields
- **Child Relationships:** 12
- **Key Fields:**
  - Id, AssetActionNumber
  - AssetId (parent reference)
  - Type, CategoryEnum, Subtype
  - ActionDate
  - MrrChange, QuantityChange
  - ProductAmountChange, SubtotalChange
  - TotalAmount, TotalQuantity, TotalMrr

### 4. Asset Action Source
- **Label:** Asset Action Source
- **API Name:** AssetActionSource
- **Fields:** 45 fields
- **Child Relationships:** 12
- **Key Fields:**
  - Id, AssetActionSourceNumber
  - AssetActionId (parent reference)
  - ExternalReference, ExternalReferenceDataSource
  - ReferenceEntityItemId
  - ProductAmount, AdjustmentAmount, Subtotal
  - StartDate, EndDate, Quantity
  - TransactionDate

### 5. Application Usage Assignment
- **Label:** Application Usage Assignment
- **API Name:** AppUsageAssignment
- **Fields:** 10 fields
- **Child Relationships:** 3
- **Key Fields:**
  - Id, Name
  - AssetId (parent reference)
  - RecordId
  - AppUsageType

## Relationships

### Parent → Child
- **Asset** → AssetActions (relationship: `AssetActions`)
- **Asset** → AssetStatePeriods (relationship: `AssetStatePeriods`)
- **Asset** → AppUsageAssignments (relationship: `AppUsageAssignments`)
- **AssetAction** → AssetActionSources (relationship: `AssetActionSources`)

### Child → Parent
- **AssetAction** → Asset (via `AssetId` field)
- **AssetStatePeriod** → Asset (via `AssetId` field)
- **AppUsageAssignment** → Asset (via `AssetId` field)
- **AssetActionSource** → AssetAction (via `AssetActionId` field)

## Location
All files saved to: `/Users/david.louie/CursorProjects/RLMAssetMigrationTools/`
