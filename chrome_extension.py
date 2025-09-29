// Extract title
      const titleSelectors = [
        'h1[data-testid="x-item-title"]',
        'h1#x-item-title',
        'h1.x-item-title',
        '.notranslate'
      ];
      
      for (const selector of titleSelectors) {
        const titleElement = document.querySelector(selector);
        if (titleElement && titleElement.textContent.trim()) {
          itemData.title = titleElement.textContent.trim();
          break;
        }
      }
      
      // Extract price
      const priceSelectors = [
        '[data-testid="notranslate"] .notranslate',
        '.notranslate span.notranslate',
        '#prcIsum',
        '.u-flL.condText span'
      ];
      
      for (const selector of priceSelectors) {
        const priceElement = document.querySelector(selector);
        if (priceElement) {
          const priceText = priceElement.textContent.replace(/[^\d.,]/g, '');
          const price = parseFloat(priceText.replace(',', ''));
          if (!isNaN(price) && price > 0) {
            itemData.price = price;
            break;
          }
        }
      }
      
      // Extract seller info
      const sellerElement = document.querySelector('[data-testid="seller-info"] a, .seller-persona a');
      if (sellerElement) {
        itemData.seller_info.username = sellerElement.textContent.trim();
      }
      
      const feedbackElement = document.querySelector('[data-testid="seller-feedback"]');
      if (feedbackElement) {
        const feedbackText = feedbackElement.textContent;
        const feedbackMatch = feedbackText.match(/(\d+(?:\.\d+)?%)/);
        if (feedbackMatch) {
          itemData.seller_info.feedback_pct = parseFloat(feedbackMatch[1]);
        }
      }
      
      // Extract description
      const descriptionElement = document.querySelector('#desc_div, [data-testid="item-description"]');
      if (descriptionElement) {
        itemData.description = descriptionElement.textContent.trim().substring(0, 1000);
      }
      
      // Extract photos
      const photoElements = document.querySelectorAll('#PicturePanel img, [data-testid="image-viewer"] img');
      itemData.photos = Array.from(photoElements)
        .map(img => img.src || img.dataset.src)
        .filter(src => src && src.includes('ebayimg'))
        .slice(0, 10);
      
      // Extract item specifics
      const specificsElements = document.querySelectorAll('[data-testid="item-specifics"] tr');
      specificsElements.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length === 2) {
          const key = cells[0].textContent.trim();
          const value = cells[1].textContent.trim();
          itemData.item_specifics[key] = value;
        }
      });
      
      return itemData;
      
    } catch (error) {
      console.error('Failed to extract item data:', error);
      return { title: '', price: 0, url: window.location.href };
    }
  }
  
  async loadPreferences() {
    try {
      const result = await chrome.storage.sync.get([
        'soundEnabled', 'soundVolume', 'overlayPosition', 'autoVerify'
      ]);
      
      this.soundEnabled = result.soundEnabled !== false; // Default true
      this.soundVolume = result.soundVolume || 0.7;
      this.overlayPosition = result.overlayPosition || 'top-right';
      this.autoVerify = result.autoVerify !== false; // Default true
      
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  }
  
  createOverlay() {
    // Remove existing overlay
    if (this.overlayElement) {
      this.overlayElement.remove();
    }
    
    // Create overlay container
    this.overlayElement = document.createElement('div');
    this.overlayElement.id = 'trustguard-overlay';
    this.overlayElement.innerHTML = this.getOverlayHTML();
    
    // Apply styles
    this.overlayElement.style.cssText = this.getOverlayCSS();
    
    // Add to page
    document.body.appendChild(this.overlayElement);
    
    // Add event listeners
    this.setupOverlayEvents();
    
    // Animate in
    this.animateOverlayIn();
  }
  
  getOverlayHTML() {
    return `
      <div class="tg-header">
        <div class="tg-brand">
          <div class="tg-shield">🛡️</div>
          <span class="tg-brand-text">TrustGuard</span>
        </div>
        <div class="tg-close" id="tg-close">×</div>
      </div>
      
      <div class="tg-content">
        <div class="tg-loading" id="tg-loading">
          <div class="tg-spinner"></div>
          <div class="tg-loading-text">Analyzing item safety...</div>
        </div>
        
        <div class="tg-results" id="tg-results" style="display: none;">
          <div class="tg-trust-score">
            <div class="tg-score-circle" id="tg-score-circle">
              <div class="tg-score-value" id="tg-score-value">--</div>
            </div>
            <div class="tg-decision" id="tg-decision">Analyzing...</div>
          </div>
          
          <div class="tg-metrics">
            <div class="tg-metric">
              <div class="tg-metric-label">Market Value</div>
              <div class="tg-metric-value" id="tg-market-value">$--</div>
            </div>
            <div class="tg-metric">
              <div class="tg-metric-label">Profit Potential</div>
              <div class="tg-metric-value" id="tg-profit">$--</div>
            </div>
            <div class="tg-metric">
              <div class="tg-metric-label">Time to Sell</div>
              <div class="tg-metric-value" id="tg-time-sell">-- days</div>
            </div>
            <div class="tg-metric">
              <div class="tg-metric-label">Risk Level</div>
              <div class="tg-metric-value" id="tg-risk-level">--</div>
            </div>
          </div>
          
          <div class="tg-signals" id="tg-signals">
            <!-- Trust signals will be populated here -->
          </div>
          
          <div class="tg-actions">
            <button class="tg-btn tg-btn-primary" id="tg-feedback-correct">Accurate</button>
            <button class="tg-btn tg-btn-secondary" id="tg-feedback-wrong">Incorrect</button>
            <button class="tg-btn tg-btn-secondary" id="tg-more-details">Details</button>
          </div>
        </div>
        
        <div class="tg-error" id="tg-error" style="display: none;">
          <div class="tg-error-icon">⚠️</div>
          <div class="tg-error-message" id="tg-error-message">Verification failed</div>
          <button class="tg-btn tg-btn-primary" id="tg-retry">Retry</button>
        </div>
      </div>
      
      <div class="tg-footer">
        <div class="tg-powered">Powered by AI • <span id="tg-processing-time">0ms</span></div>
      </div>
    `;
  }
  
  getOverlayCSS() {
    const position = this.getOverlayPosition();
    
    return `
      position: fixed;
      ${position.css}
      width: 320px;
      max-height: 600px;
      background: linear-gradient(145deg, #ffffff, #f8fafc);
      border: 2px solid #e2e8f0;
      border-radius: 16px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      line-height: 1.4;
      color: #1f2937;
      overflow: hidden;
      transform: translateY(20px) scale(0.95);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    `;
  }
  
  getOverlayPosition() {
    switch (this.overlayPosition) {
      case 'top-left':
        return { css: 'top: 100px; left: 20px;' };
      case 'top-right':
        return { css: 'top: 100px; right: 20px;' };
      case 'bottom-left':
        return { css: 'bottom: 20px; left: 20px;' };
      case 'bottom-right':
        return { css: 'bottom: 20px; right: 20px;' };
      default:
        return { css: 'top: 100px; right: 20px;' };
    }
  }
  
  setupOverlayEvents() {
    // Close button
    const closeBtn = this.overlayElement.querySelector('#tg-close');
    closeBtn?.addEventListener('click', () => this.hideOverlay());
    
    // Retry button
    const retryBtn = this.overlayElement.querySelector('#tg-retry');
    retryBtn?.addEventListener('click', () => this.verifyCurrentItem());
    
    // Feedback buttons
    const correctBtn = this.overlayElement.querySelector('#tg-feedback-correct');
    correctBtn?.addEventListener('click', () => this.sendFeedback(true));
    
    const wrongBtn = this.overlayElement.querySelector('#tg-feedback-wrong');
    wrongBtn?.addEventListener('click', () => this.sendFeedback(false));
    
    // More details button
    const detailsBtn = this.overlayElement.querySelector('#tg-more-details');
    detailsBtn?.addEventListener('click', () => this.showDetailedAnalysis());
    
    // Make draggable
    this.makeDraggable();
  }
  
  makeDraggable() {
    const header = this.overlayElement.querySelector('.tg-header');
    let isDragging = false;
    let startX, startY, startLeft, startTop;
    
    header.style.cursor = 'move';
    
    header.addEventListener('mousedown', (e) => {
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      
      const rect = this.overlayElement.getBoundingClientRect();
      startLeft = rect.left;
      startTop = rect.top;
      
      e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const newLeft = startLeft + (e.clientX - startX);
      const newTop = startTop + (e.clientY - startY);
      
      // Keep within viewport bounds
      const maxLeft = window.innerWidth - this.overlayElement.offsetWidth;
      const maxTop = window.innerHeight - this.overlayElement.offsetHeight;
      
      this.overlayElement.style.left = `${Math.max(0, Math.min(newLeft, maxLeft))}px`;
      this.overlayElement.style.top = `${Math.max(0, Math.min(newTop, maxTop))}px`;
      this.overlayElement.style.right = 'auto';
      this.overlayElement.style.bottom = 'auto';
    });
    
    document.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }
  
  animateOverlayIn() {
    // Trigger reflow
    this.overlayElement.offsetHeight;
    
    // Animate in
    this.overlayElement.style.transform = 'translateY(0) scale(1)';
    this.overlayElement.style.opacity = '1';
  }
  
  hideOverlay() {
    this.overlayElement.style.transform = 'translateY(-20px) scale(0.95)';
    this.overlayElement.style.opacity = '0';
    
    setTimeout(() => {
      if (this.overlayElement && this.overlayElement.parentNode) {
        this.overlayElement.remove();
        this.overlayElement = null;
      }
    }, 300);
  }
  
  async verifyCurrentItem() {
    if (!this.currentItemData.title) {
      this.showError('No item data found on this page');
      return;
    }
    
    // Show loading state
    this.showLoading();
    
    try {
      const startTime = performance.now();
      
      // Send verification request to background script
      const response = await new Promise((resolve) => {
        chrome.runtime.sendMessage({
          action: 'verify_item',
          data: this.currentItemData
        }, resolve);
      });
      
      const processingTime = performance.now() - startTime;
      
      if (!response.success) {
        throw new Error(response.error || 'Verification failed');
      }
      
      // Display results
      this.displayResults(response.data, processingTime);
      
      // Play success sound
      if (this.soundEnabled) {
        this.playSound(response.data.trust_score >= 70 ? 'success' : 'warning');
      }
      
    } catch (error) {
      console.error('Verification error:', error);
      this.showError(error.message);
      
      // Play error sound
      if (this.soundEnabled) {
        this.playSound('error');
      }
    }
  }
  
  showLoading() {
    const loading = this.overlayElement.querySelector('#tg-loading');
    const results = this.overlayElement.querySelector('#tg-results');
    const error = this.overlayElement.querySelector('#tg-error');
    
    loading.style.display = 'block';
    results.style.display = 'none';
    error.style.display = 'none';
  }
  
  displayResults(data, processingTime) {
    const loading = this.overlayElement.querySelector('#tg-loading');
    const results = this.overlayElement.querySelector('#tg-results');
    const error = this.overlayElement.querySelector('#tg-error');
    
    loading.style.display = 'none';
    results.style.display = 'block';
    error.style.display = 'none';
    
    // Update trust score
    const scoreValue = this.overlayElement.querySelector('#tg-score-value');
    const scoreCircle = this.overlayElement.querySelector('#tg-score-circle');
    const decision = this.overlayElement.querySelector('#tg-decision');
    
    scoreValue.textContent = Math.round(data.trust_score || 0);
    
    // Color code the score
    const score = data.trust_score || 0;
    let scoreColor, decisionText, decisionEmoji;
    
    if (score >= 80) {
      scoreColor = '#10b981'; // Green
      decisionText = 'SAFE TO BUY';
      decisionEmoji = '✅';
    } else if (score >= 60) {
      scoreColor = '#f59e0b'; // Yellow
      decisionText = 'PROCEED CAREFULLY';
      decisionEmoji = '⚠️';
    } else {
      scoreColor = '#ef4444'; // Red
      decisionText = 'HIGH RISK - AVOID';
      decisionEmoji = '❌';
    }
    
    scoreCircle.style.borderColor = scoreColor;
    scoreValue.style.color = scoreColor;
    decision.innerHTML = `${decisionEmoji} ${decisionText}`;
    decision.style.color = scoreColor;
    
    // Update metrics
    this.overlayElement.querySelector('#tg-market-value').textContent = 
      data.market_value ? `${data.market_value}` : 'N/A';
    this.overlayElement.querySelector('#tg-profit').textContent = 
      data.profit_potential ? `${data.profit_potential}` : 'N/A';
    this.overlayElement.querySelector('#tg-time-sell').textContent = 
      data.time_to_sell ? `${data.time_to_sell} days` : 'N/A';
    this.overlayElement.querySelector('#tg-risk-level').textContent = 
      data.risk_level || 'Unknown';
    
    // Update trust signals
    this.displayTrustSignals(data.trust_signals || []);
    
    // Update processing time
    const totalTime = (data.extension_processing_time || 0) + processingTime;
    this.overlayElement.querySelector('#tg-processing-time').textContent = 
      `${Math.round(totalTime)}ms`;
    
    // Store current results for feedback
    this.currentResults = data;
  }
  
  displayTrustSignals(signals) {
    const signalsContainer = this.overlayElement.querySelector('#tg-signals');
    
    if (!signals.length) {
      signalsContainer.innerHTML = '<div class="tg-no-signals">No specific concerns identified</div>';
      return;
    }
    
    const signalsHTML = signals.slice(0, 4).map(signal => {
      const emoji = signal.value > 0 ? '✅' : signal.value < -0.5 ? '❌' : '⚠️';
      return `
        <div class="tg-signal">
          <span class="tg-signal-icon">${emoji}</span>
          <span class="tg-signal-text">${signal.feature}: ${signal.explanation || 'OK'}</span>
        </div>
      `;
    }).join('');
    
    signalsContainer.innerHTML = signalsHTML;
  }
  
  showError(message) {
    const loading = this.overlayElement.querySelector('#tg-loading');
    const results = this.overlayElement.querySelector('#tg-results');
    const error = this.overlayElement.querySelector('#tg-error');
    const errorMessage = this.overlayElement.querySelector('#tg-error-message');
    
    loading.style.display = 'none';
    results.style.display = 'none';
    error.style.display = 'block';
    
    errorMessage.textContent = message;
  }
  
  async sendFeedback(isCorrect) {
    if (!this.currentResults) return;
    
    try {
      await chrome.runtime.sendMessage({
        action: 'track_usage',
        data: {
          action: 'feedback',
          item_id: this.currentItemData.url,
          feedback: isCorrect ? 'correct' : 'incorrect',
          trust_score: this.currentResults.trust_score,
          decision: this.currentResults.decision
        }
      });
      
      // Show feedback confirmation
      const button = isCorrect ? 
        this.overlayElement.querySelector('#tg-feedback-correct') :
        this.overlayElement.querySelector('#tg-feedback-wrong');
      
      const originalText = button.textContent;
      button.textContent = 'Thanks! ✓';
      button.disabled = true;
      
      setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
      }, 2000);
      
    } catch (error) {
      console.error('Feedback error:', error);
    }
  }
  
  showDetailedAnalysis() {
    if (!this.currentResults) return;
    
    // Open detailed analysis in popup
    chrome.runtime.sendMessage({
      action: 'open_details',
      data: this.currentResults
    });
  }
  
  async playSound(soundName) {
    try {
      await chrome.runtime.sendMessage({
        action: 'play_sound',
        soundName: soundName
      });
    } catch (error) {
      // Ignore sound errors
    }
  }
  
  handleMessage(request, sender, sendResponse) {
    switch (request.action) {
      case 'play_sound':
        this.playAudioFile(request.soundName, request.volume);
        break;
      case 'refresh_verification':
        this.verifyCurrentItem();
        break;
    }
  }
  
  playAudioFile(soundName, volume = 0.7) {
    // Create and play audio element
    const audio = new Audio();
    audio.volume = volume;
    
    // Map sound names to files
    const soundMap = {
      'success': 'sounds/success.mp3',
      'warning': 'sounds/warning.mp3',
      'error': 'sounds/error.mp3'
    };
    
    const soundFile = soundMap[soundName];
    if (soundFile) {
      audio.src = chrome.runtime.getURL(soundFile);
      audio.play().catch(() => {
        // Ignore play errors (user may not have interacted with page)
      });
    }
  }
}

