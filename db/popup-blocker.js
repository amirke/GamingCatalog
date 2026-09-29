/**
 * PS4 Games Database - Popup Blocker & Ad Blocker
 * Prevents unwanted popups, redirects, and ads from opening
 * Compatible with PS4 WebKit browser
 */

(function() {
    'use strict';
    
    // Configuration
    var config = {
        blockPopups: true,
        blockRedirects: true,
        blockAds: true,
        blockExternalLinks: false,
        allowedDomains: [
            'mediafire.com',
            '1fichier.com',
            '1file',
            'mega.nz',
            'drive.google.com',
            'dropbox.com',
            'dlpsgame.com'
        ]
    };
    
    // Track blocked popups
    var blockedCount = 0;
    
    // Override window.open to block popups
    var originalOpen = window.open;
    window.open = function(url, target, features) {
        blockedCount++;
        console.log('[Popup Blocker] Blocked popup #' + blockedCount + ': ' + url);
        return null;
    };
    
    // Block window.location redirects to suspicious domains
    var originalLocationHref = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
    // Some browsers expose href on the Location instance, not its prototype.
    if (originalLocationHref && originalLocationHref.configurable && originalLocationHref.get && originalLocationHref.set) {
    Object.defineProperty(Location.prototype, 'href', {
        set: function(url) {
            if (isSuspiciousDomain(url)) {
                console.log('[Popup Blocker] Blocked redirect to: ' + url);
                return;
            }
            originalLocationHref.set.call(this, url);
        },
        get: originalLocationHref.get
    });
    }
    
    // Block target="_blank" on suspicious links
    document.addEventListener('click', function(e) {
        var target = e.target;
        
        // Find the link element
        while (target && target.tagName !== 'A') {
            target = target.parentElement;
        }
        
        if (target && target.tagName === 'A') {
            var href = target.getAttribute('href');
            var targetAttr = target.getAttribute('target');
            
            // Block external blank targets
            if (targetAttr === '_blank' && isSuspiciousDomain(href)) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[Popup Blocker] Blocked external link: ' + href);
                return false;
            }
        }
    }, true);
    
    // Block common ad/redirect patterns
    document.addEventListener('beforeunload', function(e) {
        // Check if navigation is to a suspicious domain
        if (window.location.href && isSuspiciousDomain(window.location.href)) {
            console.log('[Popup Blocker] Suspicious navigation detected');
        }
    });
    
    // Intercept fetch requests to block ad networks
    if (window.fetch) {
        var originalFetch = window.fetch;
        window.fetch = function(resource, config) {
            if (typeof resource === 'string' && isAdNetwork(resource)) {
                console.log('[Popup Blocker] Blocked ad network request: ' + resource);
                return Promise.reject(new Error('Blocked by popup blocker'));
            }
            return originalFetch.apply(this, arguments);
        };
    }
    
    // Intercept XMLHttpRequest to block ad networks
    var originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        if (isAdNetwork(url)) {
            console.log('[Popup Blocker] Blocked ad network XHR: ' + url);
            this._blocked = true;
            return;
        }
        return originalXHROpen.apply(this, arguments);
    };
    
    var originalXHRSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function() {
        if (this._blocked) {
            return;
        }
        return originalXHRSend.apply(this, arguments);
    };
    
    // Block script injection attempts
    var originalCreateElement = document.createElement;
    document.createElement = function(tagName) {
        var element = originalCreateElement.call(document, tagName);
        
        if (tagName.toLowerCase() === 'script') {
            var originalSetAttribute = element.setAttribute;
            element.setAttribute = function(name, value) {
                if (name === 'src' && isAdNetwork(value)) {
                    console.log('[Popup Blocker] Blocked ad script: ' + value);
                    return;
                }
                return originalSetAttribute.call(this, name, value);
            };
        }
        
        return element;
    };
    
    // Remove common ad elements
    function removeAdElements() {
        var adSelectors = [
            '[id*="ad"]',
            '[class*="ad"]',
            '[id*="banner"]',
            '[class*="banner"]',
            '[id*="popup"]',
            '[class*="popup"]',
            'iframe[src*="ads"]',
            'iframe[src*="doubleclick"]',
            'iframe[src*="google"]',
            'script[src*="ads"]',
            'script[src*="analytics"]'
        ];
        
        for (var i = 0; i < adSelectors.length; i++) {
            var selector = adSelectors[i];
            try {
                var elements = document.querySelectorAll(selector);
                for (var j = 0; j < elements.length; j++) {
                    var element = elements[j];
                    if (element && element.parentNode) {
                        element.parentNode.removeChild(element);
                        console.log('[Popup Blocker] Removed ad element: ' + selector);
                    }
                }
            } catch (e) {
                // Selector not supported
            }
        }
    }
    
    // Helper function to check if domain is suspicious
    function isSuspiciousDomain(url) {
        if (!url) return false;
        
        var suspiciousDomains = [
            'bit.ly',
            'tinyurl.com',
            'short.link',
            'adf.ly',
            'linkvertise.com',
            'shorte.st',
            'ouo.io',
            'linkbucks.com',
            'adfly.com',
            'clicksfly.com',
            'lnk.co',
            'exe.io',
            'sub2unlock.com',
            'linksnappy.com',
            'rapidgator.net',
            'turbobit.net',
            'uploaded.net',
            'filejoker.net',
            'keep2share.cc',
            'nitroflare.com'
        ];
        
        for (var i = 0; i < suspiciousDomains.length; i++) {
            if (url.indexOf(suspiciousDomains[i]) > -1) {
                return true;
            }
        }
        
        return false;
    }
    
    // Helper function to check if URL is an ad network
    function isAdNetwork(url) {
        if (!url) return false;
        
        var adNetworks = [
            'doubleclick.net',
            'google-analytics.com',
            'googleadservices.com',
            'googlesyndication.com',
            'facebook.com/tr',
            'analytics.google.com',
            'ads.google.com',
            'pagead2.googlesyndication.com',
            'adservice.google.com',
            'googletagmanager.com',
            'amazon-adsystem.com',
            'criteo.com',
            'scorecardresearch.com',
            'quantserve.com',
            'addthis.com',
            'sharethis.com'
        ];
        
        for (var i = 0; i < adNetworks.length; i++) {
            if (url.indexOf(adNetworks[i]) > -1) {
                return true;
            }
        }
        
        return false;
    }
    
    // Initialize popup blocker
    function init() {
        console.log('[Popup Blocker] Initialized');
        
        // Remove ad elements on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', removeAdElements);
        } else {
            removeAdElements();
        }
        
        // Monitor for dynamically added ad elements
        if (window.MutationObserver) {
            var observer = new MutationObserver(function(mutations) {
                for (var i = 0; i < mutations.length; i++) {
                    var mutation = mutations[i];
                    if (mutation.addedNodes.length) {
                        removeAdElements();
                    }
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }
    
    // Start popup blocker
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose stats
    window.popupBlockerStats = {
        getBlockedCount: function() {
            return blockedCount;
        },
        reset: function() {
            blockedCount = 0;
        }
    };
    
    console.log('[Popup Blocker] Loaded and active');
})();
