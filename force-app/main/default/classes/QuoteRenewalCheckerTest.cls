/**
 * QuoteRenewalCheckerTest
 *
 * Test class for QuoteRenewalChecker
 * Note: OriginalActionType is a read-only field, so we use mock objects for testing
 */
@IsTest
private class QuoteRenewalCheckerTest {

    /**
     * Helper method to create a mock Quote with OriginalActionType set
     * Uses JSON deserialization to set read-only fields
     */
    private static Quote createMockQuote(String actionType) {
        Map<String, Object> quoteFields = new Map<String, Object>{
            'Id' => getFakeId(Quote.SObjectType),
            'OriginalActionType' => actionType
        };
        return (Quote) JSON.deserialize(JSON.serialize(quoteFields), Quote.class);
    }

    @IsTest
    static void testIsRenewalQuote_ByRecord_Renewal() {
        // Given a renewal quote record
        Quote renewalQuote = createMockQuote('Renew');

        // When checking if it's a renewal
        Test.startTest();
        Boolean result = QuoteRenewalChecker.isRenewalQuote(renewalQuote);
        Test.stopTest();

        // Then it should return true
        System.assertEquals(true, result, 'Renewal quote record should return true');
    }

    @IsTest
    static void testIsRenewalQuote_ByRecord_NonRenewal_Add() {
        // Given an add quote record
        Quote addQuote = createMockQuote('Add');

        // When checking if it's a renewal
        Test.startTest();
        Boolean result = QuoteRenewalChecker.isRenewalQuote(addQuote);
        Test.stopTest();

        // Then it should return false
        System.assertEquals(false, result, 'Add quote record should return false');
    }

    @IsTest
    static void testIsRenewalQuote_ByRecord_NonRenewal_Amend() {
        // Given an amend quote record
        Quote amendQuote = createMockQuote('Amend');

        // When checking if it's a renewal
        Test.startTest();
        Boolean result = QuoteRenewalChecker.isRenewalQuote(amendQuote);
        Test.stopTest();

        // Then it should return false
        System.assertEquals(false, result, 'Amend quote record should return false');
    }

    @IsTest
    static void testIsRenewalQuote_NullActionType() {
        // Given a quote with null OriginalActionType
        Quote nullActionQuote = createMockQuote(null);

        // When checking if it's a renewal
        Test.startTest();
        Boolean result = QuoteRenewalChecker.isRenewalQuote(nullActionQuote);
        Test.stopTest();

        // Then it should return false
        System.assertEquals(false, result, 'Quote with null action type should return false');
    }

    @IsTest
    static void testIsRenewalQuote_CaseInsensitive() {
        // Given a quote with lowercase 'renew'
        Quote renewalQuote = createMockQuote('renew');

        // When checking if it's a renewal
        Test.startTest();
        Boolean result = QuoteRenewalChecker.isRenewalQuote(renewalQuote);
        Test.stopTest();

        // Then it should return true (case insensitive)
        System.assertEquals(true, result, 'Lowercase renew should return true');
    }

    @IsTest
    static void testIsRenewalQuote_NullRecord() {
        // Given a null quote record
        Quote nullQuote = null;

        // When checking if it's a renewal
        // Then it should throw an exception
        Test.startTest();
        try {
            QuoteRenewalChecker.isRenewalQuote(nullQuote);
            System.assert(false, 'Should have thrown IllegalArgumentException');
        } catch (IllegalArgumentException e) {
            System.assertEquals('Quote record cannot be null', e.getMessage());
        }
        Test.stopTest();
    }

    @IsTest
    static void testFilterRenewalQuotes() {
        // Given a list of quotes with different action types
        List<Quote> quotes = new List<Quote>{
            createMockQuote('Renew'),
            createMockQuote('Add'),
            createMockQuote('Amend'),
            createMockQuote(null),
            createMockQuote('Renew')
        };

        // When filtering for renewals
        Test.startTest();
        List<Quote> renewalQuotes = QuoteRenewalChecker.filterRenewalQuotes(quotes);
        Test.stopTest();

        // Then should return only the renewal quotes
        System.assertEquals(2, renewalQuotes.size(), 'Should return 2 renewal quotes');
        System.assertEquals('Renew', renewalQuotes[0].OriginalActionType, 'First should be renewal');
        System.assertEquals('Renew', renewalQuotes[1].OriginalActionType, 'Second should be renewal');
    }

    @IsTest
    static void testFilterRenewalQuotes_EmptyList() {
        // Given an empty list
        List<Quote> emptyList = new List<Quote>();

        // When filtering for renewals
        Test.startTest();
        List<Quote> renewalQuotes = QuoteRenewalChecker.filterRenewalQuotes(emptyList);
        Test.stopTest();

        // Then should return empty list
        System.assertEquals(0, renewalQuotes.size(), 'Empty list should return empty list');
    }

    @IsTest
    static void testFilterRenewalQuotes_NullList() {
        // Given a null list
        List<Quote> nullList = null;

        // When filtering for renewals
        Test.startTest();
        List<Quote> renewalQuotes = QuoteRenewalChecker.filterRenewalQuotes(nullList);
        Test.stopTest();

        // Then should return empty list
        System.assertEquals(0, renewalQuotes.size(), 'Null list should return empty list');
    }

    @IsTest
    static void testFilterRenewalQuotes_AllRenewals() {
        // Given a list of all renewal quotes
        List<Quote> quotes = new List<Quote>{
            createMockQuote('Renew'),
            createMockQuote('Renew'),
            createMockQuote('Renew')
        };

        // When filtering for renewals
        Test.startTest();
        List<Quote> renewalQuotes = QuoteRenewalChecker.filterRenewalQuotes(quotes);
        Test.stopTest();

        // Then should return all quotes
        System.assertEquals(3, renewalQuotes.size(), 'Should return all 3 renewal quotes');
    }

    @IsTest
    static void testFilterRenewalQuotes_NoRenewals() {
        // Given a list with no renewal quotes
        List<Quote> quotes = new List<Quote>{
            createMockQuote('Add'),
            createMockQuote('Amend'),
            createMockQuote(null)
        };

        // When filtering for renewals
        Test.startTest();
        List<Quote> renewalQuotes = QuoteRenewalChecker.filterRenewalQuotes(quotes);
        Test.stopTest();

        // Then should return empty list
        System.assertEquals(0, renewalQuotes.size(), 'Should return no quotes');
    }

    // Counter for generating unique fake IDs
    private static Integer fakeIdCount = 1;

    /**
     * Helper method to generate fake Salesforce IDs for testing
     */
    private static Id getFakeId(Schema.SObjectType sObjectType) {
        String result = String.valueOf(fakeIdCount++);
        return (Id)(sObjectType.getDescribe().getKeyPrefix() + '0'.repeat(12-result.length()) + result);
    }
}
