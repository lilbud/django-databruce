const originalAttachShadow = Element.prototype.attachShadow;
Element.prototype.attachShadow = function (options) {
    // Force the mode to open so we can inspect it later
    if (options && options.mode === 'closed') {
        options.mode = 'open';
    }

    return originalAttachShadow.call(this, options);
};

const observer = new MutationObserver(() => {
    // Scan all elements on the page that have an open shadowRoot
    document.querySelectorAll('*').forEach(el => {
        if (el.shadowRoot) {
            // Look for the specific link inside the open root
            const link = el.shadowRoot.querySelector('a[href="https://datatables.net/tn/25"]');
            if (link) {
                // remove element
                el.remove()
            }
        }
    });
});

observer.observe(document.documentElement, { childList: true, subtree: true });