// Initialize content script when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new TrustGuardContent());
} else {
  new TrustGuardContent();
}

// ===== content.css =====
/* TrustGuard Overlay Styles */
#trustguard-overlay * {
  box-sizing: border-box !important;
  margin: 0 !important;
  padding: 0 !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

#trustguard-overlay {
  all: initial !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.tg-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 12px 16px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  border-radius: 14px 14px 0 0 !important;
}

.tg-brand {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

.tg-shield {
  font-size: 18px !important;
}

.tg-brand-text {
  font-weight: 700 !important;
  font-size: 16px !important;
}

.tg-close {
  width: 24px !important;
  height: 24px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: rgba(255, 255, 255, 0.2) !important;
  border-radius: 50% !important;
  cursor: pointer !important;
  font-size: 18px !important;
  font-weight: bold !important;
  transition: background 0.2s !important;
}

.tg-close:hover {
  background: rgba(255, 255, 255, 0.3) !important;
}

.tg-content {
  padding: 20px !important;
}

/* Loading State */
.tg-loading {
  text-align: center !important;
  padding: 20px !important;
}

.tg-spinner {
  width: 32px !important;
  height: 32px !important;
  border: 3px solid #e2e8f0 !important;
  border-top: 3px solid #667eea !important;
  border-radius: 50% !important;
  animation: tg-spin 1s linear infinite !important;
  margin: 0 auto 12px !important;
}

.tg-loading-text {
  color: #6b7280 !important;
  font-size: 14px !important;
}

@keyframes tg-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Results State */
.tg-trust-score {
  text-align: center !important;
  margin-bottom: 20px !important;
}

.tg-score-circle {
  width: 80px !important;
  height: 80px !important;
  border: 4px solid #e2e8f0 !important;
  border-radius: 50% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin: 0 auto 12px !important;
  transition: border-color 0.3s !important;
}

.tg-score-value {
  font-size: 24px !important;
  font-weight: 800 !important;
  color: #1f2937 !important;
}

.tg-decision {
  font-weight: 600 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

.tg-metrics {
  display: grid !important;
  grid-template-columns: 1fr 1fr !important;
  gap: 12px !important;
  margin-bottom: 20px !important;
}

.tg-metric {
  background: #f8fafc !important;
  padding: 12px !important;
  border-radius: 8px !important;
  text-align: center !important;
}

.tg-metric-label {
  font-size: 11px !important;
  color: #6b7280 !important;
  font-weight: 600 !important;
  margin-bottom: 4px !important;
}

.tg-metric-value {
  font-size: 14px !important;
  font-weight: 700 !important;
  color: #1f2937 !important;
}

.tg-signals {
  margin-bottom: 20px !important;
}

.tg-signal {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  margin-bottom: 8px !important;
  font-size: 12px !important;
}

.tg-signal-icon {
  width: 16px !important;
  text-align: center !important;
}

.tg-signal-text {
  color: #4b5563 !important;
  flex: 1 !important;
}

.tg-no-signals {
  text-align: center !important;
  color: #6b7280 !important;
  font-size: 12px !important;
  font-style: italic !important;
}

.tg-actions {
  display: flex !important;
  gap: 8px !important;
}

.tg-btn {
  flex: 1 !important;
  padding: 8px 12px !important;
  border: none !important;
  border-radius: 6px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.2s !important;
}

.tg-btn-primary {
  background: #667eea !important;
  color: white !important;
}

.tg-btn-primary:hover {
  background: #5a6fd8 !important;
  transform: translateY(-1px) !important;
}

.tg-btn-secondary {
  background: #f3f4f6 !important;
  color: #374151 !important;
  border: 1px solid #d1d5db !important;
}

.tg-btn-secondary:hover {
  background: #e5e7eb !important;
}

.tg-btn:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
}

/* Error State */
.tg-error {
  text-align: center !important;
  padding: 20px !important;
}

.tg-error-icon {
  font-size: 32px !important;
  margin-bottom: 12px !important;
}

.tg-error-message {
  color: #ef4444 !important;
  font-weight: 600 !important;
  margin-bottom: 16px !important;
}

.tg-footer {
  padding: 12px 16px !important;
  border-top: 1px solid #e5e7eb !important;
  background: #f8fafc !important;
  border-radius: 0 0 14px 14px !important;
}

.tg-powered {
  text-align: center !important;
  font-size: 10px !important;
  color: #6b7280 !important;
}

/* Responsive */
@media (max-width: 768px) {
  #trustguard-overlay {
    width: calc(100vw - 20px) !important;
    left: 10px !important;
    right: 10px !important;
  }
  
  .tg-metrics {
    grid-template-columns: 1fr !important;
  }
}

