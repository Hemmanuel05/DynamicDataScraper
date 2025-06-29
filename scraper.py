import time
import logging
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup

class SuffolkMapScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.map_url = "https://suffolk.digitalovine.com/modules.php?op=modload&name=_custom_maps&file=members#the-map"
        
    def setup_driver(self):
        """Setup Firefox WebDriver with headless configuration"""
        try:
            firefox_options = Options()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--no-sandbox')
            firefox_options.add_argument('--disable-dev-shm-usage')
            firefox_options.add_argument('--disable-gpu')
            firefox_options.add_argument('--window-size=1920,1080')
            
            # Set user agent
            firefox_options.set_preference("general.useragent.override", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Setup service with GeckoDriverManager
            service = Service(GeckoDriverManager().install())
            
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            logging.info('Firefox WebDriver initialized successfully')
            
        except Exception as e:
            logging.error(f'Failed to setup Firefox WebDriver: {str(e)}')
            raise

    def load_map_page(self):
        """Load the Suffolk map page and wait for it to fully load"""
        try:
            logging.info(f'Loading map page: {self.map_url}')
            self.driver.get(self.map_url)
            
            # Wait for the page to load
            time.sleep(8)
            
            # Try multiple selectors for the map container
            map_selectors = [
                "#the-map",
                ".map",
                "[id*='map']",
                "[class*='map']",
                "iframe",
                "[src*='google']",
                "[src*='map']"
            ]
            
            map_container = None
            for selector in map_selectors:
                try:
                    logging.info(f'Trying map selector: {selector}')
                    map_container = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f'Found map container with selector: {selector}')
                    break
                except TimeoutException:
                    continue
            
            if not map_container:
                # If no specific map container found, just wait for page body
                logging.info('No specific map container found, waiting for page body')
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Wait additional time for the map and pins to fully load
            time.sleep(15)
            
            # Check if we're on the right page by looking for expected content
            page_source = self.driver.page_source.lower()
            if 'suffolk' in page_source or 'member' in page_source or 'map' in page_source:
                logging.info('Map page loaded successfully - Suffolk content detected')
            else:
                logging.warning('Map page loaded but Suffolk content not clearly detected')
            
        except Exception as e:
            logging.error(f'Error loading map page: {str(e)}')
            # Log page source for debugging
            try:
                logging.info(f'Current page title: {self.driver.title}')
                logging.info(f'Current page URL: {self.driver.current_url}')
            except:
                pass
            raise

    def find_map_pins(self):
        """Find all clickable pins on the map"""
        try:
            logging.info('Starting pin search...')
            
            # Look for various possible pin selectors
            pin_selectors = [
                "img[src*='pushpin']",
                "img[src*='pin']", 
                "img[src*='marker']",
                "img[src*='colour']",  # Common in map pin naming
                ".pushpin",
                ".marker",
                ".pin",
                "area[shape='circle']",
                "area[shape='rect']",
                "area[onclick]",
                "[onclick*='showInfo']",
                "[onclick*='popup']",
                "[onclick*='member']",
                "[onclick*='info']",
                "div[onclick]",
                "span[onclick]",
                "a[onclick]"
            ]
            
            all_pins = []
            
            for selector in pin_selectors:
                try:
                    pins = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if pins:
                        logging.info(f'Found {len(pins)} elements using selector: {selector}')
                        all_pins.extend(pins)
                except Exception as e:
                    logging.debug(f'Selector {selector} failed: {str(e)}')
                    continue
            
            # Remove duplicates
            unique_pins = []
            seen_elements = set()
            
            for pin in all_pins:
                try:
                    element_id = pin.get_attribute('outerHTML')
                    if element_id and element_id not in seen_elements:
                        seen_elements.add(element_id)
                        unique_pins.append(pin)
                except:
                    continue
            
            # If no pins found with standard selectors, try broader search
            if not unique_pins:
                logging.info('No pins found with standard selectors, trying broader search...')
                
                # Try looking for any clickable elements
                clickable_selectors = [
                    "[onclick]",
                    "[onmousedown]", 
                    "[onmouseup]",
                    "img[alt*='member']",
                    "img[title*='member']",
                    "a[href*='member']"
                ]
                
                for selector in clickable_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logging.info(f'Found {len(elements)} clickable elements with: {selector}')
                            unique_pins.extend(elements)
                    except:
                        continue
            
            # If still no pins, search within any map containers found
            if not unique_pins:
                logging.info('Still no pins found, searching within all containers...')
                container_selectors = [
                    "#the-map",
                    ".map",
                    "[id*='map']",
                    "[class*='map']",
                    "div[style*='position']"
                ]
                
                for container_sel in container_selectors:
                    try:
                        containers = self.driver.find_elements(By.CSS_SELECTOR, container_sel)
                        for container in containers:
                            clickable_elements = container.find_elements(By.XPATH, ".//*[@onclick or @onmousedown or @onmouseup or @href]")
                            if clickable_elements:
                                logging.info(f'Found {len(clickable_elements)} clickable elements in container: {container_sel}')
                                unique_pins.extend(clickable_elements)
                    except:
                        continue
            
            # Final deduplication
            final_pins = []
            seen_final = set()
            for pin in unique_pins:
                try:
                    pin_html = pin.get_attribute('outerHTML')
                    if pin_html and pin_html not in seen_final:
                        seen_final.add(pin_html)
                        final_pins.append(pin)
                except:
                    continue
            
            logging.info(f'Found {len(final_pins)} total unique interactive elements')
            
            # If we still have no pins, log page source for debugging
            if not final_pins:
                logging.warning('No interactive elements found. Logging page info for debugging...')
                try:
                    logging.info(f'Page title: {self.driver.title}')
                    logging.info(f'Page URL: {self.driver.current_url}')
                    # Log a snippet of page source
                    page_source = self.driver.page_source
                    if len(page_source) > 1000:
                        logging.info(f'Page source snippet: {page_source[:1000]}...')
                    else:
                        logging.info(f'Full page source: {page_source}')
                except:
                    pass
            
            return final_pins
            
        except Exception as e:
            logging.error(f'Error finding map pins: {str(e)}')
            return []

    def extract_pin_data(self, pin):
        """Click a pin and extract the popup data"""
        try:
            # Scroll pin into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", pin)
            time.sleep(1)
            
            # Try different methods to click the pin
            clicked = False
            
            # Method 1: Regular click
            try:
                pin.click()
                clicked = True
            except ElementClickInterceptedException:
                # Method 2: JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", pin)
                    clicked = True
                except:
                    pass
            except:
                pass
            
            # Method 3: ActionChains click
            if not clicked:
                try:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(pin).click().perform()
                    clicked = True
                except:
                    pass
            
            if not clicked:
                logging.warning('Failed to click pin')
                return None
            
            # Wait for popup to appear
            time.sleep(3)
            
            # Look for popup content with various selectors
            popup_selectors = [
                ".popup",
                ".modal",
                ".info-window",
                ".member-info",
                "[class*='popup']",
                "[class*='modal']",
                "[class*='info']",
                "div[style*='position: absolute']",
                "div[style*='z-index']"
            ]
            
            popup_content = None
            
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            popup_content = element
                            break
                    if popup_content:
                        break
                except:
                    continue
            
            # If no popup found, try to get any newly appeared content
            if not popup_content:
                # Look for any div that appeared after clicking
                time.sleep(2)
                all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                for div in all_divs:
                    try:
                        if div.is_displayed() and div.text.strip() and len(div.text.strip()) > 20:
                            # Check if this looks like member data
                            text = div.text.lower()
                            if any(keyword in text for keyword in ['name', 'phone', 'email', 'address', 'farm']):
                                popup_content = div
                                break
                    except:
                        continue
            
            if popup_content:
                # Extract and parse the popup content
                # Try to get HTML content first for better parsing
                try:
                    html_content = popup_content.get_attribute('innerHTML')
                    text_content = popup_content.text
                    data = self.parse_popup_content(text_content, html_content)
                except:
                    # Fallback to text content only
                    data = self.parse_popup_content(popup_content.text, None)
                
                # Close popup if possible
                self.close_popup()
                
                return data
            else:
                logging.warning('No popup content found after clicking pin')
                return None
                
        except Exception as e:
            logging.error(f'Error extracting pin data: {str(e)}')
            return None

    def parse_popup_content(self, content, html_content=None):
        """Parse the popup content to extract member data"""
        try:
            data = {
                'business_name': '',
                'owner1': '',
                'owner2': '',
                'phone_primary': '',
                'phone_cell': '',
                'phone_office': '',
                'phone_other': '',
                'address_line1': '',
                'address_line2': '',
                'city': '',
                'state': '',
                'zip_code': '',
                'country': '',
                'email1': '',
                'email2': '',
                'website': '',
                'business_type': '',
                'species': '',
                'breeds': '',
                'social_network1': '',
                'social_network2': '',
                'social_network3': '',
                'last_updated': '',
                'about': '',
                'notes': '',
                'data_source': 'Suffolk DigitalOvine',
                'data_source_url': self.map_url,
                'date_scraped': time.strftime('%Y-%m-%d')
            }
            
            # Filter out Google Maps interface elements and noise
            google_noise = [
                'keyboard shortcuts', 'map data', 'google', 'inegi', 'terms of use',
                'report a map error', 'satellite', 'map', 'terrain', 'labels',
                '©2025', 'imagery', 'close', 'directions', 'terms', 'visit website',
                '10 km', '500 km', 'km', 'miles', 'mi'
            ]
            
            lines = []
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Skip Google Maps interface elements
                line_lower = line.lower()
                if any(noise in line_lower for noise in google_noise):
                    continue
                    
                # Skip single characters or very short strings
                if len(line) < 3:
                    continue
                    
                lines.append(line)
            
            # Log the cleaned content for debugging
            logging.info(f'Cleaned popup content lines: {lines[:5]}...' if len(lines) > 5 else f'Cleaned popup content lines: {lines}')
            
            all_text = ' '.join(lines)
            
            # Also try parsing HTML content if available for structured data
            if html_content:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Look for structured data in HTML
                    # Try to find links (potential websites/emails)
                    links = soup.find_all('a', href=True)
                    for link in links:
                        try:
                            href_attr = link.get('href')
                            if href_attr:
                                href = str(href_attr)
                                if 'mailto:' in href and not data['email1']:
                                    email = href.replace('mailto:', '').strip()
                                    data['email1'] = email
                                elif 'http' in href and not data['website']:
                                    # Filter out Google Maps URLs
                                    if not any(domain in href.lower() for domain in excluded_domains):
                                        data['website'] = href.strip()
                        except:
                            continue
                    
                    # Look for phone numbers in text content
                    text_elements = soup.find_all(text=True)
                    for text_elem in text_elements:
                        try:
                            text_str = str(text_elem).strip()
                            if text_str and re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text_str):
                                phone_clean = re.sub(r'[^\d]', '', text_str)
                                if len(phone_clean) >= 10 and not data['phone_primary']:
                                    data['phone_primary'] = text_str.strip()
                                    break
                        except:
                            continue
                    
                except Exception as e:
                    logging.debug(f'HTML parsing failed: {str(e)}')
                    pass
            
            # Extract different data types with improved patterns
            
            # Phone numbers - multiple patterns
            phone_patterns = [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567 or 555-123-4567
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',        # 555.123.4567
                r'\d{10,}',                               # 5551234567
                r'phone:?\s*([^\n\r]+)',                  # Phone: xxx
                r'tel:?\s*([^\n\r]+)',                    # Tel: xxx
                r'cell:?\s*([^\n\r]+)',                   # Cell: xxx
                r'mobile:?\s*([^\n\r]+)'                  # Mobile: xxx
            ]
            
            phones_found = []
            for pattern in phone_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                for match in matches:
                    # Clean phone number
                    if isinstance(match, tuple):
                        match = match[0] if match else ''
                    phone_clean = re.sub(r'[^\d]', '', str(match))
                    if len(phone_clean) >= 10:
                        phones_found.append(match.strip())
            
            # Assign phones to different fields
            if phones_found:
                if len(phones_found) >= 1:
                    data['phone_primary'] = phones_found[0]
                if len(phones_found) >= 2:
                    data['phone_cell'] = phones_found[1]
                if len(phones_found) >= 3:
                    data['phone_office'] = phones_found[2]
                if len(phones_found) >= 4:
                    data['phone_other'] = phones_found[3]
            
            # Email addresses - improved pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, all_text)
            if emails:
                data['email1'] = emails[0]
                if len(emails) > 1:
                    data['email2'] = emails[1]
            
            # Website/URLs - filter out Google Maps and other unwanted URLs
            url_patterns = [
                r'https?://[^\s]+',
                r'www\.[^\s]+',
                r'[a-zA-Z0-9.-]+\.(com|net|org|edu|gov)[^\s]*'
            ]
            
            excluded_domains = [
                'google.com', 'maps.google.com', 'gstatic.com', 'googleapis.com',
                'maps.gstatic.com', 'digitalovine.com'
            ]
            
            for pattern in url_patterns:
                urls = re.findall(pattern, all_text, re.IGNORECASE)
                for url in urls:
                    url_clean = url.lower().strip()
                    # Skip Google Maps and other unwanted URLs
                    if not any(domain in url_clean for domain in excluded_domains):
                        data['website'] = url
                        break
                if data['website']:
                    break
            
            # Business/Farm names and owner names
            name_candidates = []
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                    
                # Skip lines that look like addresses or other data
                if re.search(r'\d{5}(-\d{4})?', line_clean):  # ZIP code
                    continue
                if re.search(r'@', line_clean):  # Email
                    continue
                if re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line_clean):  # Phone
                    continue
                if re.search(r'https?://', line_clean):  # URL
                    continue
                    
                # Check if this looks like a name or business
                if len(line_clean) > 2 and re.search(r'[A-Za-z]', line_clean):
                    name_candidates.append(line_clean)
            
            # Assign names to appropriate fields
            if name_candidates:
                # First candidate is likely business name or primary owner
                first_name = name_candidates[0]
                
                # Check if first name contains joint names (e.g., "Earl & Cathy Marsh")
                joint_patterns = [' & ', ' and ', ' + ', '/', ' / ']
                is_joint_name = any(pattern in first_name for pattern in joint_patterns)
                
                if is_joint_name:
                    # Parse joint names
                    parsed_owners = self.parse_joint_names(first_name)
                    if parsed_owners:
                        data['owner1'] = parsed_owners.get('owner1', '')
                        data['owner2'] = parsed_owners.get('owner2', '')
                        data['business_name'] = parsed_owners.get('business_name', first_name)
                elif any(keyword in first_name.lower() for keyword in ['farm', 'ranch', 'acres', 'livestock', 'suffolks', 'sheep']):
                    # It's likely a business name
                    data['business_name'] = self.apply_proper_case(first_name)
                    if len(name_candidates) > 1:
                        # Check if second candidate is also a joint name
                        second_name = name_candidates[1]
                        if any(pattern in second_name for pattern in joint_patterns):
                            parsed_owners = self.parse_joint_names(second_name)
                            if parsed_owners:
                                data['owner1'] = parsed_owners.get('owner1', '')
                                data['owner2'] = parsed_owners.get('owner2', '')
                        else:
                            data['owner1'] = self.apply_proper_case(second_name)
                    if len(name_candidates) > 2:
                        data['owner2'] = self.apply_proper_case(name_candidates[2])
                else:
                    # Likely owner name
                    data['owner1'] = self.apply_proper_case(first_name)
                    if len(name_candidates) > 1:
                        second_name = name_candidates[1]
                        if any(keyword in second_name.lower() for keyword in ['farm', 'ranch', 'acres', 'livestock', 'suffolks', 'sheep']):
                            data['business_name'] = self.apply_proper_case(second_name)
                        else:
                            data['owner2'] = self.apply_proper_case(second_name)
                    
                    # If no business name found yet, use owner name
                    if not data['business_name']:
                        data['business_name'] = data['owner1']
            
            # Address parsing
            address_lines = []
            for line in lines:
                # Look for address patterns
                if re.search(r'\d+\s+[A-Za-z]', line):  # Street address pattern
                    address_lines.append(line)
                elif re.search(r'[A-Z]{2}\s+\d{5}', line):  # State ZIP pattern
                    address_lines.append(line)
            
            if address_lines:
                data['address_line1'] = address_lines[0]
                if len(address_lines) > 1:
                    data['address_line2'] = address_lines[1]
            
            # Extract city, state, ZIP from address-like lines
            for line in lines:
                # Look for ZIP codes
                zip_match = re.search(r'\b(\d{5}(-\d{4})?)\b', line)
                if zip_match and not data['zip_code']:
                    data['zip_code'] = zip_match.group(1)
                    
                    # Try to extract city and state from same line
                    # Pattern: CITY, STATE ZIP
                    city_state_pattern = r'([A-Z\s]+),\s*([A-Z]{2})\s+\d{5}'
                    cs_match = re.search(city_state_pattern, line)
                    if cs_match:
                        data['city'] = cs_match.group(1).strip()
                        data['state'] = cs_match.group(2).strip()
            
            # Species and breeds - look for Suffolk-specific terms
            for line in lines:
                line_lower = line.lower()
                if 'suffolk' in line_lower and not data['species']:
                    data['species'] = 'Sheep'
                    data['breeds'] = 'Suffolk'
                elif any(breed in line_lower for breed in ['sheep', 'lamb', 'ewe', 'ram']) and not data['species']:
                    data['species'] = 'Sheep'
            
            return data
            
        except Exception as e:
            logging.error(f'Error parsing popup content: {str(e)}')
            return None

    def parse_joint_names(self, name_string):
        """Parse joint names like 'Earl & Cathy Marsh' into separate owners"""
        try:
            # Patterns for joint names
            joint_patterns = [' & ', ' and ', ' + ', '/', ' / ']
            
            for pattern in joint_patterns:
                if pattern in name_string:
                    parts = name_string.split(pattern)
                    if len(parts) == 2:
                        left_part = parts[0].strip()
                        right_part = parts[1].strip()
                        
                        # Check if they share a last name
                        left_words = left_part.split()
                        right_words = right_part.split()
                        
                        if len(left_words) >= 2 and len(right_words) == 1:
                            # Case: "Earl & Cathy Marsh" -> "Earl Marsh" & "Cathy Marsh"
                            last_name = left_words[-1]
                            owner1 = self.apply_proper_case(f"{left_words[0]} {last_name}")
                            owner2 = self.apply_proper_case(f"{right_words[0]} {last_name}")
                            business_name = self.apply_proper_case(name_string)
                        elif len(left_words) >= 2 and len(right_words) >= 2:
                            # Case: "John Smith & Jane Doe" -> separate names
                            owner1 = self.apply_proper_case(left_part)
                            owner2 = self.apply_proper_case(right_part)
                            business_name = self.apply_proper_case(name_string)
                        else:
                            # Fallback
                            owner1 = self.apply_proper_case(left_part)
                            owner2 = self.apply_proper_case(right_part)
                            business_name = self.apply_proper_case(name_string)
                        
                        return {
                            'owner1': owner1,
                            'owner2': owner2,
                            'business_name': business_name
                        }
            
            return None
            
        except Exception as e:
            logging.error(f'Error parsing joint names: {str(e)}')
            return None

    def apply_proper_case(self, text):
        """Apply proper case formatting to names and titles"""
        if not text:
            return text
            
        try:
            # Handle special cases for all caps
            if text.isupper():
                # Convert to title case but handle special words
                words = text.split()
                proper_words = []
                
                for word in words:
                    # Handle special abbreviations that should stay uppercase
                    if word in ['LLC', 'INC', 'CORP', 'LTD', 'CO']:
                        proper_words.append(word)
                    # Handle Roman numerals
                    elif re.match(r'^[IVX]+$', word):
                        proper_words.append(word)
                    # Handle single letters or initials
                    elif len(word) == 1:
                        proper_words.append(word.upper())
                    # Handle hyphenated names
                    elif '-' in word:
                        hyphen_parts = [part.capitalize() for part in word.split('-')]
                        proper_words.append('-'.join(hyphen_parts))
                    # Regular words
                    else:
                        proper_words.append(word.capitalize())
                
                return ' '.join(proper_words)
            else:
                # Text is already in mixed case, just clean it up
                return text.strip()
                
        except Exception as e:
            logging.error(f'Error applying proper case: {str(e)}')
            return text

    def close_popup(self):
        """Try to close any open popup"""
        try:
            # Try various methods to close popup
            close_selectors = [
                ".close",
                ".x",
                "[onclick*='close']",
                "[onclick*='hide']",
                "button[type='button']"
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if close_btn.is_displayed():
                        close_btn.click()
                        time.sleep(1)
                        return
                except:
                    continue
            
            # Try pressing Escape key
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except:
                pass
            
            # Click somewhere else on the map to close popup
            try:
                map_container = self.driver.find_element(By.ID, "the-map")
                self.driver.execute_script("arguments[0].click();", map_container)
                time.sleep(1)
            except:
                pass
                
        except Exception as e:
            logging.warning(f'Could not close popup: {str(e)}')

    def cleanup(self):
        """Close the browser and cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                logging.info('WebDriver closed successfully')
        except Exception as e:
            logging.error(f'Error during cleanup: {str(e)}')
