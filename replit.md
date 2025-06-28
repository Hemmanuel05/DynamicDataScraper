# Suffolk Map Scraper

## Overview

This is a web application that scrapes member data from the Suffolk sheep breeders map and exports it to a clean CSV file. The application consists of a Flask web server with a simple interface for initiating scraping operations, a Selenium-based web scraper for extracting data from the Suffolk DigitalOvine map, and a data cleaning module to standardize the extracted information.

## System Architecture

### Frontend Architecture
- **Technology**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Styling**: Bootstrap 5.1.3 for responsive UI components
- **Icons**: Font Awesome 6.0.0 for visual elements
- **Design Pattern**: Single-page application with real-time progress updates
- **Database Interface**: Dedicated database viewer with member management

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Architecture Pattern**: MVC pattern with database persistence layer
- **Threading**: Background thread processing for non-blocking scraping operations
- **Logging**: Comprehensive logging to both file and console
- **API**: RESTful endpoints for database operations

### Data Processing Pipeline
1. **Data Extraction**: Selenium WebDriver scrapes the Suffolk map
2. **Data Cleaning**: Custom cleaning module standardizes extracted data
3. **Data Storage**: Clean data saved to PostgreSQL database
4. **Data Export**: Clean data exported to CSV format

## Key Components

### Web Scraper (`scraper.py`)
- **Purpose**: Extracts member data from the Suffolk DigitalOvine map
- **Technology**: Selenium WebDriver with Chrome (headless mode)
- **Target**: Interactive map with clickable pins containing member information
- **Architecture Decision**: Chose Selenium over requests/BeautifulSoup due to the dynamic, JavaScript-heavy nature of the target website

### Data Cleaner (`data_cleaner.py`)
- **Purpose**: Standardizes and validates scraped data
- **Features**: Text cleaning, phone number formatting, email validation, address normalization
- **Output Schema**: 27 predefined CSV columns including business info, contact details, and metadata
- **Architecture Decision**: Separate cleaning module allows for easy modification of cleaning rules without affecting scraper logic

### Web Interface (`main.py`, `templates/`, `static/`)
- **Purpose**: Provides user-friendly interface for scraping operations and database management
- **Features**: Real-time progress tracking, status updates, error handling, CSV download, database viewer
- **Architecture Decision**: Flask chosen for simplicity and rapid development; JavaScript handles real-time updates via polling
- **Database Integration**: PostgreSQL with SQLAlchemy ORM for persistent data storage

### Progress Tracking System
- **Implementation**: Global status dictionary with thread-safe updates
- **Features**: Progress percentage, current operation status, error reporting
- **Real-time Updates**: Frontend polls backend every 2 seconds for status updates

## Data Flow

1. **Initialization**: User clicks "Start Scraping" button
2. **Background Processing**: Flask spawns background thread for scraping
3. **Web Scraping**: Selenium loads map page and extracts pin data
4. **Data Cleaning**: Raw data processed through cleaning pipeline
5. **CSV Export**: Clean data written to timestamped CSV file
6. **User Notification**: Frontend updates with completion status and download link

## External Dependencies

### Python Packages
- **Flask**: Web framework for the user interface
- **Selenium**: Web browser automation for scraping
- **BeautifulSoup4**: HTML parsing (used in conjunction with Selenium)
- **Chrome WebDriver**: Browser automation engine

### External Services
- **Target Website**: Suffolk DigitalOvine map (https://suffolk.digitalovine.com/)
- **Chrome Browser**: Required for Selenium automation

### Browser Requirements
- **Chrome/Chromium**: Must be installed on the system
- **ChromeDriver**: Automatically managed by Selenium

## Deployment Strategy

### Environment Setup
- **Python Version**: Compatible with Python 3.7+
- **System Requirements**: Chrome browser and appropriate drivers
- **Logging**: File-based logging (scraper.log) and console output

### Configuration
- **Headless Mode**: Chrome runs in headless mode for server environments
- **Timeouts**: 30-second timeout for web elements
- **User Agent**: Spoofed to avoid detection

### Scalability Considerations
- **Single-threaded**: One scraping operation at a time to avoid overwhelming target server
- **Memory Management**: Log entries limited to prevent memory issues
- **Error Handling**: Comprehensive exception handling with user-friendly error messages

## Database Schema

### ScrapedMember Table
Stores cleaned member data with all 27 required CSV columns:
- **Primary Fields**: business_name, owner1, owner2
- **Contact Fields**: phone_primary, phone_cell, phone_office, phone_other, email1, email2, website
- **Address Fields**: address_line1, address_line2, city, state_province_region, zip_postal_code, country
- **Business Fields**: business_type, species, breeds
- **Social Fields**: social_network1, social_network2, social_network3
- **Metadata Fields**: last_updated, about, notes, data_source, data_source_url, date_scraped
- **System Fields**: id (primary key), created_at, updated_at

### ScrapeSession Table
Tracks scraping operations and their results:
- **Session Fields**: session_id (UUID), start_time, end_time, status
- **Progress Fields**: total_pins_found, records_scraped, records_saved
- **Output Fields**: csv_filename, error_message

## API Endpoints

### Database API Routes
- **GET /api/members**: Paginated list of all scraped members
- **GET /api/members/{id}**: Individual member details
- **GET /api/sessions**: List of all scraping sessions
- **GET /api/sessions/{session_id}**: Individual session details  
- **GET /api/stats**: Database statistics and counts
- **GET /database**: Database viewer interface

## Changelog

Changelog:
- June 28, 2025: Database integration added with PostgreSQL, SQLAlchemy models, API endpoints, and database viewer interface
- June 28, 2025: Initial setup with web scraper, data cleaner, and Flask interface

## User Preferences

Preferred communication style: Simple, everyday language.