// ===== popup.html =====
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      width: 350px;
      height: 500px;
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    
    .popup-header {
      padding: 20px;
      text-align: center;
      background: rgba(255, 255, 255, 0.1);
    }
    
    .popup-content {
      padding: 20px;
      background: white;
      color: #1f2937;
      flex: 1;
      overflow-y: auto;
    }
    
    .user-status {
      text-align: center;
      margin-bottom: 20px;
    }
    
    .feature-list {
      list-style: none;
      padding: 0;
    }
    
    .feature-list li {
      padding: 8px 0;
      border-bottom: 1px solid #e5e7eb;
    }
    
    .btn {
      width: 100%;
      padding: 12px;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      margin-bottom: 8px;
      transition: all 0.2s;
    }
    
    .btn-primary {
      background: #667eea;
      color: white;
    }
    
    .btn-secondary {
      background: #f3f4f6;
      color: #374151;
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin: 20px 0;
    }
    
    .stat-card {
      background: #f8fafc;
      padding: 12px;
      border-radius: 8px;
      text-align: center;
    }
    
    .stat-value {
      font-size: 20px;
      font-weight: 700;
      color: #667eea;
    }
    
    .stat-label {
      font-size: 11px;
      color: #6b7280;
      margin-top: 4px;
    }
  </style>
