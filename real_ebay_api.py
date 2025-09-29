# real_ebay_api.py
"""
Production-ready eBay API integration
Handles real eBay Finding Service API calls with proper error handling,
rate limiting, and data transformation
"""

import aiohttp
import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

@dataclass
class EBayAPIConfig:
    """eBay API configuration"""
    app_id: str
    cert_id: str = ""
    dev_id: str = ""
    site_id: str = "0"  # 0 = US, 3 = UK, 77 = Germany
    version: str = "1.13.0"
    base_url: str = "https://svcs.ebay.com/services/search/FindingService/v1"
    
class EBayAPIError(Exception):
    """Custom eBay API error"""
    pass

class EBayAPIClient:
    """Production eBay API client with comprehensive error handling"""
    
    def __init__(self, config: EBayAPIConfig):
        self.config = config
        self.session = None
        
        # Rate limiting (eBay allows 5000 calls/day, 200/hour for Finding API)
        self.rate_limit_calls = 0
        self.rate_limit_window_start = time.time()
        self.max_calls_per_hour = 180  # Conservative limit
        
        # Caching to reduce API calls
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Request retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=10
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'TrustGuard-API/2.0',
                'Accept-Encoding': 'gzip, deflate'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter if hour has passed
        if current_time - self.rate_limit_window_start > 3600:
            self.rate_limit_calls = 0
            self.rate_limit_window_start = current_time
        
        if self.rate_limit_calls >= self.max_calls_per_hour:
            raise EBayAPIError(f"Rate limit exceeded: {self.max_calls_per_hour} calls/hour")
        
        self.rate_limit_calls += 1
    
    def _get_cache_key(self, operation: str, params: dict) -> str:
        """Generate cache key for request"""
        # Sort params for consistent key generation
        param_str = json.dumps(params, sort_keys=True)
        cache_key = f"{operation}:{hashlib.md5(param_str.encode()).hexdigest()}"
        return cache_key
    
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry['timestamp'] < self.cache_ttl
    
    async def _make_request(self, operation: str, params: dict) -> dict:
        """Make HTTP request to eBay API with retry logic"""
        if not self.session:
            raise EBayAPIError("Session not initialized. Use async context manager.")
        
        # Check rate limit
        self._check_rate_limit()
        
        # Check cache first
        cache_key = self._get_cache_key(operation, params)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info(f"Cache hit for {operation}")
            return self.cache[cache_key]['data']
        
        # Prepare request parameters
        request_params = {
            'OPERATION-NAME': operation,
            'SERVICE-VERSION': self.config.version,
            'SECURITY-APPNAME': self.config.app_id,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'REST-PAYLOAD': '',
            'GLOBAL-ID': f'EBAY-US',  # Can be made configurable
            **params
        }
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"eBay API call: {operation} (attempt {attempt + 1})")
                
                async with self.session.get(self.config.base_url, params=request_params) as response:
                    # Check HTTP status
                    if response.status == 429:  # Too Many Requests
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited by eBay. Waiting {retry_after} seconds.")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        raise EBayAPIError(f"HTTP {response.status}: {error_text}")
                    
                    # Parse JSON response
                    data = await response.json()
                    
                    # Check for eBay API errors
                    self._validate_ebay_response(data, operation)
                    
                    # Cache successful response
                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': time.time()
                    }
                    
                    logger.info(f"eBay API call successful: {operation}")
                    return data
                    
            except asyncio.TimeoutError as e:
                last_exception = EBayAPIError(f"Request timeout: {e}")
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                
            except aiohttp.ClientError as e:
                last_exception = EBayAPIError(f"Network error: {e}")
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_exception = EBayAPIError(f"Unexpected error: {e}")
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        raise last_exception or EBayAPIError("All retry attempts failed")
    
    def _validate_ebay_response(self, data: dict, operation: str):
        """Validate eBay API response for errors"""
        if not data:
            raise EBayAPIError("Empty response from eBay API")
        
        # Check for operation-specific response structure
        response_key = f"{operation}Response"
        if response_key not in data:
            raise EBayAPIError(f"Missing {response_key} in API response")
        
        response_data = data[response_key][0]  # eBay wraps in array
        
        # Check acknowledgment
        ack = response_data.get('ack', [''])[0]
        if ack not in ['Success', 'Warning']:
            errors = response_data.get('errorMessage', [{}])
            error_msgs = [err.get('error', [{}])[0].get('message', ['Unknown error'])[0] 
                         for err in errors if 'error' in err]
            raise EBayAPIError(f"eBay API error: {'; '.join(error_msgs)}")
        
        # Log warnings
        if ack == 'Warning' and 'errorMessage' in response_data:
            warnings = response_data.get('errorMessage', [{}])
            warning_msgs = [warn.get('error', [{}])[0].get('message', [''])[0] 
                           for warn in warnings if 'error' in warn]
            logger.warning(f"eBay API warnings: {'; '.join(warning_msgs)}")
    
    async def find_completed_items(self, keywords: str, category_id: str = None, 
                                 max_entries: int = 100) -> List[Dict]:
        """Find completed/sold items"""
        params = {
            'keywords': keywords,
            'itemFilter(0).name': 'SoldItemsOnly',
            'itemFilter(0).value': 'true',
            'itemFilter(1).name': 'ListingType',
            'itemFilter(1).value': 'FixedPrice',
            'sortOrder': 'EndTimeSoonest',
            'paginationInput.entriesPerPage': str(min(max_entries, 100))
        }
        
        if category_id:
            params['categoryId'] = category_id
        
        try:
            data = await self._make_request('findCompletedItems', params)
            return self._parse_items_response(data, 'findCompletedItems')
        except EBayAPIError as e:
            logger.error(f"Error finding completed items for '{keywords}': {e}")
            return []
    
    async def find_active_items(self, keywords: str, category_id: str = None,
                              max_entries: int = 100) -> List[Dict]:
        """Find active items for sale"""
        params = {
            'keywords': keywords,
            'itemFilter(0).name': 'ListingType',
            'itemFilter(0).value': 'FixedPrice',
            'sortOrder': 'BestMatch',
            'paginationInput.entriesPerPage': str(min(max_entries, 100))
        }
        
        if category_id:
            params['categoryId'] = category_id
        
        try:
            data = await self._make_request('findItemsAdvanced', params)
            return self._parse_items_response(data, 'findItemsAdvanced')
        except EBayAPIError as e:
            logger.error(f"Error finding active items for '{keywords}': {e}")
            return []
    
    async def get_item_details(self, item_id: str) -> Optional[Dict]:
        """Get detailed information about a specific item"""
        # Note: This requires Shopping API, not Finding API
        # For now, return None - would need separate Shopping API integration
        logger.info(f"Item details not available for {item_id} (requires Shopping API)")
        return None
    
    def _parse_items_response(self, data: dict, operation: str) -> List[Dict]:
        """Parse items from eBay API response"""
        try:
            response_key = f"{operation}Response"
            response_data = data[response_key][0]
            search_result = response_data.get('searchResult', [{}])[0]
            
            items = search_result.get('item', [])
            if not items:
                logger.info(f"No items found in {operation} response")
                return []
            
            parsed_items = []
            for item in items:
                try:
                    parsed_item = self._parse_single_item(item)
                    if parsed_item:
                        parsed_items.append(parsed_item)
                except Exception as e:
                    logger.warning(f"Error parsing item: {e}")
                    continue
            
            logger.info(f"Parsed {len(parsed_items)} items from {operation}")
            return parsed_items
            
        except Exception as e:
            logger.error(f"Error parsing {operation} response: {e}")
            return []
    
    def _parse_single_item(self, item: dict) -> Optional[Dict]:
        """Parse a single item from eBay response"""
        try:
            # Extract basic information
            item_id = item.get('itemId', [''])[0]
            title = item.get('title', [''])[0]
            
            if not item_id or not title:
                return None
            
            # Extract price information
            selling_status = item.get('sellingStatus', [{}])[0]
            current_price = selling_status.get('currentPrice', [{}])[0]
            price = float(current_price.get('__value__', 0))
            currency = current_price.get('@currencyId', 'USD')
            
            # Extract listing information
            listing_info = item.get('listingInfo', [{}])[0]
            listing_type = listing_info.get('listingType', [''])[0]
            end_time = listing_info.get('endTime', [''])[0]
            start_time = listing_info.get('startTime', [''])[0]
            
            # Extract seller information
            seller_info = item.get('sellerInfo', [{}])[0]
            seller_name = seller_info.get('sellerUserName', [''])[0]
            feedback_score = int(seller_info.get('feedbackScore', [0])[0])
            feedback_percent = float(seller_info.get('positiveFeedbackPercent', [0])[0])
            
            # Extract condition
            condition_info = item.get('condition', [{}])
            if condition_info and condition_info[0]:
                condition = condition_info[0].get('conditionDisplayName', ['Used'])[0]
            else:
                condition = 'Used'
            
            # Extract category
            primary_category = item.get('primaryCategory', [{}])[0]
            category_id = primary_category.get('categoryId', [''])[0]
            category_name = primary_category.get('categoryName', [''])[0]
            
            # Extract shipping information
            shipping_info = item.get('shippingInfo', [{}])[0]
            shipping_cost = 0.0
            if 'shippingServiceCost' in shipping_info:
                shipping_cost = float(shipping_info['shippingServiceCost'][0].get('__value__', 0))
            
            # Extract location
            location = item.get('location', [''])[0]
            
            # Extract watch count (if available)
            watch_count = 0
            if 'listingInfo' in item:
                watch_count = int(item['listingInfo'][0].get('watchCount', [0])[0])
            
            # Build standardized item dictionary
            parsed_item = {
                'item_id': item_id,
                'title': title,
                'price': price,
                'currency': currency,
                'condition': condition,
                'category_id': category_id,
                'category_name': category_name,
                'listing_type': listing_type,
                'start_time': start_time,
                'end_time': end_time,
                'seller': {
                    'username': seller_name,
                    'feedback_score': feedback_score,
                    'feedback_percentage': feedback_percent
                },
                'shipping': {
                    'cost': shipping_cost,
                    'location': location
                },
                'watch_count': watch_count,
                'url': f"https://www.ebay.com/itm/{item_id}",
                'raw_data': item  # Keep original for debugging
            }
            
            return parsed_item
            
        except Exception as e:
            logger.error(f"Error parsing individual item: {e}")
            return None
    
    async def search_similar_items(self, title: str, max_entries: int = 50) -> Tuple[List[Dict], List[Dict]]:
        """Search for similar items (both sold and active)"""
        # Clean and optimize search terms
        search_terms = self._optimize_search_terms(title)
        
        # Run both searches concurrently
        sold_task = self.find_completed_items(search_terms, max_entries=max_entries)
        active_task = self.find_active_items(search_terms, max_entries=max_entries)
        
        sold_items, active_items = await asyncio.gather(sold_task, active_task)
        
        return sold_items, active_items
    
    def _optimize_search_terms(self, title: str) -> str:
        """Optimize search terms for better eBay matching"""
        # Remove common eBay noise words
        noise_words = {
            'new', 'used', 'refurbished', 'pre-owned', 'vintage', 'rare',
            'authentic', 'original', 'genuine', 'oem', 'aftermarket',
            'free', 'shipping', 'fast', 'quick', 'sale', 'deal', 'look',
            'nice', 'great', 'excellent', 'good', 'mint', 'perfect',
            'bundle', 'lot', 'set', 'kit', 'case', 'box'
        }
        
        words = title.lower().split()
        
        # Remove noise words but keep brand/model words
        filtered_words = []
        for word in words:
            # Keep if not noise word or if it looks like a model number
            if word not in noise_words or any(char.isdigit() for char in word):
                filtered_words.append(word)
        
        # Take most important words (usually first 5-6 are brand/model)
        important_words = filtered_words[:6]
        
        return ' '.join(important_words)
    
    def get_api_usage_stats(self) -> dict:
        """Get current API usage statistics"""
        return {
            'calls_this_hour': self.rate_limit_calls,
            'calls_remaining': max(0, self.max_calls_per_hour - self.rate_limit_calls),
            'window_reset_time': self.rate_limit_window_start + 3600,
            'cache_entries': len(self.cache),
            'cache_hit_rate': getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_attempts', 1), 1)
        }

