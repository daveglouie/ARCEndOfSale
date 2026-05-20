/**
 * QuoteRenewalProductReplacer
 *
 * Handles automatic product replacement for renewal quotes based on the
 * RenewalReplacementProduct__c field on Product2.
 *
 * Usage:
 *   QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote(quoteId);
 */
public with sharing class QuoteRenewalProductReplacer {

    /**
     * Result class containing information about the replacement operation
     */
    public class ReplacementResult {
        @AuraEnabled public Boolean isRenewalQuote;
        @AuraEnabled public Integer lineItemsProcessed;
        @AuraEnabled public Integer productsReplaced;
        @AuraEnabled public List<ReplacementDetail> replacements;

        public ReplacementResult() {
            this.isRenewalQuote = false;
            this.lineItemsProcessed = 0;
            this.productsReplaced = 0;
            this.replacements = new List<ReplacementDetail>();
        }
    }

    /**
     * Details about a specific product replacement
     */
    public class ReplacementDetail {
        @AuraEnabled public Id quoteLineItemId;
        @AuraEnabled public Id originalProductId;
        @AuraEnabled public String originalProductName;
        @AuraEnabled public Id replacementProductId;
        @AuraEnabled public String replacementProductName;

        public ReplacementDetail(Id qliId, Id origProdId, String origProdName,
                                Id replProdId, String replProdName) {
            this.quoteLineItemId = qliId;
            this.originalProductId = origProdId;
            this.originalProductName = origProdName;
            this.replacementProductId = replProdId;
            this.replacementProductName = replProdName;
        }
    }

    /**
     * Replace products on a renewal quote with their renewal replacement products
     *
     * Note: Since Product2Id is not updateable on QuoteLineItem, this method deletes
     * the old QLI and creates a new one with the replacement product, preserving key
     * fields like Quantity, StartDate, PeriodBoundary, etc.
     *
     * @param quoteId The ID of the Quote to process
     * @return ReplacementResult containing details about the operation
     */
    @AuraEnabled
    public static ReplacementResult replaceProductsOnRenewalQuote(Id quoteId) {
        if (quoteId == null) {
            throw new IllegalArgumentException('Quote ID cannot be null');
        }

        ReplacementResult result = new ReplacementResult();

        // Check if this is a renewal quote
        if (!QuoteRenewalChecker.isRenewalQuote(quoteId)) {
            return result;
        }

        result.isRenewalQuote = true;

        // Query quote line items with all fields needed for replacement
        List<QuoteLineItem> quoteLineItems = [
            SELECT Id, QuoteId, Product2Id, Product2.Name, PricebookEntryId,
                   Quantity, UnitPrice, Discount, Description,
                   StartDate, PeriodBoundary, PeriodBoundaryDay,
                   PeriodBoundaryStartMonth, SubscriptionTerm
            FROM QuoteLineItem
            WHERE QuoteId = :quoteId
        ];

        result.lineItemsProcessed = quoteLineItems.size();

        if (quoteLineItems.isEmpty()) {
            return result;
        }

        // Collect all product IDs
        Set<Id> productIds = new Set<Id>();
        for (QuoteLineItem qli : quoteLineItems) {
            productIds.add(qli.Product2Id);
        }

        // Query products to get their renewal replacement products
        Map<Id, Product2> productsWithReplacements = new Map<Id, Product2>([
            SELECT Id, Name, RenewalReplacementProduct__c, RenewalReplacementProduct__r.Name
            FROM Product2
            WHERE Id IN :productIds
            AND RenewalReplacementProduct__c != null
        ]);

        // Get replacement product IDs to query their pricebook entries
        Set<Id> replacementProductIds = new Set<Id>();
        for (Product2 product : productsWithReplacements.values()) {
            if (product.RenewalReplacementProduct__c != null) {
                replacementProductIds.add(product.RenewalReplacementProduct__c);
            }
        }

        // Query pricebook entries for replacement products (use the same pricebook as the quote)
        List<Quote> quotes = [SELECT Id, Pricebook2Id FROM Quote WHERE Id = :quoteId LIMIT 1];
        Id pricebookId = quotes[0].Pricebook2Id;

        Map<Id, PricebookEntry> replacementPricebookEntries = new Map<Id, PricebookEntry>();
        if (!replacementProductIds.isEmpty()) {
            List<PricebookEntry> pbes = [
                SELECT Id, Product2Id, UnitPrice, IsActive
                FROM PricebookEntry
                WHERE Product2Id IN :replacementProductIds
                AND Pricebook2Id = :pricebookId
                AND IsActive = true
            ];

            for (PricebookEntry pbe : pbes) {
                replacementPricebookEntries.put(pbe.Product2Id, pbe);
            }
        }

        // Create new QLIs and track old QLIs to delete
        List<QuoteLineItem> qliToDelete = new List<QuoteLineItem>();
        List<QuoteLineItem> qliToInsert = new List<QuoteLineItem>();

        for (QuoteLineItem qli : quoteLineItems) {
            Product2 product = productsWithReplacements.get(qli.Product2Id);

            if (product != null && product.RenewalReplacementProduct__c != null) {
                // Get the pricebook entry for the replacement product
                PricebookEntry replacementPbe = replacementPricebookEntries.get(product.RenewalReplacementProduct__c);

                if (replacementPbe != null) {
                    // Track the replacement
                    result.replacements.add(new ReplacementDetail(
                        qli.Id,
                        qli.Product2Id,
                        qli.Product2.Name,
                        product.RenewalReplacementProduct__c,
                        product.RenewalReplacementProduct__r.Name
                    ));

                    // Create new QLI with replacement product, copying key fields
                    QuoteLineItem newQli = new QuoteLineItem(
                        QuoteId = qli.QuoteId,
                        PricebookEntryId = replacementPbe.Id,
                        Quantity = qli.Quantity,
                        Discount = qli.Discount,
                        Description = qli.Description,
                        StartDate = qli.StartDate,
                        PeriodBoundary = qli.PeriodBoundary,
                        PeriodBoundaryDay = qli.PeriodBoundaryDay,
                        PeriodBoundaryStartMonth = qli.PeriodBoundaryStartMonth,
                        SubscriptionTerm = qli.SubscriptionTerm
                    );

                    qliToInsert.add(newQli);
                    qliToDelete.add(qli);
                }
            }
        }

        // Perform the replacement (insert new, then delete old)
        if (!qliToInsert.isEmpty()) {
            insert qliToInsert;
            delete qliToDelete;
            result.productsReplaced = qliToInsert.size();

            // Automatically reprice the quote after replacement (async for better UI responsiveness)
            List<String> quoteIdsToReprice = new List<String>{ String.valueOf(quoteId) };
            RepriceQuotesPST.repriceQuotesPSTAsync(quoteIdsToReprice);
        }

        return result;
    }

    /**
     * Replace products on multiple renewal quotes in bulk
     *
     * Note: Since Product2Id is not updateable on QuoteLineItem, this method deletes
     * old QLIs and creates new ones with replacement products, preserving key fields.
     *
     * @param quoteIds Set of Quote IDs to process
     * @return Map of Quote ID to ReplacementResult
     */
    public static Map<Id, ReplacementResult> replaceProductsOnRenewalQuotes(Set<Id> quoteIds) {
        Map<Id, ReplacementResult> results = new Map<Id, ReplacementResult>();

        if (quoteIds == null || quoteIds.isEmpty()) {
            return results;
        }

        // Check which quotes are renewal quotes
        Map<Id, Boolean> renewalQuoteMap = QuoteRenewalChecker.areRenewalQuotes(quoteIds);

        // Filter to only renewal quotes
        Set<Id> renewalQuoteIds = new Set<Id>();
        for (Id quoteId : quoteIds) {
            if (renewalQuoteMap.get(quoteId) == true) {
                renewalQuoteIds.add(quoteId);
            } else {
                // Create result for non-renewal quotes
                ReplacementResult result = new ReplacementResult();
                result.isRenewalQuote = false;
                results.put(quoteId, result);
            }
        }

        if (renewalQuoteIds.isEmpty()) {
            return results;
        }

        // Query all quote line items with all fields needed for replacement
        List<QuoteLineItem> allQuoteLineItems = [
            SELECT Id, QuoteId, Product2Id, Product2.Name, PricebookEntryId,
                   Quantity, UnitPrice, Discount, Description,
                   StartDate, PeriodBoundary, PeriodBoundaryDay,
                   PeriodBoundaryStartMonth, SubscriptionTerm
            FROM QuoteLineItem
            WHERE QuoteId IN :renewalQuoteIds
        ];

        // Group QLIs by Quote ID
        Map<Id, List<QuoteLineItem>> qlisByQuoteId = new Map<Id, List<QuoteLineItem>>();
        Set<Id> allProductIds = new Set<Id>();

        for (QuoteLineItem qli : allQuoteLineItems) {
            if (!qlisByQuoteId.containsKey(qli.QuoteId)) {
                qlisByQuoteId.put(qli.QuoteId, new List<QuoteLineItem>());
            }
            qlisByQuoteId.get(qli.QuoteId).add(qli);
            allProductIds.add(qli.Product2Id);
        }

        // Query all products with replacement products
        Map<Id, Product2> productsWithReplacements = new Map<Id, Product2>([
            SELECT Id, Name, RenewalReplacementProduct__c, RenewalReplacementProduct__r.Name
            FROM Product2
            WHERE Id IN :allProductIds
            AND RenewalReplacementProduct__c != null
        ]);

        // Get replacement product IDs to query their pricebook entries
        Set<Id> replacementProductIds = new Set<Id>();
        for (Product2 product : productsWithReplacements.values()) {
            if (product.RenewalReplacementProduct__c != null) {
                replacementProductIds.add(product.RenewalReplacementProduct__c);
            }
        }

        // Query quotes to get their pricebook IDs
        Map<Id, Id> quotePricebookMap = new Map<Id, Id>();
        for (Quote q : [SELECT Id, Pricebook2Id FROM Quote WHERE Id IN :renewalQuoteIds]) {
            quotePricebookMap.put(q.Id, q.Pricebook2Id);
        }

        // Get all unique pricebook IDs
        Set<Id> pricebookIds = new Set<Id>(quotePricebookMap.values());

        // Query pricebook entries for replacement products across all relevant pricebooks
        Map<String, PricebookEntry> replacementPricebookEntries = new Map<String, PricebookEntry>();
        if (!replacementProductIds.isEmpty()) {
            List<PricebookEntry> pbes = [
                SELECT Id, Product2Id, Pricebook2Id, UnitPrice, IsActive
                FROM PricebookEntry
                WHERE Product2Id IN :replacementProductIds
                AND Pricebook2Id IN :pricebookIds
                AND IsActive = true
            ];

            for (PricebookEntry pbe : pbes) {
                // Key: ProductId|PricebookId
                String key = String.valueOf(pbe.Product2Id) + '|' + String.valueOf(pbe.Pricebook2Id);
                replacementPricebookEntries.put(key, pbe);
            }
        }

        // Process each renewal quote
        List<QuoteLineItem> allQliToDelete = new List<QuoteLineItem>();
        List<QuoteLineItem> allQliToInsert = new List<QuoteLineItem>();

        for (Id quoteId : renewalQuoteIds) {
            ReplacementResult result = new ReplacementResult();
            result.isRenewalQuote = true;

            List<QuoteLineItem> quoteLineItems = qlisByQuoteId.get(quoteId);
            Id pricebookId = quotePricebookMap.get(quoteId);

            if (quoteLineItems != null) {
                result.lineItemsProcessed = quoteLineItems.size();

                for (QuoteLineItem qli : quoteLineItems) {
                    Product2 product = productsWithReplacements.get(qli.Product2Id);

                    if (product != null && product.RenewalReplacementProduct__c != null) {
                        // Get the pricebook entry for the replacement product
                        String pbeKey = String.valueOf(product.RenewalReplacementProduct__c) + '|' + String.valueOf(pricebookId);
                        PricebookEntry replacementPbe = replacementPricebookEntries.get(pbeKey);

                        if (replacementPbe != null) {
                            result.replacements.add(new ReplacementDetail(
                                qli.Id,
                                qli.Product2Id,
                                qli.Product2.Name,
                                product.RenewalReplacementProduct__c,
                                product.RenewalReplacementProduct__r.Name
                            ));

                            // Create new QLI with replacement product, copying key fields
                            QuoteLineItem newQli = new QuoteLineItem(
                                QuoteId = qli.QuoteId,
                                PricebookEntryId = replacementPbe.Id,
                                Quantity = qli.Quantity,
                                Discount = qli.Discount,
                                Description = qli.Description,
                                StartDate = qli.StartDate,
                                PeriodBoundary = qli.PeriodBoundary,
                                PeriodBoundaryDay = qli.PeriodBoundaryDay,
                                PeriodBoundaryStartMonth = qli.PeriodBoundaryStartMonth,
                                SubscriptionTerm = qli.SubscriptionTerm
                            );

                            allQliToInsert.add(newQli);
                            allQliToDelete.add(qli);
                        }
                    }
                }

                result.productsReplaced = result.replacements.size();
            }

            results.put(quoteId, result);
        }

        // Perform bulk replacement (insert new, then delete old)
        if (!allQliToInsert.isEmpty()) {
            insert allQliToInsert;
            delete allQliToDelete;

            // Automatically reprice all quotes that had products replaced
            List<String> quoteIdsToReprice = new List<String>();
            for (Id quoteId : renewalQuoteIds) {
                ReplacementResult result = results.get(quoteId);
                if (result != null && result.productsReplaced > 0) {
                    quoteIdsToReprice.add(String.valueOf(quoteId));
                }
            }

            if (!quoteIdsToReprice.isEmpty()) {
                RepriceQuotesPST.repriceQuotesPST(quoteIdsToReprice);
            }
        }

        return results;
    }

    /**
     * Custom exception for product replacement errors
     */
    public class ProductReplacementException extends Exception {}
}
