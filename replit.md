# Suffolk Map Scraper

## Overview

This is a web application that scrapes member data from the Suffolk sheep breeders map and exports it to a clean CSV file. The application consists of a Flask web server with a simple interface for initiating scraping operations, a Selenium-based web scraper for extracting data from the Suffolk DigitalOvine map, and a data cleaning module to standardize the extracted information.

## System Architecture

### Frontend Architecture
- **Technology**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Styling**: Bootstrap 5.1.3 for responsive UI components
- **Icons**: Font Awesome 6.0.0 for visual elements
- **Design Pattern**: Single-page application with real-time progress updates

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Architecture Pattern**: Simple MVC pattern with separation of concerns
- **Threading**: Background thread processing for non-blocking scraping operations
- **Logging**: Comprehensive logging to both file and console

### Data Processing Pipeline
1. **Data Extraction**: Selenium WebDriver scrapes the Suffolk map
2. **Data Cleaning**: Custom cleaning module standardizes extracted data
3. **Data Export**: Clean data exported to CSV format

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
- **Purpose**: Provides user-friendly interface for scraping operations
- **Features**: Real-time progress tracking, status updates, error handling, CSV download
- **Architecture Decision**: Flask chosen for simplicity and rapid development; JavaScript handles real-time updates via polling

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

## Changelog

Changelog:
- June 28, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.