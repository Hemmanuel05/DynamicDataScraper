import os
import logging
from flask import Flask, render_template, jsonify, send_file
from scraper import SuffolkMapScraper
from data_cleaner import DataCleaner
import threading
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Global variables for tracking scraping progress
scraping_status = {
    'running': False,
    'progress': 0,
    'total_pins': 0,
    'current_pin': 0,
    'message': 'Ready to start scraping',
    'completed': False,
    'error': None,
    'csv_file': None
}

def run_scraping():
    """Run the scraping process in a background thread"""
    global scraping_status
    
    try:
        scraping_status['running'] = True
        scraping_status['completed'] = False
        scraping_status['error'] = None
        scraping_status['message'] = 'Initializing scraper...'
        
        # Initialize scraper
        scraper = SuffolkMapScraper()
        scraper.setup_driver()
        
        scraping_status['message'] = 'Loading map page...'
        
        # Load the map page
        scraper.load_map_page()
        
        scraping_status['message'] = 'Finding pins on map...'
        
        # Find all pins
        pins = scraper.find_map_pins()
        scraping_status['total_pins'] = len(pins)
        
        if not pins:
            scraping_status['error'] = 'No pins found on the map'
            return
        
        scraping_status['message'] = f'Found {len(pins)} pins. Starting extraction...'
        
        # Extract data from each pin
        raw_data = []
        for i, pin in enumerate(pins):
            scraping_status['current_pin'] = i + 1
            scraping_status['progress'] = int((i / len(pins)) * 50)  # First 50% for scraping
            scraping_status['message'] = f'Extracting data from pin {i + 1} of {len(pins)}'
            
            try:
                pin_data = scraper.extract_pin_data(pin)
                if pin_data:
                    raw_data.append(pin_data)
                    logging.info(f'Extracted data from pin {i + 1}: {pin_data.get("business_name", "Unknown")}')
            except Exception as e:
                logging.error(f'Error extracting data from pin {i + 1}: {str(e)}')
                continue
        
        scraper.cleanup()
        
        if not raw_data:
            scraping_status['error'] = 'No data extracted from any pins'
            return
        
        scraping_status['message'] = f'Extracted {len(raw_data)} records. Cleaning data...'
        scraping_status['progress'] = 50
        
        # Clean the data
        cleaner = DataCleaner()
        cleaned_data = []
        
        for i, record in enumerate(raw_data):
            scraping_status['progress'] = 50 + int((i / len(raw_data)) * 50)  # Second 50% for cleaning
            scraping_status['message'] = f'Cleaning record {i + 1} of {len(raw_data)}'
            
            try:
                cleaned_record = cleaner.clean_record(record)
                cleaned_data.append(cleaned_record)
            except Exception as e:
                logging.error(f'Error cleaning record {i + 1}: {str(e)}')
                continue
        
        # Export to CSV
        scraping_status['message'] = 'Exporting to CSV...'
        csv_filename = f'suffolk_members_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        cleaner.export_to_csv(cleaned_data, csv_filename)
        
        scraping_status['csv_file'] = csv_filename
        scraping_status['progress'] = 100
        scraping_status['completed'] = True
        scraping_status['message'] = f'Scraping completed! Exported {len(cleaned_data)} records to {csv_filename}'
        
        logging.info(f'Scraping completed successfully. {len(cleaned_data)} records exported to {csv_filename}')
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['message'] = f'Error: {str(e)}'
        logging.error(f'Scraping failed: {str(e)}')
    finally:
        scraping_status['running'] = False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    global scraping_status
    
    if scraping_status['running']:
        return jsonify({'error': 'Scraping is already running'}), 400
    
    # Reset status
    scraping_status = {
        'running': True,
        'progress': 0,
        'total_pins': 0,
        'current_pin': 0,
        'message': 'Starting scraper...',
        'completed': False,
        'error': None,
        'csv_file': None
    }
    
    # Start scraping in background thread
    thread = threading.Thread(target=run_scraping)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started'})

@app.route('/status')
def get_status():
    """Get current scraping status"""
    return jsonify(scraping_status)

@app.route('/download/<filename>')
def download_file(filename):
    """Download the generated CSV file"""
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
