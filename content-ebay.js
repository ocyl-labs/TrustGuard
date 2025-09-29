// content-ebay.js - eBay Page Injection Script
/**
 * TrustGuard eBay Content Script
 * Injects real-time fraud alerts directly on eBay listing pages
 * Users never leave eBay - alerts appear inline
 * 
 * Features:
 * - Real-time DOM monitoring
 * - Instant risk badges
 * - Expandable detail panels
 * - Profit opportunity highlights
 * - Safe alternative recommendations
 */

// ============================================================================
// 1. CONFIGURATION & CONSTANTS
// ============================================================================

const TRUSTGUARD_CONFIG = {
  API_URL: 'https://api.trustguard.com/v1',
  CACHE_DURATION: 300000, // 5 minutes
  DEBOUNCE_DELAY: 500, // ms
  MAX_RETRIES: 3,
  OVERLAY_Z_INDEX: 999999,
};

const RISK_LEVELS = {
  CRITICAL: { color: '#DC143C', label: 'High Risk', icon: '⚠️', score: 80 },
  HIGH: { color: '#FF6B35', label: 'Caution', icon: '⚠️', score: 60 },
  MEDIUM: { color: '#FFB200', label: 'Medium Risk', icon: '⚡', score: 40 },
  LOW: { color: '#059669', label: 'Low Risk', icon: '✓', score: 20 },
  SAFE: { color: '#10B981', label: 'Verified Safe', icon: '🛡️', score: 0 },
};

// ============================================================================
// 2. LISTING DATA EXTRACTOR
// ============================================================================

class EbayListingExtractor {
  constructor() {
    this.cache = new Map();
  }

  /**
   * Extract all relevant data from eBay listing page
   */
  extractListingData() {
    const data = {
      url: window.location.href,
      itemId: this.extractItemId(),
      title: this.extractTitle(),
      price: this.extractPrice(),
      sellerId: this.extractSellerId(),
      sellerName: this.extractSellerName(),
      sellerFeedback: this.extractSellerFeedback(),
      imageUrls: this.extractImages(),
      description: this.extractDescription(),
      condition: this.extractCondition(),
      shipping: this.extractShipping(),
      category: this.extractCategory(),
      timestamp: Date.now(),
    };

    return data;
  }

  extractItemId() {
    // eBay item ID from URL
    const match = window.location.href.match(/\/itm\/(\d+)/);
    return match ? match[1] : null;
  }

  extractTitle() {
    const titleEl = document.querySelector('h1.x-item-title__mainTitle') ||
                   document.querySelector('.it-ttl');
    return titleEl ? titleEl.textContent.trim() : '';
  }

  extractPrice() {
    const priceEl = document.querySelector('.x-price-primary span.ux-textspans') ||
                   document.querySelector('#prcIsum');
    if (!priceEl) return null;

    const priceText = priceEl.textContent.trim();
    const match = priceText.match(/[\d,]+\.?\d*/);
    return match ? parseFloat(match[0].replace(/,/g, '')) : null;
  }

  extractSellerId() {
    const sellerLink = document.querySelector('a[href*="/usr/"]');
    if (!sellerLink) return null;

    const match = sellerLink.href.match(/\/usr\/([^?]+)/);
    return match ? match[1] : null;
  }

  extractSellerName() {
    const sellerEl = document.querySelector('.x-sellercard-atf__info__about-seller a') ||
                    document.querySelector('#mbgLink');
    return sellerEl ? sellerEl.textContent.trim() : '';
  }

  extractSellerFeedback() {
    const feedbackEl = document.querySelector('.x-sellercard-atf__data--score') ||
                      document.querySelector('#si-fb');
    if (!feedbackEl) return null;

    const text = feedbackEl.textContent.trim();
    const match = text.match(/[\d,]+/);
    return match ? parseInt(match[0].replace(/,/g, '')) : null;
  }

  extractImages() {
    const images = [];
    const imgElements = document.querySelectorAll('.ux-image-carousel-item img');
    
    imgElements.forEach(img => {
      if (img.src && !img.src.includes('placeholder')) {
        images.push(img.src);
      }
    });

    return images.slice(0, 5); // First 5 images
  }

  extractDescription() {
    const descEl = document.querySelector('.x-item-description iframe');
    return descEl ? descEl.contentWindow.document.body.textContent.substring(0, 1000) : '';
  }

  extractCondition() {
    const condEl = document.querySelector('.x-item-condition-value__value') ||
                  document.querySelector('#vi-itm-cond');
    return condEl ? condEl.textContent.trim() : 'Unknown';
  }

  extractShipping() {
    const shippingEl = document.querySelector('.ux-labels-values--shipping .ux-textspans--BOLD');
    if (!shippingEl) return null;

    const text = shippingEl.textContent.trim();
    if (text.toLowerCase().includes('free')) return 0;

    const match = text.match(/[\d.]+/);
    return match ? parseFloat(match[0]) : null;
  }

  extractCategory() {
    const breadcrumbs = document.querySelectorAll('.breadcrumb a');
    if (breadcrumbs.length === 0) return 'Unknown';
    
    return Array.from(breadcrumbs).map(a => a.textContent.trim()).join(' > ');
  }
}

// ============================================================================
// 3. API CLIENT
// ============================================================================

class TrustGuardAPI {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.cache = new Map();
  }

  /**
   * Analyze listing for fraud and profit
   */
  async analyzeList(listingData) {
    // Check cache first
    const cacheKey = `listing_${listingData.itemId}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached && (Date.now() - cached.timestamp
