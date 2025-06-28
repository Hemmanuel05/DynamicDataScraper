from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

db = SQLAlchemy()

class ScrapedMember(db.Model):
    """Model for storing scraped member data"""
    __tablename__ = 'scraped_members'
    
    id = Column(Integer, primary_key=True)
    business_name = Column(String(255))
    owner1 = Column(String(100))
    owner2 = Column(String(100))
    phone_primary = Column(String(20))
    phone_cell = Column(String(20))
    phone_office = Column(String(20))
    phone_other = Column(String(20))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state_province_region = Column(String(100))
    zip_postal_code = Column(String(20))
    country = Column(String(100))
    email1 = Column(String(255))
    email2 = Column(String(255))
    website = Column(String(255))
    business_type = Column(String(100))
    species = Column(String(100))
    breeds = Column(String(255))
    social_network1 = Column(String(255))
    social_network2 = Column(String(255))
    social_network3 = Column(String(255))
    last_updated = Column(String(50))
    about = Column(Text)
    notes = Column(Text)
    data_source = Column(String(100))
    data_source_url = Column(String(255))
    date_scraped = Column(String(50))
    
    # Additional metadata fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScrapedMember {self.business_name}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'business_name': self.business_name,
            'owner1': self.owner1,
            'owner2': self.owner2,
            'phone_primary': self.phone_primary,
            'phone_cell': self.phone_cell,
            'phone_office': self.phone_office,
            'phone_other': self.phone_other,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state_province_region': self.state_province_region,
            'zip_postal_code': self.zip_postal_code,
            'country': self.country,
            'email1': self.email1,
            'email2': self.email2,
            'website': self.website,
            'business_type': self.business_type,
            'species': self.species,
            'breeds': self.breeds,
            'social_network1': self.social_network1,
            'social_network2': self.social_network2,
            'social_network3': self.social_network3,
            'last_updated': self.last_updated,
            'about': self.about,
            'notes': self.notes,
            'data_source': self.data_source,
            'data_source_url': self.data_source_url,
            'date_scraped': self.date_scraped,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ScrapeSession(db.Model):
    """Model for tracking scraping sessions"""
    __tablename__ = 'scrape_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50))  # 'running', 'completed', 'failed'
    total_pins_found = Column(Integer, default=0)
    records_scraped = Column(Integer, default=0)
    records_saved = Column(Integer, default=0)
    error_message = Column(Text)
    csv_filename = Column(String(255))
    
    def __repr__(self):
        return f'<ScrapeSession {self.session_id}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_pins_found': self.total_pins_found,
            'records_scraped': self.records_scraped,
            'records_saved': self.records_saved,
            'error_message': self.error_message,
            'csv_filename': self.csv_filename
        }