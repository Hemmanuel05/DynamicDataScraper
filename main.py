import os
import logging
import uuid
from flask import Flask, render_template, jsonify, send_file, request
from flask_migrate import Migrate
from scraper import SuffolkMapScraper
from data_cleaner import DataCleaner
from models import db, ScrapedMember, ScrapeSession
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

# Configure database
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    database_url = 'sqlite:///suffolk_scraper.db'  # Fallback to SQLite

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

# Create tables
with app.app_context():
    db.create_all()

# Global variables for tracking scraping progress
scraping_status = {
    'running': False,
    'progress': 0,
    'total_pins': 0,
    'current_pin': 0,
    'message': 'Ready to start scraping',
    'completed': False,
    'error': None,
    'csv_file': None,
    'session_id': None,
    'records_saved': 0
}

def run_scraping():
    """Run the scraping process in a background thread"""
    global scraping_status
    session = None
    
    try:
        # Create new scrape session
        session_id = str(uuid.uuid4())
        scraping_status['session_id'] = session_id
        scraping_status['running'] = True
        scraping_status['completed'] = False
        scraping_status['error'] = None
        scraping_status['records_saved'] = 0
        scraping_status['message'] = 'Initializing scraper...'
        
        # Create database session record
        with app.app_context():
            session = ScrapeSession(
                session_id=session_id,
                status='running'
            )
            db.session.add(session)
            db.session.commit()
        
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
        
        # Update session with pin count
        with app.app_context():
            session = ScrapeSession.query.filter_by(session_id=session_id).first()
            if session:
                session.total_pins_found = len(pins)
                db.session.commit()
        
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
        
        scraping_status['message'] = f'Extracted {len(raw_data)} records. Cleaning and saving data...'
        scraping_status['progress'] = 50
        
        # Clean and save the data
        cleaner = DataCleaner()
        cleaned_data = []
        saved_count = 0
        
        for i, record in enumerate(raw_data):
            scraping_status['progress'] = 50 + int((i / len(raw_data)) * 40)  # 40% for cleaning
            scraping_status['message'] = f'Processing record {i + 1} of {len(raw_data)}'
            
            try:
                cleaned_record = cleaner.clean_record(record)
                cleaned_data.append(cleaned_record)
                
                # Save to database
                with app.app_context():
                    member = ScrapedMember(
                        business_name=cleaned_record.get('Business Name'),
                        owner1=cleaned_record.get('Owner1'),
                        owner2=cleaned_record.get('Owner2'),
                        phone_primary=cleaned_record.get('Phone_primary'),
                        phone_cell=cleaned_record.get('Phone_cell'),
                        phone_office=cleaned_record.get('Phone_office'),
                        phone_other=cleaned_record.get('Phone_other'),
                        address_line1=cleaned_record.get('Address_Line1'),
                        address_line2=cleaned_record.get('Address_Line2'),
                        city=cleaned_record.get('City'),
                        state_province_region=cleaned_record.get('State / Province / Region'),
                        zip_postal_code=cleaned_record.get('Zip / Postal Code'),
                        country=cleaned_record.get('Country'),
                        email1=cleaned_record.get('Email1'),
                        email2=cleaned_record.get('Email2'),
                        website=cleaned_record.get('Website'),
                        business_type=cleaned_record.get('Business Type'),
                        species=cleaned_record.get('Species'),
                        breeds=cleaned_record.get('Breed(s)'),
                        social_network1=cleaned_record.get('Social Network1'),
                        social_network2=cleaned_record.get('Social Network 2'),
                        social_network3=cleaned_record.get('Social Network 3'),
                        last_updated=cleaned_record.get('Last Updated'),
                        about=cleaned_record.get('About'),
                        notes=cleaned_record.get('Notes'),
                        data_source=cleaned_record.get('Data Source'),
                        data_source_url=cleaned_record.get('Data Source URL'),
                        date_scraped=cleaned_record.get('Date Scraped')
                    )
                    db.session.add(member)
                    db.session.commit()
                    saved_count += 1
                    scraping_status['records_saved'] = saved_count
                    
            except Exception as e:
                logging.error(f'Error processing record {i + 1}: {str(e)}')
                continue
        
        # Export to CSV
        scraping_status['message'] = 'Exporting to CSV...'
        scraping_status['progress'] = 90
        csv_filename = f'suffolk_members_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        cleaner.export_to_csv(cleaned_data, csv_filename)
        
        # Update session record
        with app.app_context():
            session = ScrapeSession.query.filter_by(session_id=session_id).first()
            if session:
                session.status = 'completed'
                session.end_time = datetime.utcnow()
                session.records_scraped = len(raw_data)
                session.records_saved = saved_count
                session.csv_filename = csv_filename
                db.session.commit()
        
        scraping_status['csv_file'] = csv_filename
        scraping_status['progress'] = 100
        scraping_status['completed'] = True
        scraping_status['message'] = f'Scraping completed! Saved {saved_count} records to database and exported to {csv_filename}'
        
        logging.info(f'Scraping completed successfully. {saved_count} records saved to database and exported to {csv_filename}')
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['message'] = f'Error: {str(e)}'
        logging.error(f'Scraping failed: {str(e)}')
        
        # Update session record with error
        if scraping_status.get('session_id'):
            try:
                with app.app_context():
                    session = ScrapeSession.query.filter_by(session_id=scraping_status['session_id']).first()
                    if session:
                        session.status = 'failed'
                        session.end_time = datetime.utcnow()
                        session.error_message = str(e)
                        db.session.commit()
            except:
                pass
                
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

@app.route('/api/members')
def get_members():
    """Get all scraped members from database"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        members = ScrapedMember.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'members': [member.to_dict() for member in members.items],
            'total': members.total,
            'pages': members.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<int:member_id>')
def get_member(member_id):
    """Get a specific member by ID"""
    try:
        member = ScrapedMember.query.get_or_404(member_id)
        return jsonify(member.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions')
def get_sessions():
    """Get all scraping sessions"""
    try:
        sessions = ScrapeSession.query.order_by(ScrapeSession.start_time.desc()).all()
        return jsonify([session.to_dict() for session in sessions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>')
def get_session(session_id):
    """Get a specific scraping session"""
    try:
        session = ScrapeSession.query.filter_by(session_id=session_id).first_or_404()
        return jsonify(session.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    try:
        total_members = ScrapedMember.query.count()
        total_sessions = ScrapeSession.query.count()
        completed_sessions = ScrapeSession.query.filter_by(status='completed').count()
        failed_sessions = ScrapeSession.query.filter_by(status='failed').count()
        
        latest_session = ScrapeSession.query.order_by(ScrapeSession.start_time.desc()).first()
        
        return jsonify({
            'total_members': total_members,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'failed_sessions': failed_sessions,
            'latest_session': latest_session.to_dict() if latest_session else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/database')
def database_view():
    """View database contents"""
    return render_template('database.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
