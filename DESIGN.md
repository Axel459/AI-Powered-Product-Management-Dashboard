# Product Management Dashboard - Technical Design Document

## System Architecture

### Overview

The Product Management Dashboard is built on a Flask-based web application that integrates multiple AI agents through CrewAI for review analysis. The system contains three different core complonents: data, AI analysis, and presentation layers.

## Core Compontents

### 1. Data

**Product Search Flow**
* Uses a public dataset of Amazon reviews available at https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
* Database is reduced to only electronics reviews and metadata having more than 100 reviews in 2023 to optimize demo speed and storage in the SQLite database
* Two tables are used, the Metadata table and the Reviews table. These are linked through the products' unqiue identifier (ASIN) in the analysis.

**Company Search Flow**
* Data is scraped in real time from web using BeautifulSoup4 for parsing HTML
* Trustpilot.com is used to read company reviews
* At least 50 reviews for the company, otherwise the application will ask the user to select another company

### 2. AI Analysis

**Design Choice**
The system uses CrewAI to orchestrate multiple specialized AI agents. This approach was chosen over a single-agent system for several reasons:
* Better separation of concerns to enhance analysis
* More focused and accurate analysis per domain
* Easier to maintain and modify individual components
* Allows for parallel processing in future iterations

**Example: Product Manager Agent**
* Role: "Lead Product Manager"
* Goal: "Develop strategic feature improvements based on customer feedback"
* Background: "You are a strategic product consultant who excels attransforming customer feedback into actionable product improvements. You have a track record of identifying high-impact feature enhancements"
* Imrovement_task: As a Product Manager, propose the single most impactful feature improvement for {product_title}. Current Features: product_metadata['features']. Use the output of the Feature Analysis Specialist and Customer Pain Point Specalist as context. Format your output in HTML format.

*All agents can be found in helpers.py*

**Agent Task Flow:**
1. Data Collection Tasks
* Review gathering
* Initial preprocessing
* Data validation

2. Analysis Tasks
* Feature identification
* Pain point analysis
* Strategic recommendations

3. HTML formatting
* Output to fit CSS Template
* HTML structure generation
* Consistent styling

### 3. Presentation Layer
Frontend Design

1. TailwindCSS
* Chosen for utility-first approach
* Enables rapid UI development
* Easy responsiveness implementation

2. JavaScript Functionality
* Asynchronous processing with loading states
* Real-time search suggestions
* Error handling and user feedback
* Progress monitoring for long-running tasks


## Main Technologies Used
* Flask (Web Framework)
* CrewAI (AI Orchestration)
* GPT-4 (Language Model)
* BeautifulSoup4 (Web Scraping)
* SQLite (Database)
* TailwindCSS (Styling)


## Code Organization
* documentation: User and Technical guides
* templates: all html pages
* amazon_reviews_filtered.db: database for product search
* app.py: main application file
* beautifulscraper.py: webscraper for company search
* helpers.py: supporting functions
* load_data.py: load and filters data into db
* requirements.txt: includes all libraries
* test.py: contains old test code, not used

## Support
* In case of issues or quesitons, feel free to reach out to axel.svensson@yale.edu