# Usage example and testing
async def test_ebay_api():
    """Test the eBay API integration"""
    config = EBayAPIConfig(
        app_id="YOUR_EBAY_APP_ID_HERE",  # Replace with real app ID
        site_id="0"  # US site
    )
    
    async with EBayAPIClient(config) as client:
        print("Testing eBay API integration...")
        
        # Test finding sold items
        print("\n1. Finding sold items for 'iPhone 13'...")
        sold_items = await client.find_completed_items("iPhone 13", max_entries=10)
        print(f"Found {len(sold_items)} sold items")
        
        if sold_items:
            print(f"Example sold item: {sold_items[0]['title']} - ${sold_items[0]['price']}")
        
        # Test finding active items
        print("\n2. Finding active items for 'iPhone 13'...")
        active_items = await client.find_active_items("iPhone 13", max_entries=10)
        print(f"Found {len(active_items)} active items")
        
        if active_items:
            print(f"Example active item: {active_items[0]['title']} - ${active_items[0]['price']}")
        
        # Test similar items search
        print("\n3. Testing similar items search...")
        sold, active = await client.search_similar_items("Apple iPhone 13 Pro Max 256GB Unlocked")
        print(f"Similar items: {len(sold)} sold, {len(active)} active")
        
        # Show API usage stats
        stats = client.get_api_usage_stats()
        print(f"\n4. API Usage Stats:")
        print(f"   Calls this hour: {stats['calls_this_hour']}")
        print(f"   Calls remaining: {stats['calls_remaining']}")
        print(f"   Cache entries: {stats['cache_entries']}")

if __name__ == "__main__":
    asyncio.run(test_ebay_api())
