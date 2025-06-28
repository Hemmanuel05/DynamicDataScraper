import re
import csv
import logging
from datetime import datetime

class DataCleaner:
    def __init__(self):
        self.csv_columns = [
            'Business Name', 'Owner1', 'Owner2', 'Phone_primary', 'Phone_cell', 
            'Phone_office', 'Phone_other', 'Address_Line1', 'Address_Line2', 
            'City', 'State / Province / Region', 'Zip / Postal Code', 'Country', 
            'Email1', 'Email2', 'Website', 'Business Type', 'Species', 'Breed(s)', 
            'Social Network1', 'Social Network 2', 'Social Network 3', 
            'Last Updated', 'About', 'Notes', 'Data Source', 'Data Source URL', 
            'Date Scraped'
        ]

    def clean_record(self, raw_data):
        """Clean a single record according to the specified rules"""
        cleaned = {}
        
        # Clean business name
        cleaned['Business Name'] = self.clean_business_name(raw_data.get('business_name', ''))
        
        # Clean owner names
        owner1, owner2 = self.clean_owner_names(
            raw_data.get('owner1', ''), 
            raw_data.get('owner2', ''),
            cleaned['Business Name']
        )
        cleaned['Owner1'] = owner1
        cleaned['Owner2'] = owner2
        
        # Clean phone numbers
        cleaned['Phone_primary'] = self.clean_phone_number(raw_data.get('phone_primary', ''))
        cleaned['Phone_cell'] = self.clean_phone_number(raw_data.get('phone_cell', ''))
        cleaned['Phone_office'] = self.clean_phone_number(raw_data.get('phone_office', ''))
        cleaned['Phone_other'] = self.clean_phone_number(raw_data.get('phone_other', ''))
        
        # Clean address fields
        cleaned['Address_Line1'] = self.clean_text(raw_data.get('address_line1', ''))
        cleaned['Address_Line2'] = self.clean_text(raw_data.get('address_line2', ''))
        cleaned['City'] = self.clean_city_name(raw_data.get('city', ''))
        cleaned['State / Province / Region'] = self.clean_text(raw_data.get('state', ''))
        cleaned['Zip / Postal Code'] = self.clean_zip_code(raw_data.get('zip_code', ''))
        cleaned['Country'] = self.clean_text(raw_data.get('country', ''))
        
        # Clean contact info
        cleaned['Email1'] = self.clean_email(raw_data.get('email1', ''))
        cleaned['Email2'] = self.clean_email(raw_data.get('email2', ''))
        cleaned['Website'] = self.clean_website(raw_data.get('website', ''))
        
        # Clean business details
        cleaned['Business Type'] = self.clean_text(raw_data.get('business_type', ''))
        cleaned['Species'] = self.clean_text(raw_data.get('species', ''))
        cleaned['Breed(s)'] = self.clean_text(raw_data.get('breeds', ''))
        
        # Social networks
        cleaned['Social Network1'] = self.clean_text(raw_data.get('social_network1', ''))
        cleaned['Social Network 2'] = self.clean_text(raw_data.get('social_network2', ''))
        cleaned['Social Network 3'] = self.clean_text(raw_data.get('social_network3', ''))
        
        # Dates and metadata
        cleaned['Last Updated'] = self.clean_date(raw_data.get('last_updated', ''))
        cleaned['About'] = self.clean_text(raw_data.get('about', ''))
        cleaned['Notes'] = self.clean_text(raw_data.get('notes', ''))
        cleaned['Data Source'] = raw_data.get('data_source', 'Suffolk DigitalOvine')
        cleaned['Data Source URL'] = raw_data.get('data_source_url', '')
        cleaned['Date Scraped'] = self.clean_date(raw_data.get('date_scraped', datetime.now().strftime('%Y-%m-%d')))
        
        return cleaned

    def clean_text(self, text):
        """Clean general text fields"""
        if not text:
            return ''
        
        # Fix encoding artifacts
        text = text.replace('â€™', "'")
        text = text.replace('â€œ', '"')
        text = text.replace('â€', '"')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def clean_business_name(self, name):
        """Clean business name with special rules"""
        name = self.clean_text(name)
        if not name:
            return ''
        
        # Standardize LLC formatting
        name = re.sub(r'\bllc\b', 'LLC', name, flags=re.IGNORECASE)
        name = re.sub(r'\bl\.l\.c\.\b', 'LLC', name, flags=re.IGNORECASE)
        
        # Standardize Inc formatting
        name = re.sub(r'\binc\b', 'Inc', name, flags=re.IGNORECASE)
        name = re.sub(r'\bincorporated\b', 'Inc', name, flags=re.IGNORECASE)
        
        # Capitalize properly
        name = self.proper_case(name)
        
        return name

    def clean_owner_names(self, owner1, owner2, business_name):
        """Clean and parse owner names according to rules"""
        owner1 = self.clean_text(owner1)
        owner2 = self.clean_text(owner2)
        
        # If owner1 contains multiple names, try to split them
        if owner1 and not owner2:
            # Handle patterns like "Scott & Lee Ann Armstrong"
            if ' & ' in owner1:
                parts = owner1.split(' & ')
                if len(parts) == 2:
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()
                    
                    # If second part doesn't have last name, use last name from first part
                    if ' ' in first_part and ' ' not in second_part:
                        last_name = first_part.split()[-1]
                        owner1 = self.proper_case(first_part)
                        owner2 = self.proper_case(f"{second_part} {last_name}")
                    else:
                        owner1 = self.proper_case(first_part)
                        owner2 = self.proper_case(second_part)
            
            # Handle patterns like "Lowder, Michael and Kate"
            elif ', ' in owner1 and ' and ' in owner1:
                # Pattern: "Last, First and Second"
                match = re.match(r'([^,]+),\s*(.+?)\s+and\s+(.+)', owner1)
                if match:
                    last_name = match.group(1).strip()
                    first_name = match.group(2).strip()
                    second_name = match.group(3).strip()
                    
                    owner1 = self.proper_case(f"{first_name} {last_name}")
                    owner2 = self.proper_case(f"{second_name} {last_name}")
        
        # Remove duplicate names from business name if they match owners
        if business_name and owner1:
            # If business name is just the owner name, keep it
            pass
        
        # Ensure proper case for owner names
        if owner1:
            owner1 = self.proper_case(owner1)
        if owner2:
            owner2 = self.proper_case(owner2)
        
        return owner1, owner2

    def proper_case(self, text):
        """Apply proper case to names and titles"""
        if not text:
            return ''
        
        # Split into words and capitalize each
        words = text.split()
        capitalized_words = []
        
        for word in words:
            # Handle special cases
            if word.upper() in ['LLC', 'INC', 'CO', 'LTD', 'LP', 'LLP']:
                capitalized_words.append(word.upper())
            elif word.lower() in ['and', 'of', 'the', 'for', 'with', 'in', 'on', 'at']:
                # Keep articles and prepositions lowercase unless they're the first word
                if len(capitalized_words) == 0:
                    capitalized_words.append(word.capitalize())
                else:
                    capitalized_words.append(word.lower())
            else:
                # Handle names with apostrophes like O'Connor
                if "'" in word:
                    parts = word.split("'")
                    capitalized_parts = [part.capitalize() for part in parts]
                    capitalized_words.append("'".join(capitalized_parts))
                else:
                    capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)

    def clean_phone_number(self, phone):
        """Clean phone numbers to digits only, max 10 digits"""
        if not phone:
            return ''
        
        # Extract only digits
        digits = re.sub(r'[^\d]', '', phone)
        
        # Remove leading 1 if it makes the number 11 digits
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        
        # Return only if 10 digits or fewer
        if len(digits) <= 10 and len(digits) >= 7:
            return digits
        
        return ''

    def clean_email(self, email):
        """Clean email addresses"""
        if not email:
            return ''
        
        email = self.clean_text(email)
        
        # Validate email format
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, email)
        
        if match:
            return match.group().lower()
        
        return ''

    def clean_website(self, website):
        """Clean website URLs"""
        if not website:
            return ''
        
        website = self.clean_text(website)
        
        # Add http:// if missing
        if website and not website.startswith(('http://', 'https://')):
            if website.startswith('www.'):
                website = 'http://' + website
            elif '.' in website:
                website = 'http://www.' + website
        
        return website

    def clean_city_name(self, city):
        """Clean city names"""
        city = self.clean_text(city)
        if city:
            city = self.proper_case(city)
        return city

    def clean_zip_code(self, zip_code):
        """Clean ZIP codes"""
        if not zip_code:
            return ''
        
        # Extract ZIP code pattern
        zip_pattern = r'\b\d{5}(-\d{4})?\b'
        match = re.search(zip_pattern, zip_code)
        
        if match:
            return match.group()
        
        return ''

    def clean_date(self, date_str):
        """Normalize dates to YYYY-MM-DD format"""
        if not date_str:
            return ''
        
        # If already in correct format
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        # Try to parse various date formats
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2})/(\d{1,2})/(\d{2})',  # MM/DD/YY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if len(match.group(3)) == 4:  # 4-digit year
                        month, day, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif len(match.group(1)) == 4:  # YYYY/MM/DD
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:  # 2-digit year
                        month, day, year = match.groups()
                        year = f"20{year}" if int(year) < 50 else f"19{year}"
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    continue
        
        return ''

    def export_to_csv(self, cleaned_data, filename):
        """Export cleaned data to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writeheader()
                
                for record in cleaned_data:
                    writer.writerow(record)
            
            logging.info(f'Successfully exported {len(cleaned_data)} records to {filename}')
            
        except Exception as e:
            logging.error(f'Error exporting to CSV: {str(e)}')
            raise
