/**
 * QuoteRenewalChecker
 *
 * Utility class to check if a Quote is a renewal quote based on the OriginalActionType field.
 *
 * Usage:
 *   Boolean isRenewal = QuoteRenewalChecker.isRenewalQuote(quoteId);
 *   Boolean isRenewal = QuoteRenewalChecker.isRenewalQuote(quoteRecord);
 */
public with sharing class QuoteRenewalChecker {

    // Constant for the Renewal action type value
    private static final String RENEWAL_ACTION_TYPE = 'Renew';

    /**
     * Check if a quote is a renewal quote by Quote ID
     *
     * @param quoteId The ID of the Quote record
     * @return True if the quote has OriginalActionType = 'Renew', false otherwise
     */
    public static Boolean isRenewalQuote(Id quoteId) {
        if (quoteId == null) {
            throw new IllegalArgumentException('Quote ID cannot be null');
        }

        try {
            Quote quote = [
                SELECT Id, QuoteNumber, OriginalActionType
                FROM Quote
                WHERE Id = :quoteId
                LIMIT 1
            ];

            return isRenewalQuote(quote);
        } catch (QueryException e) {
            throw new QuoteNotFoundException('Quote not found with ID: ' + quoteId, e);
        }
    }

    /**
     * Check if a quote is a renewal quote from a Quote record
     *
     * @param quote The Quote record (must include OriginalActionType field)
     * @return True if the quote has OriginalActionType = 'Renew', false otherwise
     */
    public static Boolean isRenewalQuote(Quote quote) {
        if (quote == null) {
            throw new IllegalArgumentException('Quote record cannot be null');
        }

        return RENEWAL_ACTION_TYPE.equalsIgnoreCase(quote.OriginalActionType);
    }

    /**
     * Check if multiple quotes are renewal quotes
     *
     * @param quoteIds Set of Quote IDs to check
     * @return Map of Quote ID to Boolean (true if renewal, false otherwise)
     */
    public static Map<Id, Boolean> areRenewalQuotes(Set<Id> quoteIds) {
        Map<Id, Boolean> results = new Map<Id, Boolean>();

        if (quoteIds == null || quoteIds.isEmpty()) {
            return results;
        }

        List<Quote> quotes = [
            SELECT Id, OriginalActionType
            FROM Quote
            WHERE Id IN :quoteIds
        ];

        for (Quote quote : quotes) {
            results.put(quote.Id, isRenewalQuote(quote));
        }

        return results;
    }

    /**
     * Get all renewal quotes from a list of Quote records
     *
     * @param quotes List of Quote records (must include OriginalActionType field)
     * @return List of Quote records that are renewals
     */
    public static List<Quote> filterRenewalQuotes(List<Quote> quotes) {
        List<Quote> renewalQuotes = new List<Quote>();

        if (quotes == null || quotes.isEmpty()) {
            return renewalQuotes;
        }

        for (Quote quote : quotes) {
            if (isRenewalQuote(quote)) {
                renewalQuotes.add(quote);
            }
        }

        return renewalQuotes;
    }

    /**
     * Custom exception for quote not found scenarios
     */
    public class QuoteNotFoundException extends Exception {}
}
