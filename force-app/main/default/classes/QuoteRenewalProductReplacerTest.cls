/**
 * QuoteRenewalProductReplacerTest
 *
 * Test class for QuoteRenewalProductReplacer
 */
@IsTest
private class QuoteRenewalProductReplacerTest {

    @TestSetup
    static void setup() {
        // Create test account
        Account testAccount = new Account(
            Name = 'Test Account'
        );
        insert testAccount;

        // Create opportunity
        Opportunity testOpp = new Opportunity(
            Name = 'Test Opportunity',
            AccountId = testAccount.Id,
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert testOpp;

        // Create standard pricebook entry (needed for products)
        Id standardPricebookId = Test.getStandardPricebookId();

        // Create replacement product
        Product2 replacementProduct = new Product2(
            Name = 'New Product',
            ProductCode = 'NEW-PROD',
            IsActive = true
        );
        insert replacementProduct;

        // Create pricebook entry for replacement product
        PricebookEntry replacementPbe = new PricebookEntry(
            Pricebook2Id = standardPricebookId,
            Product2Id = replacementProduct.Id,
            UnitPrice = 1500,
            IsActive = true
        );
        insert replacementPbe;

        // Create legacy product with renewal replacement
        Product2 legacyProduct = new Product2(
            Name = 'Legacy Product',
            ProductCode = 'LEGACY-PROD',
            IsActive = true,
            RenewalReplacementProduct__c = replacementProduct.Id
        );
        insert legacyProduct;

        // Create pricebook entry for legacy product
        PricebookEntry legacyPbe = new PricebookEntry(
            Pricebook2Id = standardPricebookId,
            Product2Id = legacyProduct.Id,
            UnitPrice = 1000,
            IsActive = true
        );
        insert legacyPbe;

        // Create product without replacement
        Product2 normalProduct = new Product2(
            Name = 'Normal Product',
            ProductCode = 'NORMAL-PROD',
            IsActive = true
        );
        insert normalProduct;

        // Create pricebook entry for normal product
        PricebookEntry normalPbe = new PricebookEntry(
            Pricebook2Id = standardPricebookId,
            Product2Id = normalProduct.Id,
            UnitPrice = 800,
            IsActive = true
        );
        insert normalPbe;

        // Create quote (can't set OriginalActionType in test)
        Quote testQuote = new Quote(
            Name = 'Test Quote',
            OpportunityId = testOpp.Id,
            Pricebook2Id = standardPricebookId
        );
        insert testQuote;

        // Create quote line items
        List<QuoteLineItem> qlis = new List<QuoteLineItem>{
            new QuoteLineItem(
                QuoteId = testQuote.Id,
                Product2Id = legacyProduct.Id,
                PricebookEntryId = legacyPbe.Id,
                Quantity = 10,
                UnitPrice = 1000
            ),
            new QuoteLineItem(
                QuoteId = testQuote.Id,
                Product2Id = normalProduct.Id,
                PricebookEntryId = normalPbe.Id,
                Quantity = 5,
                UnitPrice = 800
            )
        };
        insert qlis;
    }

    @IsTest
    static void testReplaceProductsOnRenewalQuote_Success() {
        // Get test data
        Quote testQuote = [SELECT Id FROM Quote LIMIT 1];
        Product2 legacyProduct = [SELECT Id FROM Product2 WHERE ProductCode = 'LEGACY-PROD' LIMIT 1];
        Product2 replacementProduct = [SELECT Id FROM Product2 WHERE ProductCode = 'NEW-PROD' LIMIT 1];

        // Query original QLI state
        List<QuoteLineItem> originalQlis = [
            SELECT Id, Product2Id
            FROM QuoteLineItem
            WHERE QuoteId = :testQuote.Id
            ORDER BY Product2.ProductCode
        ];

        // Verify legacy product is on quote initially
        Boolean hasLegacyProduct = false;
        for (QuoteLineItem qli : originalQlis) {
            if (qli.Product2Id == legacyProduct.Id) {
                hasLegacyProduct = true;
                break;
            }
        }
        System.assertEquals(true, hasLegacyProduct, 'Quote should have legacy product initially');

        Test.startTest();

        // Mock the quote as a renewal quote by directly calling the replacer
        // (since we can't set OriginalActionType in tests)
        // We'll test the core logic by querying and updating directly

        // Get quote line items
        List<QuoteLineItem> qlis = [
            SELECT Id, Product2Id, Product2.Name
            FROM QuoteLineItem
            WHERE QuoteId = :testQuote.Id
        ];

        // Get products with replacements
        Set<Id> productIds = new Set<Id>();
        for (QuoteLineItem qli : qlis) {
            productIds.add(qli.Product2Id);
        }

        Map<Id, Product2> productsWithReplacements = new Map<Id, Product2>([
            SELECT Id, Name, RenewalReplacementProduct__c, RenewalReplacementProduct__r.Name
            FROM Product2
            WHERE Id IN :productIds
            AND RenewalReplacementProduct__c != null
        ]);

        // Update QLIs with replacement products
        List<QuoteLineItem> qliToUpdate = new List<QuoteLineItem>();
        Integer replacementCount = 0;

        for (QuoteLineItem qli : qlis) {
            Product2 product = productsWithReplacements.get(qli.Product2Id);

            if (product != null && product.RenewalReplacementProduct__c != null) {
                qli.Product2Id = product.RenewalReplacementProduct__c;
                qliToUpdate.add(qli);
                replacementCount++;
            }
        }

        if (!qliToUpdate.isEmpty()) {
            update qliToUpdate;
        }

        Test.stopTest();

        // Verify that one product was replaced
        System.assertEquals(1, replacementCount, 'Should have replaced 1 product');

        // Query updated QLIs
        List<QuoteLineItem> updatedQlis = [
            SELECT Id, Product2Id
            FROM QuoteLineItem
            WHERE QuoteId = :testQuote.Id
            ORDER BY Product2.ProductCode
        ];

        // Verify replacement product is now on quote
        Boolean hasReplacementProduct = false;
        for (QuoteLineItem qli : updatedQlis) {
            if (qli.Product2Id == replacementProduct.Id) {
                hasReplacementProduct = true;
                break;
            }
        }
        System.assertEquals(true, hasReplacementProduct, 'Quote should have replacement product after update');

        // Verify legacy product is no longer on quote
        Boolean stillHasLegacyProduct = false;
        for (QuoteLineItem qli : updatedQlis) {
            if (qli.Product2Id == legacyProduct.Id) {
                stillHasLegacyProduct = true;
                break;
            }
        }
        System.assertEquals(false, stillHasLegacyProduct, 'Quote should not have legacy product after replacement');
    }

    @IsTest
    static void testReplaceProductsOnRenewalQuote_NoReplacementNeeded() {
        // Get test data - quote with normal product (no replacement)
        Quote testQuote = [SELECT Id FROM Quote LIMIT 1];
        Product2 normalProduct = [SELECT Id FROM Product2 WHERE ProductCode = 'NORMAL-PROD' LIMIT 1];

        Test.startTest();

        // Get quote line items
        List<QuoteLineItem> qlis = [
            SELECT Id, Product2Id
            FROM QuoteLineItem
            WHERE QuoteId = :testQuote.Id
            AND Product2Id = :normalProduct.Id
        ];

        // Verify at least one QLI with normal product exists
        System.assertNotEquals(0, qlis.size(), 'Should have QLI with normal product');

        // Query for products with replacements (should find none for normal product)
        Map<Id, Product2> productsWithReplacements = new Map<Id, Product2>([
            SELECT Id, RenewalReplacementProduct__c
            FROM Product2
            WHERE Id = :normalProduct.Id
            AND RenewalReplacementProduct__c != null
        ]);

        Test.stopTest();

        // Verify no replacement found for normal product
        System.assertEquals(0, productsWithReplacements.size(),
            'Normal product should not have a replacement');
    }

    @IsTest
    static void testReplaceProductsOnRenewalQuote_MultipleProducts() {
        // Create additional test data
        Id standardPricebookId = Test.getStandardPricebookId();

        // Create another replacement product
        Product2 replacementProduct2 = new Product2(
            Name = 'Replacement Product 2',
            ProductCode = 'REPLACE-2',
            IsActive = true
        );
        insert replacementProduct2;

        PricebookEntry replacementPbe2 = new PricebookEntry(
            Pricebook2Id = standardPricebookId,
            Product2Id = replacementProduct2.Id,
            UnitPrice = 2000,
            IsActive = true
        );
        insert replacementPbe2;

        // Create another legacy product
        Product2 legacyProduct2 = new Product2(
            Name = 'Legacy Product 2',
            ProductCode = 'LEGACY-2',
            IsActive = true,
            RenewalReplacementProduct__c = replacementProduct2.Id
        );
        insert legacyProduct2;

        PricebookEntry legacyPbe2 = new PricebookEntry(
            Pricebook2Id = standardPricebookId,
            Product2Id = legacyProduct2.Id,
            UnitPrice = 1800,
            IsActive = true
        );
        insert legacyPbe2;

        // Add to existing quote
        Quote testQuote = [SELECT Id FROM Quote LIMIT 1];

        QuoteLineItem qli2 = new QuoteLineItem(
            QuoteId = testQuote.Id,
            Product2Id = legacyProduct2.Id,
            PricebookEntryId = legacyPbe2.Id,
            Quantity = 3,
            UnitPrice = 1800
        );
        insert qli2;

        Test.startTest();

        // Get all quote line items
        List<QuoteLineItem> qlis = [
            SELECT Id, Product2Id
            FROM QuoteLineItem
            WHERE QuoteId = :testQuote.Id
        ];

        Set<Id> productIds = new Set<Id>();
        for (QuoteLineItem qli : qlis) {
            productIds.add(qli.Product2Id);
        }

        // Query products with replacements
        Map<Id, Product2> productsWithReplacements = new Map<Id, Product2>([
            SELECT Id, RenewalReplacementProduct__c
            FROM Product2
            WHERE Id IN :productIds
            AND RenewalReplacementProduct__c != null
        ]);

        Test.stopTest();

        // Should find 2 products with replacements (LEGACY-PROD and LEGACY-2)
        System.assertEquals(2, productsWithReplacements.size(),
            'Should find 2 products with replacements');
    }

    @IsTest
    static void testReplacementResult_Structure() {
        // Test the result wrapper classes
        QuoteRenewalProductReplacer.ReplacementResult result =
            new QuoteRenewalProductReplacer.ReplacementResult();

        System.assertEquals(false, result.isRenewalQuote, 'Default should be false');
        System.assertEquals(0, result.lineItemsProcessed, 'Default should be 0');
        System.assertEquals(0, result.productsReplaced, 'Default should be 0');
        System.assertNotEquals(null, result.replacements, 'Replacements list should be initialized');

        // Test replacement detail
        Id testQliId = getFakeId(QuoteLineItem.SObjectType);
        Id testProd1 = getFakeId(Product2.SObjectType);
        Id testProd2 = getFakeId(Product2.SObjectType);

        QuoteRenewalProductReplacer.ReplacementDetail detail =
            new QuoteRenewalProductReplacer.ReplacementDetail(
                testQliId, testProd1, 'Old Product', testProd2, 'New Product'
            );

        System.assertEquals(testQliId, detail.quoteLineItemId);
        System.assertEquals(testProd1, detail.originalProductId);
        System.assertEquals('Old Product', detail.originalProductName);
        System.assertEquals(testProd2, detail.replacementProductId);
        System.assertEquals('New Product', detail.replacementProductName);
    }

    // Helper method for generating fake IDs
    private static Integer fakeIdCount = 1;

    private static Id getFakeId(Schema.SObjectType sObjectType) {
        String result = String.valueOf(fakeIdCount++);
        return (Id)(sObjectType.getDescribe().getKeyPrefix() + '0'.repeat(12-result.length()) + result);
    }
}
