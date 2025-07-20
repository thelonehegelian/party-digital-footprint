import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import asyncio
from loguru import logger

from .base import BaseScraper


class MetaAdsScraper(BaseScraper):
    """Scraper for Meta Ad Library to get political advertisements."""
    
    def __init__(self, search_terms: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.search_terms = search_terms or ["Reform UK", "Reform Party"]
        self.access_token = None
        self.base_url = "https://graph.facebook.com/v18.0/ads_archive"
    
    async def setup(self):
        """Initialize Meta Ads API access."""
        self.access_token = os.getenv("META_ADS_API_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        if not self.access_token:
            logger.warning("Meta Ads API Token not found. Skipping Meta Ads scraping.")
            return
        
        # Test API access
        try:
            test_params = {
                'access_token': self.access_token,
                'search_terms': 'test',
                'ad_reached_countries': "['GB']",
                'ad_type': 'POLITICAL_AND_ISSUE_ADS',
                'limit': 1
            }
            response = requests.get(self.base_url, params=test_params)
            
            if response.status_code == 200:
                logger.info("Meta Ads API access verified")
            else:
                logger.error(f"Meta Ads API test failed: {response.status_code}")
                self.access_token = None
                
        except Exception as e:
            logger.error(f"Error testing Meta Ads API: {e}")
            self.access_token = None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape political ads from Meta Ad Library."""
        if not self.access_token:
            logger.warning("Meta Ads API not initialized. Skipping Meta Ads scraping.")
            return []
        
        messages = []
        
        for search_term in self.search_terms:
            try:
                term_messages = await self.scrape_ads_for_term(search_term)
                messages.extend(term_messages)
                await asyncio.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"Error scraping ads for term '{search_term}': {e}")
                continue
        
        # Remove duplicates based on ad_id
        seen_ids = set()
        unique_messages = []
        for msg in messages:
            ad_id = msg.get('raw_data', {}).get('ad_id')
            if ad_id and ad_id not in seen_ids:
                seen_ids.add(ad_id)
                unique_messages.append(msg)
        
        logger.info(f"Scraped {len(unique_messages)} unique political ads")
        return unique_messages
    
    async def scrape_ads_for_term(self, search_term: str) -> List[Dict[str, Any]]:
        """Scrape ads for a specific search term."""
        messages = []
        
        params = {
            'access_token': self.access_token,
            'search_terms': search_term,
            'ad_reached_countries': "['GB']",  # UK only
            'ad_type': 'POLITICAL_AND_ISSUE_ADS',
            'ad_active_status': 'ALL',
            'fields': 'id,ad_creation_time,ad_creative_bodies,ad_creative_link_captions,ad_creative_link_descriptions,ad_creative_link_titles,ad_delivery_start_time,ad_delivery_stop_time,ad_snapshot_url,currency,demographic_distribution,delivery_by_region,estimated_audience_size,impressions,page_id,page_name,publisher_platforms,spend,funding_entity',
            'limit': 100
        }
        
        try:
            while len(messages) < 200:  # Limit per search term
                response = requests.get(self.base_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Meta Ads API error for term '{search_term}': {response.status_code}")
                    break
                
                data = response.json()
                
                if 'data' not in data or not data['data']:
                    break
                
                for ad in data['data']:
                    message_data = self.process_ad(ad)
                    if message_data:
                        messages.append(message_data)
                
                # Check for next page
                if 'paging' in data and 'next' in data['paging']:
                    next_url = data['paging']['next']
                    # Extract cursor for next request
                    if 'after' in next_url:
                        cursor = next_url.split('after=')[1].split('&')[0]
                        params['after'] = cursor
                    else:
                        break
                else:
                    break
                
                await asyncio.sleep(self.delay)
                
        except Exception as e:
            logger.error(f"Error in scrape_ads_for_term for '{search_term}': {e}")
        
        return messages
    
    def process_ad(self, ad: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single political ad into message format."""
        try:
            ad_id = ad.get('id', '')
            
            # Extract ad content
            content_parts = []
            
            # Ad creative bodies (main text)
            if 'ad_creative_bodies' in ad and ad['ad_creative_bodies']:
                content_parts.extend(ad['ad_creative_bodies'])
            
            # Link titles and descriptions
            if 'ad_creative_link_titles' in ad and ad['ad_creative_link_titles']:
                content_parts.extend(ad['ad_creative_link_titles'])
            
            if 'ad_creative_link_descriptions' in ad and ad['ad_creative_link_descriptions']:
                content_parts.extend(ad['ad_creative_link_descriptions'])
            
            if 'ad_creative_link_captions' in ad and ad['ad_creative_link_captions']:
                content_parts.extend(ad['ad_creative_link_captions'])
            
            content = ' | '.join(content_parts) if content_parts else ''
            
            if not content:
                logger.debug(f"Skipping ad {ad_id} - no content")
                return None
            
            # Parse dates
            created_time = None
            start_time = None
            stop_time = None
            
            if ad.get('ad_creation_time'):
                created_time = self.parse_date(ad['ad_creation_time'])
            
            if ad.get('ad_delivery_start_time'):
                start_time = self.parse_date(ad['ad_delivery_start_time'])
            
            if ad.get('ad_delivery_stop_time'):
                stop_time = self.parse_date(ad['ad_delivery_stop_time'])
            
            # Build metadata
            metadata = {
                'page_name': ad.get('page_name', ''),
                'funding_entity': ad.get('funding_entity', ''),
                'currency': ad.get('currency', ''),
                'publisher_platforms': ad.get('publisher_platforms', []),
                'estimated_audience_size': ad.get('estimated_audience_size', {}),
                'delivery_dates': {
                    'start': start_time.isoformat() if start_time else None,
                    'stop': stop_time.isoformat() if stop_time else None
                }
            }
            
            # Add spend information
            if 'spend' in ad:
                metadata['spend'] = ad['spend']
            
            # Add impressions
            if 'impressions' in ad:
                metadata['impressions'] = ad['impressions']
            
            # Add demographic and geographic data
            if 'demographic_distribution' in ad:
                metadata['demographics'] = ad['demographic_distribution']
            
            if 'delivery_by_region' in ad:
                metadata['delivery_regions'] = ad['delivery_by_region']
            
            return {
                'content': content,
                'url': ad.get('ad_snapshot_url', ''),
                'published_at': start_time or created_time,
                'message_type': 'ad',
                'metadata': metadata,
                'raw_data': {
                    'ad_id': ad_id,
                    'page_id': ad.get('page_id', ''),
                    'scraper': 'meta_ads',
                    'raw_ad': ad
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing Meta ad: {e}")
            return None