</head>
<body>
  <div class="popup-header">
    <h2>🛡️ TrustGuard</h2>
    <p>eBay Intelligence & Protection</p>
  </div>
  
  <div class="popup-content">
    <div class="user-status" id="userStatus">
      <!-- Will be populated by popup.js -->
    </div>
    
    <div class="stats-grid" id="statsGrid">
      <!-- Will be populated by popup.js -->
    </div>
    
    <div class="quick-actions">
      <button class="btn btn-primary" id="scanCurrentPage">
        🔍 Scan Current Page
      </button>
      <button class="btn btn-secondary" id="openDashboard">
        📊 Open Dashboard
      </button>
      <button class="btn btn-secondary" id="openSettings">
        ⚙️ Settings
      </button>
    </div>
    
    <div class="feature-highlights">
      <h3>Protection Features</h3>
      <ul class="feature-list">
        <li>✅ Instant scam detection</li>
        <li>📈 Real-time market analysis</li>
        <li>💰 Profit potential calculation</li>
        <li>🔄 Cross-platform arbitrage alerts</li>
        <li>🎯 AI-powered seller verification</li>
      </ul>
    </div>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>

// ===== popup.js =====
class TrustGuardPopup {
  constructor() {
    this.initialize();
  }
  
  async initialize() {
    await this.loadUserStatus();
    await this.loadUserStats();
    this.setupEventListeners();
  }
  
