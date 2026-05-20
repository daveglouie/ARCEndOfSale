/**
 * RepriceQuotesPST
 *
 * Reprices quotes using Place Sales Transaction (PST) API.
 * This invocable method can be called from Flow, Process Builder, or Apex.
 *
 * Usage:
 *   List<String> quoteIds = new List<String>{'0Q0XXXXXXXXXXXX'};
 *   RepriceQuotesPST.repriceQuotesPST(quoteIds);
 */
public class RepriceQuotesPST {

    /**
     * Async version - reprices quotes in future context for better UI responsiveness
     */
    @future
    public static void repriceQuotesPSTAsync(List<String> ids) {
        repriceQuotesPST(ids);
    }

    @InvocableMethod(label='repriceQuotesPST' category='Quote')
    public static void repriceQuotesPST(List<String> ids) {
        RevSalesTrxn.PricingPreferenceEnum pricingPreference = RevSalesTrxn.PricingPreferenceEnum.FORCE;
        RevSalesTrxn.ConfigurationExecutionEnum configEnum = RevSalesTrxn.ConfigurationExecutionEnum.SYSTEM;
        RevSalesTrxn.ConfigurationOptionsInput config = new RevSalesTrxn.ConfigurationOptionsInput();
        config.addDefaultConfiguration = true;
        config.executeConfigurationRules = true;
        config.validateAmendRenewCancel = true;
        config.validateProductCatalog = true;

        for (String id : ids) {
            RevSalesTrxn.RecordResource quoteRecord = new RevSalesTrxn.RecordResource(Quote.getSObjectType(), 'PATCH', id);
            RevSalesTrxn.RecordWithReferenceRequest quoteObject = new RevSalesTrxn.RecordWithReferenceRequest('refQuote', quoteRecord);

            List<RevSalesTrxn.RecordWithReferenceRequest> records = new List<RevSalesTrxn.RecordWithReferenceRequest>();
            records.add(quoteObject);

            RevSalesTrxn.GraphRequest graph = new RevSalesTrxn.GraphRequest('myGraphId', records);
            RevSalesTrxn.PlaceSalesTransactionExecutor.execute(graph, pricingPreference, configEnum, config, null);
        }
    }
}
