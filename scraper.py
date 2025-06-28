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
            time.sleep(5)
            
            # Wait for the map container to be present
            map_container = self.wait.until(
                EC.presence_of_element_located((By.ID, "the-map"))
            )
            
            # Wait additional time for the map and pins to fully load
            time.sleep(10)
            
            logging.info('Map page loaded successfully')
            
        except TimeoutException:
            logging.error('Timeout waiting for map to load')
            raise
        except Exception as e:
            logging.error(f'Error loading map page: {str(e)}')
            raise

    def find_map_pins(self):
        """Find all clickable pins on the map"""
        try:
            # Look for various possible pin selectors
            pin_selectors = [
                "img[src*='pushpin']",
                "img[src*='pin']",
                "img[src*='marker']",
                ".pushpin",
                ".marker",
                ".pin",
                "area[shape='circle']",
                "area[shape='rect']",
                "[onclick*='showInfo']",
                "[onclick*='popup']"
            ]
            
            all_pins = []
            
            for selector in pin_selectors:
                try:
                    pins = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if pins:
                        logging.info(f'Found {len(pins)} pins using selector: {selector}')
                        all_pins.extend(pins)
                except Exception as e:
                    continue
            
            # Remove duplicates
            unique_pins = []
            seen_elements = set()
            
            for pin in all_pins:
                try:
                    element_id = pin.get_attribute('outerHTML')
                    if element_id not in seen_elements:
                        seen_elements.add(element_id)
                        unique_pins.append(pin)
                except:
                    continue
            
            # If no pins found with standard selectors, try to find clickable elements within map
            if not unique_pins:
                logging.info('No pins found with standard selectors, searching within map container')
                map_container = self.driver.find_element(By.ID, "the-map")
                clickable_elements = map_container.find_elements(By.XPATH, ".//*[@onclick or @onmousedown or @onmouseup]")
                unique_pins.extend(clickable_elements)
            
            logging.info(f'Found {len(unique_pins)} total unique pins')
            return unique_pins
            
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
                data = self.parse_popup_content(popup_content.text)
                
                # Close popup if possible
                self.close_popup()
                
                return data
            else:
                logging.warning('No popup content found after clicking pin')
                return None
                
        except Exception as e:
            logging.error(f'Error extracting pin data: {str(e)}')
            return None

    def parse_popup_content(self, content):
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
            
            lines = content.split('\n')
            current_field = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to identify and extract different fields
                line_lower = line.lower()
                
                # Business/Farm name (usually first or prominent)
                if not data['business_name'] and any(keyword in line_lower for keyword in ['farm', 'ranch', 'acres', 'livestock']):
                    data['business_name'] = line
                elif not data['business_name'] and len(line) > 3 and not any(char.isdigit() for char in line):
                    # Likely a business name if it's not too short and has no digits
                    data['business_name'] = line
                
                # Phone numbers
                phone_pattern = r'[\(]?[\d\s\-\.\(\)]{10,}'
                if re.search(phone_pattern, line):
                    phone = re.sub(r'[^\d]', '', line)
                    if len(phone) >= 10:
                        if not data['phone_primary']:
                            data['phone_primary'] = line
                        elif not data['phone_cell']:
                            data['phone_cell'] = line
                        elif not data['phone_office']:
                            data['phone_office'] = line
                
                # Email addresses
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                if re.search(email_pattern, line):
                    if not data['email1']:
                        data['email1'] = line
                    elif not data['email2']:
                        data['email2'] = line
                
                # Website
                if 'http' in line_lower or 'www.' in line_lower:
                    data['website'] = line
                
                # Address components
                if re.search(r'\d+\s+\w+', line) and not data['address_line1']:
                    # Looks like street address
                    data['address_line1'] = line
                
                # State abbreviations or full state names
                state_pattern = r'\b(A[LK]|A[SZRKLY]|C[AOT]|D[CE]|F[L]|G[A]|H[I]|I[DLANO]|K[SY]|L[A]|M[EHDAINSOT]|N[EVHJMYCD]|O[HKR]|P[ARW]|R[I]|S[CD]|T[NX]|U[T]|V[AIT]|W[AVIY])\b'
                if re.search(state_pattern, line, re.IGNORECASE):
                    data['state'] = line
                
                # ZIP codes
                zip_pattern = r'\b\d{5}(-\d{4})?\b'
                if re.search(zip_pattern, line):
                    data['zip_code'] = re.search(zip_pattern, line).group()
                
                # Owner names (look for patterns like "John & Jane Doe" or "John Doe")
                if re.search(r'^[A-Z][a-z]+ [A-Z][a-z]+', line) and not any(keyword in line_lower for keyword in ['farm', 'ranch', 'acres']):
                    if not data['owner1']:
                        data['owner1'] = line
                    elif not data['owner2']:
                        data['owner2'] = line
            
            # If no business name found, use owner name
            if not data['business_name'] and data['owner1']:
                data['business_name'] = data['owner1']
            
            return data
            
        except Exception as e:
            logging.error(f'Error parsing popup content: {str(e)}')
            return None

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