  async loadUserStatus() {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'get_user_status'
      });
      
      const userStatusElement = document.getElementById('userStatus');
      
      if (response.success && response.data.authenticated) {
        const user = response.data.user;
        userStatusElement.innerHTML = `
          <div style="background: #ecfdf5; color: #065f46; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
            <div style="font-weight: 600;">Welcome back, ${user.first_name || 'User'}!</div>
            <div style="font-size: 12px; opacity: 0.8;">
              ${user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1)} Plan
            </div>
          </div>
        `;
      } else {
        userStatusElement.innerHTML = `
          <div style="background: #fef3c7; color: #92400e; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
            <div style="font-weight: 600;">Sign in for full protection</div>
            <div style="font-size: 12px; margin-top: 8px;">
              <button class="btn btn-primary" id="signInBtn" style="font-size: 12px; padding: 6px 12px;">
                Sign In / Register
              </button>
            </div>
          </div>
        `;
        
        // Add sign-in event listener
        document.getElementById('signInBtn')?.addEventListener('click', () => {
          chrome.tabs.create({ url: 'https://app.trustguard.com/auth/login' });
        });
      }
      
    } catch (error) {
      console.error('Failed to load user status:', error);
    }
  }
  
  async loadUserStats() {
    try {
      // Get usage stats from storage
      const result = await chrome.storage.local.get(['usage_stats']);
      const stats = result.usage_stats || {};
      
      // Calculate totals
      let totalVerifications = 0;
      let totalSavings = 0;
      let riskItemsFound = 0;
      let avgResponseTime = 0;
      
      Object.values(stats).forEach(dayStats => {
        dayStats.forEach(stat => {
          if (stat.action === 'verification') {
            totalVerifications++;
            if (stat.trust_score < 50) riskItemsFound++;
            if (stat.processing_time) {
              avgResponseTime += stat.processing_time;
            }
          }
        });
      });
      
      if (totalVerifications > 0) {
        avgResponseTime = Math.round(avgResponseTime / totalVerifications);
      }
      
      const statsGridElement = document.getElementById('statsGrid');
      statsGridElement.innerHTML = `
        <div class="stat-card">
          <div class="stat-value">${totalVerifications}</div>
          <div class="stat-label">Items Verified</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${riskItemsFound}</div>
          <div class="stat-label">Risks Detected</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${avgResponseTime}ms</div>
          <div class="stat-label">Avg Response</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${totalSavings}</div>
          <div class="stat-label">Est. Savings</div>
        </div>
      `;
      
    } catch (error) {
      console.error('Failed to load user stats:', error);
    }
  }
  
  setupEventListeners() {
    // Scan current page
    document.getElementById('scanCurrentPage')?.addEventListener('click', async () => {
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!activeTab.url.includes('ebay.com/itm/')) {
        alert('Please navigate to an eBay item page to scan.');
        return;
      }
      
      // Trigger content script verification
      chrome.tabs.sendMessage(activeTab.id, { action: 'refresh_verification' });
      window.close();
    });
    
    // Open dashboard
    document.getElementById('openDashboard')?.addEventListener('click', () => {
      chrome.tabs.create({ url: 'https://app.trustguard.com/dashboard' });
    });
    
    // Open settings
    document.getElementById('openSettings')?.addEventListener('click', () => {
      chrome.runtime.openOptionsPage();
    });
  }
}

// Initialize popup
new TrustGuardPopup();

