import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { CloseActionScreenEvent } from 'lightning/actions';
import replaceProducts from '@salesforce/apex/QuoteRenewalProductReplacer.replaceProductsOnRenewalQuote';

export default class QuoteRenewalProductReplacer extends LightningElement {
    @api recordId;
    isProcessing = false;

    // Required method for Quick Action
    @api
    invoke() {
        console.log('invoke() called, recordId:', this.recordId);

        // Check if recordId is available
        if (!this.recordId) {
            this.showToast(
                'Error',
                'No Quote ID found. Please invoke this action from a Quote record page.',
                'error'
            );
            this.closeAction();
            return;
        }

        this.handleReplaceProducts();
    }

    handleReplaceProducts() {
        this.isProcessing = true;
        console.log('Calling replaceProducts with quoteId:', this.recordId);

        replaceProducts({ quoteId: this.recordId })
            .then(result => {
                console.log('Result received:', JSON.stringify(result));
                if (result.isRenewalQuote) {
                    if (result.productsReplaced > 0) {
                        // Success - products were replaced
                        this.showToast(
                            'Success',
                            `Replaced ${result.productsReplaced} product(s) on renewal quote. Repricing in progress - refresh the page in a few moments to see the updated quote.`,
                            'success'
                        );
                        this.closeAction();
                    } else {
                        // No products needed replacement
                        this.showToast(
                            'No Changes',
                            'No products needed replacement. All products are already up to date.',
                            'info'
                        );
                        this.closeAction();
                    }
                } else {
                    // Not a renewal quote
                    this.showToast(
                        'Not a Renewal Quote',
                        'This quote is not a renewal quote. Product replacement is only available for renewal quotes.',
                        'warning'
                    );
                    this.closeAction();
                }
            })
            .catch(error => {
                console.error('Error in replaceProducts:', error);
                console.error('Error details:', JSON.stringify(error));
                this.showToast(
                    'Error',
                    `Failed to replace products: ${this.getErrorMessage(error)}`,
                    'error'
                );
                this.closeAction();
            })
            .finally(() => {
                this.isProcessing = false;
            });
    }

    showToast(title, message, variant, mode = 'dismissable') {
        const event = new ShowToastEvent({
            title: title,
            message: message,
            variant: variant,
            mode: mode  // 'dismissable' (default), 'pester', or 'sticky'
        });
        this.dispatchEvent(event);
    }

    getErrorMessage(error) {
        if (error.body && error.body.message) {
            return error.body.message;
        } else if (error.message) {
            return error.message;
        } else {
            return 'Unknown error';
        }
    }

    closeAction() {
        this.dispatchEvent(new CloseActionScreenEvent());
    }

    refreshPage() {
        // Close the action and refresh the page
        this.closeAction();

        // Use setTimeout to ensure the modal closes before refresh
        setTimeout(() => {
            // eslint-disable-next-line no-restricted-globals
            location.reload();
        }, 500);
    }
}