// ===== options.html =====
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>TrustGuard Settings</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
      background: #f8fafc;
    }
    
    .header {
      text-align: center;
      margin-bottom: 40px;
      padding: 20px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .section {
      background: white;
      padding: 24px;
      margin-bottom: 20px;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .section h3 {
      margin-bottom: 16px;
      color: #1f2937;
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 8px;
    }
    
    .setting {
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .setting-label {
      font-weight: 500;
      color: #374151;
    }
    
    .setting-description {
      font-size: 13px;
      color: #6b7280;
      margin-top: 4px;
    }
    
    .toggle {
      position: relative;
      width: 48px;
      height: 24px;
      background: #d1d5db;
      border-radius: 12px;
      cursor: pointer;
      transition: background 0.2s;
    }
    
    .toggle.active {
      background: #10b981;
    }
    
    .toggle::after {
      content: '';
      position: absolute;
      width: 20px;
      height: 20px;
      background: white;
      border-radius: 50%;
      top: 2px;
      left: 2px;
      transition: transform 0.2s;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .toggle.active::after {
      transform: translateX(24px);
    }
    
    select, input[type="range"] {
      padding: 8px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
    }
    
    .btn {
      background: #667eea;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    
    .btn:hover {
      background: #5a6fd8;
    }
    
    .btn-secondary {
      background: #f3f4f6;
      color: #374151;
    }
    
    .btn-secondary:hover {
      background: #e5e7eb;
    }
    
    .save-indicator {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #10b981;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 600;
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s;
    }
    
    .save-indicator.show {
      opacity: 1;
      transform: translateY(0);
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🛡️ TrustGuard Settings</h1>
    <p>Customize your eBay protection experience</p>
  </div>

  <div class="section">
    <h3>🔊 Audio & Notifications</h3>
    
    <div class="setting">
      <div>
        <div class="setting-label">Sound Effects</div>
        <div class="setting-description">Play sounds for verification results</div>
      </div>
      <div class="toggle" id="soundEnabled"></div>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Volume Level</div>
        <div class="setting-description">Adjust sound volume</div>
      </div>
      <input type="range" id="soundVolume" min="0" max="1" step="0.1" value="0.7">
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Desktop Notifications</div>
        <div class="setting-description">Show notifications for high-risk items</div>
      </div>
      <div class="toggle" id="desktopNotifications"></div>
    </div>
  </div>

  <div class="section">
    <h3>🎯 Verification Behavior</h3>
    
    <div class="setting">
      <div>
        <div class="setting-label">Auto-Verify Items</div>
        <div class="setting-description">Automatically verify when visiting eBay listings</div>
      </div>
      <div class="toggle active" id="autoVerify"></div>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Overlay Position</div>
        <div class="setting-description">Choose where to display the verification overlay</div>
      </div>
      <select id="overlayPosition">
        <option value="top-right">Top Right</option>
        <option value="top-left">Top Left</option>
        <option value="bottom-right">Bottom Right</option>
        <option value="bottom-left">Bottom Left</option>
      </select>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Risk Threshold</div>
        <div class="setting-description">Show warnings for items below this trust score</div>
      </div>
      <select id="riskThreshold">
        <option value="30">High (30)</option>
        <option value="50" selected>Medium (50)</option>
        <option value="70">Low (70)</option>
      </select>
    </div>
  </div>

  <div class="section">
    <h3>🔧 Advanced Settings</h3>
    
    <div class="setting">
      <div>
        <div class="setting-label">API Endpoint</div>
        <div class="setting-description">Choose between production and development API</div>
      </div>
      <select id="apiEndpoint">
        <option value="https://api.trustguard.com">Production</option>
        <option value="http://localhost:5000">Local Development</option>
      </select>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Debug Mode</div>
        <div class="setting-description">Enable detailed logging for troubleshooting</div>
      </div>
      <div class="toggle" id="debugMode"></div>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Usage Analytics</div>
        <div class="setting-description">Help improve TrustGuard by sharing anonymous usage data</div>
      </div>
      <div class="toggle active" id="usageAnalytics"></div>
    </div>
  </div>

  <div class="section">
    <h3>📊 Data & Privacy</h3>
    
    <div class="setting">
      <div>
        <div class="setting-label">Clear Usage Data</div>
        <div class="setting-description">Remove all stored verification history</div>
      </div>
      <button class="btn btn-secondary" id="clearData">Clear Data</button>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Export Data</div>
        <div class="setting-description">Download your verification history</div>
      </div>
      <button class="btn btn-secondary" id="exportData">Export</button>
    </div>
    
    <div class="setting">
      <div>
        <div class="setting-label">Reset Settings</div>
        <div class="setting-description">Restore all settings to default values</div>
      </div>
      <button class="btn btn-secondary" id="resetSettings">Reset</button>
    </div>
  </div>

  <div class="section" style="text-align: center;">
    <button class="btn" id="saveSettings">Save All Settings</button>
    <p style="margin-top: 12px; font-size: 13px; color: #6b7280;">
      Settings are automatically saved as you change them
    </p>
  </div>

  <div class="save-indicator" id="saveIndicator">
    ✓ Settings saved
  </div>

  <script src="options.js"></script>
</body>
</html>

// ===== options.js =====
class TrustGuardOptions {
  constructor() {
    this.settings = {};
    this.initialize();
  }
  
  async initialize() {
    await this.loadSettings();
    this.setupEventListeners();
    this.updateUI();
  }
  
  async loadSettings() {
    const result = await chrome.storage.sync.get([
      'soundEnabled',
      'soundVolume', 
      'desktopNotifications',
      'autoVerify',
      'overlayPosition',
      'riskThreshold',
      'apiEndpoint',
      'debugMode',
      'usageAnalytics'
    ]);
    
    // Set defaults
    this.settings = {
      soundEnabled: result.soundEnabled !== false,
      soundVolume: result.soundVolume || 0.7,
      desktopNotifications: result.desktopNotifications !== false,
      autoVerify: result.autoVerify !== false,
      overlayPosition: result.overlayPosition || 'top-right',
      riskThreshold: result.riskThreshold || 50,
      apiEndpoint: result.apiEndpoint || 'https://api.trustguard.com',
      debugMode: result.debugMode || false,
      usageAnalytics: result.usageAnalytics !== false
    };
  }
  
  updateUI() {
    // Update toggles
    document.getElementById('soundEnabled').classList.toggle('active', this.settings.soundEnabled);
    document.getElementById('desktopNotifications').classList.toggle('active', this.settings.desktopNotifications);
    document.getElementById('autoVerify').classList.toggle('active', this.settings.autoVerify);
    document.getElementById('debugMode').classList.toggle('active', this.settings.debugMode);
    document.getElementById('usageAnalytics').classList.toggle('active', this.settings.usageAnalytics);
    
    // Update other controls
    document.getElementById('soundVolume').value = this.settings.soundVolume;
    document.getElementById('overlayPosition').value = this.settings.overlayPosition;
    document.getElementById('riskThreshold').value = this.settings.riskThreshold;
    document.getElementById('apiEndpoint').value = this.settings.apiEndpoint;
  }
  
  setupEventListeners() {
    // Toggle switches
    document.querySelectorAll('.toggle').forEach(toggle => {
      toggle.addEventListener('click', (e) => {
        const setting = e.target.id;
        this.settings[setting] = !this.settings[setting];
        e.target.classList.toggle('active', this.settings[setting]);
        this.saveSettings();
      });
    });
    
    // Range and select inputs
    ['soundVolume', 'overlayPosition', 'riskThreshold', 'apiEndpoint'].forEach(id => {
      document.getElementById(id).addEventListener('change', (e) => {
        const value = e.target.type === 'range' ? parseFloat(e.target.value) : e.target.value;
        this.settings[id] = value;
        this.saveSettings();
      });
    });
    
    // Action buttons
    document.getElementById('clearData').addEventListener('click', this.clearData.bind(this));
    document.getElementById('exportData').addEventListener('click', this.exportData.bind(this));
    document.getElementById('resetSettings').addEventListener('click', this.resetSettings.bind(this));
    document.getElementById('saveSettings').addEventListener('click', this.saveSettings.bind(this));
  }
  
  async saveSettings() {
    await chrome.storage.sync.set(this.settings);
    this.showSaveIndicator();
  }
  
  showSaveIndicator() {
    const indicator = document.getElementById('saveIndicator');
    indicator.classList.add('show');
    setTimeout(() => {
      indicator.classList.remove('show');
    }, 2000);
  }
  
  async clearData() {
    if (confirm('Are you sure you want to clear all verification data? This cannot be undone.')) {
      await chrome.storage.local.clear();
      alert('All data has been cleared.');
    }
  }
  
  async exportData() {
    try {
      const data = await chrome.storage.local.get();
      const exportData = {
        settings: this.settings,
        usage_data: data,
        export_date: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `trustguard-data-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Failed to export data: ' + error.message);
    }
  }
  
  async resetSettings() {
    if (confirm('Are you sure you want to reset all settings to default values?')) {
      await chrome.storage.sync.clear();
      await this.loadSettings();
      this.updateUI();
      this.showSaveIndicator();
    }
  }
}

// Initialize options page
new TrustGuardOptions();

// ===== Package.json for build process =====
{
  "name": "trustguard-extension",
  "version": "2.1.0",
  "description": "Build tools for TrustGuard Chrome Extension",
  "scripts": {
    "build": "node build.js",
    "package": "node package.js",
    "test": "node test.js"
  },
  "devDependencies": {
    "archiver": "^5.3.0",
    "fs-extra": "^10.1.0"
  }
}

// ===== build.js =====
const fs = require('fs-extra');
const path = require('path');
const archiver = require('archiver');

async function buildExtension() {
  console.log('🔨 Building TrustGuard Chrome Extension...');
  
  const distDir = path.join(__dirname, 'dist');
  const srcDir = path.join(__dirname, 'src');
  
  // Clean and create dist directory
  await fs.remove(distDir);
  await fs.ensureDir(distDir);
  
  // Copy all source files
  await fs.copy(srcDir, distDir);
  
  // Generate icons if they don't exist
  await generateIcons(distDir);
  
  // Create zip file for Chrome Web Store
  await createZipFile(distDir);
  
  console.log('✅ Extension build complete!');
}

async function generateIcons(distDir) {
  const iconsDir = path.join(distDir, 'icons');
  await fs.ensureDir(iconsDir);
  
  // For now, create placeholder icon files
  // In production, you'd use actual icon images
  const sizes = [16, 32, 48, 128];
  for (const size of sizes) {
    const iconPath = path.join(iconsDir, `icon${size}.png`);
    if (!await fs.pathExists(iconPath)) {
      // Create a simple colored square as placeholder
      const canvas = `<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <rect width="${size}" height="${size}" fill="#667eea"/>
        <text x="50%" y="50%" text-anchor="middle" dy=".35em" fill="white" font-size="${size/3}" font-family="Arial">🛡️</text>
      </svg>`;
      await fs.writeFile(iconPath.replace('.png', '.svg'), canvas);
    }
  }
}

async function createZipFile(distDir) {
  const zipPath = path.join(__dirname, 'trustguard-extension-v2.1.0.zip');
  const output = fs.createWriteStream(zipPath);
  const archive = archiver('zip', { zlib: { level: 9 } });
  
  return new Promise((resolve, reject) => {
    output.on('close', () => {
      console.log(`📦 Extension packaged: ${zipPath} (${archive.pointer()} bytes)`);
      resolve();
    });
    
    archive.on('error', reject);
    archive.pipe(output);
    archive.directory(distDir, false);
    archive.finalize();
  });
}

// Run build if called directly
if (require.main === module) {
  buildExtension().catch(console.error);
}

module.exports = { buildExtension };// Complete Chrome Extension Package
// File structure:
// manifest.json, background.js, content.js, popup.html, popup.js, options.html, options.js

// ===== manifest.json =====
{
  "manifest_version": 3,
  "name": "TrustGuard - eBay Intelligence & Protection",
  "version": "2.1.0",
  "description": "AI-powered eBay verification, profit analysis, and scam protection. Get instant trust scores, market insights, and arbitrage opportunities.",
  
  "permissions": [
    "activeTab",
    "storage",
    "notifications",
    "scripting"
  ],
  
  "host_permissions": [
    "https://*.ebay.com/*",
    "https://*.ebay.co.uk/*",
    "https://*.ebay.de/*",
    "https://*.ebay.fr/*",
    "https://api.trustguard.com/*",
    "http://localhost:5000/*"
  ],
  
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  
  "content_scripts": [
    {
      "matches": [
        "https://*.ebay.com/itm/*",
        "https://*.ebay.co.uk/itm/*",
        "https://*.ebay.de/itm/*"
      ],
      "js": ["content.js"],
      "css": ["content.css"],
      "run_at": "document_idle"
    }
  ],
  
  "action": {
    "default_popup": "popup.html",
    "default_title": "TrustGuard - eBay Intelligence",
    "default_icon": {
      "16": "icons/icon16.png",
      "32": "icons/icon32.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  
  "options_page": "options.html",
  
  "web_accessible_resources": [
    {
      "resources": ["sounds/*.mp3", "images/*.png"],
      "matches": ["https://*.ebay.com/*"]
    }
  ]
}

// ===== background.js =====
// Service worker for Chrome Extension
class TrustGuardBackground {
  constructor() {
    this.apiBaseUrl = 'https://api.trustguard.com';
    this.localApiUrl = 'http://localhost:5000';
    this.authToken = null;
    
    this.initialize();
  }
  
  async initialize() {
    // Load stored auth token
    const result = await chrome.storage.local.get(['authToken', 'apiBaseUrl']);
    this.authToken = result.authToken;
    if (result.apiBaseUrl) {
      this.apiBaseUrl = result.apiBaseUrl;
    }
    
    // Set up message listeners
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
    
    // Set up installation/update handlers
    chrome.runtime.onInstalled.addListener(this.handleInstall.bind(this));
    
    console.log('🛡️ TrustGuard background service initialized');
  }
  
  async handleInstall(details) {
    if (details.reason === 'install') {
      // First time installation
      await this.showWelcomeNotification();
      chrome.tabs.create({ url: 'https://trustguard.com/welcome' });
    } else if (details.reason === 'update') {
      // Extension updated
      await this.showUpdateNotification(details.previousVersion);
    }
  }
  
  async handleMessage(request, sender, sendResponse) {
    try {
      switch (request.action) {
        case 'verify_item':
          return await this.verifyItem(request.data, sendResponse);
        case 'authenticate':
          return await this.authenticate(request.credentials, sendResponse);
        case 'get_user_status':
          return await this.getUserStatus(sendResponse);
        case 'track_usage':
          return await this.trackUsage(request.data, sendResponse);
        case 'play_sound':
          return await this.playSound(request.soundName, sendResponse);
        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Background script error:', error);
      sendResponse({ success: false, error: error.message });
    }
    
    return true; // Keep message channel open for async response
  }
  
  async verifyItem(itemData, sendResponse) {
    const startTime = performance.now();
    
    try {
      // Try production API first, fallback to local
      let apiUrl = this.apiBaseUrl;
      let response = await this.makeApiCall(`${apiUrl}/api/verify-instant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.authToken ? `Bearer ${this.authToken}` : undefined
        },
        body: JSON.stringify(itemData)
      });
      
      // If production fails, try local development server
      if (!response.ok && apiUrl !== this.localApiUrl) {
        console.log('Production API failed, trying local...');
        apiUrl = this.localApiUrl;
        response = await this.makeApiCall(`${apiUrl}/verify-instant`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(itemData)
        });
      }
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const result = await response.json();
      const processingTime = performance.now() - startTime;
      
      // Add performance metrics
      result.extension_processing_time = Math.round(processingTime);
      result.api_url_used = apiUrl;
      
      // Track successful verification
      await this.trackUsage({
        action: 'verification',
        success: true,
        processing_time: processingTime,
        trust_score: result.trust_score
      });
      
      // Show notification for high-risk items
      if (result.risk_level === 'HIGH' || result.trust_score < 30) {
        await this.showRiskNotification(result);
      }
      
      sendResponse({ success: true, data: result });
      
    } catch (error) {
      console.error('Verification error:', error);
      
      // Track failed verification
      await this.trackUsage({
        action: 'verification',
        success: false,
        error: error.message
      });
      
      sendResponse({ 
        success: false, 
        error: error.message,
        fallback: this.getFallbackResponse(itemData)
      });
    }
  }
  
  async authenticate(credentials, sendResponse) {
    try {
      const response = await this.makeApiCall(`${this.apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Authentication failed');
      }
      
      const result = await response.json();
      
      // Store auth token
      this.authToken = result.access_token;
      await chrome.storage.local.set({ 
        authToken: result.access_token,
        refreshToken: result.refresh_token,
        user: result.user
      });
      
      sendResponse({ success: true, data: result });
      
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  }
  
  async getUserStatus(sendResponse) {
    try {
      const stored = await chrome.storage.local.get(['user', 'authToken']);
      
      if (!stored.user || !stored.authToken) {
        sendResponse({ success: true, data: { authenticated: false } });
        return;
      }
      
      // Verify token is still valid
      const response = await this.makeApiCall(`${this.apiBaseUrl}/auth/profile`, {
        headers: { 'Authorization': `Bearer ${stored.authToken}` }
      });
      
      if (!response.ok) {
        // Token expired, clear storage
        await chrome.storage.local.remove(['user', 'authToken', 'refreshToken']);
        sendResponse({ success: true, data: { authenticated: false } });
        return;
      }
      
      const profile = await response.json();
      sendResponse({ success: true, data: { authenticated: true, user: profile.user } });
      
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  }
  
  async trackUsage(usageData, sendResponse) {
    try {
      // Store locally for now
      const stored = await chrome.storage.local.get(['usage_stats']);
      const stats = stored.usage_stats || {};
      
      const today = new Date().toISOString().split('T')[0];
      if (!stats[today]) stats[today] = [];
      
      stats[today].push({
        ...usageData,
        timestamp: new Date().toISOString()
      });
      
      await chrome.storage.local.set({ usage_stats: stats });
      
      if (sendResponse) {
        sendResponse({ success: true });
      }
      
    } catch (error) {
      console.error('Usage tracking error:', error);
      if (sendResponse) {
        sendResponse({ success: false, error: error.message });
      }
    }
  }
  
  async playSound(soundName, sendResponse) {
    try {
      // Get sound preferences
      const result = await chrome.storage.sync.get(['soundEnabled', 'soundVolume']);
      
      if (!result.soundEnabled) {
        sendResponse({ success: false, reason: 'Sound disabled' });
        return;
      }
      
      // Play sound using offscreen document or active tab
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (activeTab) {
        await chrome.tabs.sendMessage(activeTab.id, {
          action: 'play_sound',
          soundName: soundName,
          volume: result.soundVolume || 0.7
        });
      }
      
      sendResponse({ success: true });
      
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  }
  
  async makeApiCall(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response;
      
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }
  
  getFallbackResponse(itemData) {
    // Provide basic fallback when API is unavailable
    return {
      trust_score: 50,
      risk_level: 'MEDIUM',
      decision: 'CAUTION',
      message: 'Unable to verify - API unavailable. Please check manually.',
      fallback: true
    };
  }
  
  async showWelcomeNotification() {
    await chrome.notifications.create('welcome', {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'TrustGuard Installed!',
      message: 'Start protecting yourself from eBay scams. Visit any eBay listing to see instant verification.'
    });
  }
  
  async showUpdateNotification(previousVersion) {
    await chrome.notifications.create('update', {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'TrustGuard Updated!',
      message: `New features available! Updated from v${previousVersion} to v2.1.0`
    });
  }
  
  async showRiskNotification(result) {
    await chrome.notifications.create('risk-alert', {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: '⚠️ High Risk Item Detected',
      message: `Trust Score: ${result.trust_score}/100. ${result.primary_reason || 'Proceed with caution.'}`
    });
  }
}

// Initialize background service
new TrustGuardBackground();

// ===== content.js =====
// Enhanced content script with better error handling and performance
class TrustGuardContent {
  constructor() {
    this.isInitialized = false;
    this.overlayElement = null;
    this.currentItemData = null;
    this.soundEnabled = true;
    this.animationFrame = null;
    
    this.initialize();
  }
  
  async initialize() {
    if (this.isInitialized) return;
    
    try {
      // Wait for page to be ready
      if (document.readyState === 'loading') {
        await new Promise(resolve => {
          document.addEventListener('DOMContentLoaded', resolve, { once: true });
        });
      }
      
      // Extract item data from page
      this.currentItemData = this.extractItemData();
      
      if (!this.currentItemData.title) {
        console.log('TrustGuard: No valid item data found on this page');
        return;
      }
      
      // Load user preferences
      await this.loadPreferences();
      
      // Create and show overlay
      this.createOverlay();
      
      // Start verification process
      this.verifyCurrentItem();
      
      // Set up message listener
      chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
      
      this.isInitialized = true;
      console.log('🛡️ TrustGuard content script initialized');
      
    } catch (error) {
      console.error('TrustGuard initialization failed:', error);
    }
  }
  
  extractItemData() {
    try {
      // Enhanced eBay item data extraction
      const itemData = {
        title: '',
        price: 0,
        seller_info: {},
        description: '',
        photos: [],
        shipping_info: {},
        item_specifics: {},
        url: window.location.href,
        timestamp: new Date().toISOString()
      };
      
      // Extract title
      const titleSelectors = [
        'h1[data-testid="x-item-title"]',
        'h1#x-item-title',
        'h
