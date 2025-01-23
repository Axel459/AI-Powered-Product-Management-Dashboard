from helpers import analyze_product_reviews, get_db_connection, analyze_company_reviews, clean_company_url
from flask import Flask, render_template, request, jsonify, redirect, url_for
import uuid
from threading import Thread
import time
import traceback
from beautifulscraper import scrape_trustpilot_reviews, InsufficientReviewsError


app = Flask(__name__)

# Store for analysis tasks
analysis_tasks = {}

@app.route('/')
def landing_page():
    """
    Render the landing page for the Product Management Dashboard
    """
    return render_template('index.html')



# ------ Product Flow --------

@app.route('/product-search', methods=['GET', 'POST'])
def product_search():
    """
    Render the product search page
    """
    if request.method == 'POST':
        selected_product = request.form.get('product_title', '')
        return redirect(url_for('product_insights', product_title=selected_product))

    return render_template('product_search.html')

@app.route('/get-product-suggestions')
def get_product_suggestions():
    """
    Provide product title suggestions based on user input
    """
    query = request.args.get('query', '')

    # Only search if query is at least 2 characters long
    if len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()

    # Use SQL LIKE for case-insensitive partial matching
    cursor.execute("""
        SELECT DISTINCT title
        FROM metadata
        WHERE LOWER(title) LIKE LOWER(?)
        ORDER BY rating_number DESC
        LIMIT 10
    """, (f'%{query}%',))

    suggestions = [row[0] for row in cursor.fetchall()]

    conn.close()
    return jsonify(suggestions)




@app.route('/product-insights/<path:product_title>')
def product_insights(product_title):
    """
    Display product insights
    """
    # Get product info from database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM metadata
        WHERE title = ?
        LIMIT 1
    """, (product_title,))

    product_info = cursor.fetchone()
    conn.close()

    # Find the completed analysis
    matching_tasks = [
        task for task in analysis_tasks.values()
        if task.get('status') == 'completed' and
        task.get('product_title') == product_title
    ]

    if not matching_tasks:
        print(f"No completed analysis found for: {product_title}")
        return redirect(url_for('product_search'))

    task = max(matching_tasks, key=lambda x: x.get('timestamp', 0))

    return render_template('product_insights.html',
                         product_title=product_title,
                         product_info=product_info,
                         insights=task['result'])



# ------ Waiting page --------

def run_analysis(task_id: str, product_title: str):
    """
    Run the analysis in a separate thread
    """
    try:
        print(f"Starting analysis for task {task_id}: {product_title}")
        # Run the analysis
        result = analyze_product_reviews(product_title)

        # Debug print to see the structure
        print("Analysis Result Structure:")
        print("Type:", type(result))
        #print("Content:", result)

        # Store the result
        analysis_tasks[task_id] = {
            'status': 'completed',
            'result': result,
            'product_title': product_title,
            'timestamp': time.time()
        }
        print(f"Analysis completed for task {task_id}")
    except Exception as e:
        print(f"Analysis failed for task {task_id}: {str(e)}")
        print(traceback.format_exc())
        analysis_tasks[task_id] = {
            'status': 'failed',
            'error': str(e),
            'product_title': product_title,
            'timestamp': time.time()
        }

@app.route('/start-analysis', methods=['POST'])
def start_analysis():
    """
    Start the analysis process and return a task ID
    """
    product_title = request.json.get('product_title')
    task_id = str(uuid.uuid4())

    print(f"Creating new analysis task {task_id} for product: {product_title}")

    # Initialize task status
    analysis_tasks[task_id] = {
        'status': 'running',
        'product_title': product_title,
        'timestamp': time.time()
    }

    # Start analysis in background thread
    analysis_thread = Thread(target=run_analysis, args=(task_id, product_title))
    analysis_thread.start()

    return jsonify({'task_id': task_id})

@app.route('/check-analysis-status/<task_id>')
def check_analysis_status(task_id):
    """
    Check the status of an analysis task
    """
    print(f"Checking status for task {task_id}")
    task = analysis_tasks.get(task_id)

    if not task:
        print(f"Task {task_id} not found")
        return jsonify({'status': 'not_found'})

    print(f"Task {task_id} status: {task['status']}")
    return jsonify({
        'status': task['status'],
        'error': task.get('error'),
        'timestamp': task.get('timestamp')
    })


# Add cleanup job for old tasks
def cleanup_old_tasks():
    """
    Remove completed tasks older than 1 hour
    """
    while True:
        current_time = time.time()
        to_remove = []

        for task_id, task in analysis_tasks.items():
            if (task['status'] in ['completed', 'failed'] and
                current_time - task.get('timestamp', current_time) > 3600):
                to_remove.append(task_id)

        for task_id in to_remove:
            del analysis_tasks[task_id]

        time.sleep(3600)  # Run every hour

# Start cleanup thread
Thread(target=cleanup_old_tasks, daemon=True).start()





# ------ Company Flow --------

@app.route('/company-search')
def company_search():
    """
    Render the company search page
    """
    return render_template('company_search.html')

@app.route('/analyze-company', methods=['POST'])
def analyze_company():
    """
    Endpoint to analyze company reviews from Trustpilot
    """
    try:
        company_url = request.json.get('company_url')
        if not company_url:
            return jsonify({'error': 'No company URL provided'}), 400

        # Clean and validate URL
        company_url = clean_company_url(company_url)
        if not company_url or '.' not in company_url:
            return jsonify({'error': 'Invalid company URL format'}), 400

        # Initialize status in analysis tasks
        task_id = str(uuid.uuid4())
        analysis_tasks[task_id] = {
            'status': 'running',
            'company_url': company_url,
            'timestamp': time.time()
        }

        # Start analysis in background
        Thread(target=run_company_analysis, args=(task_id, company_url)).start()

        return jsonify({'task_id': task_id})

    except Exception as e:
        print(f"Error starting analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_company_analysis(task_id: str, company_url: str):
    """
    Run the company analysis in a separate thread
    """
    try:
        print(f"Starting analysis for task {task_id}: {company_url}")

        # Step 1: Scrape reviews
        reviews_df = scrape_trustpilot_reviews(company_url)

        # Step 2: Run analysis
        analysis_results = analyze_company_reviews(company_url, reviews_df)

        # Store results
        analysis_tasks[task_id] = {
            'status': 'completed',
            'result': {
                'tasks_output': analysis_results,  # This should be the CrewAI output
                'reviews': reviews_df.to_dict('records'),
                'reviews_count': len(reviews_df),
                #'average_rating': round(reviews_df['rating'].astype(float).mean(), 2)
            },
            'company_url': company_url,
            'timestamp': time.time()
        }

        print(f"Analysis completed for task {task_id}")

    except InsufficientReviewsError as e:
        print(f"Insufficient reviews for task {task_id}: {str(e)}")
        analysis_tasks[task_id] = {
            'status': 'failed',
            'error': str(e),
            'company_url': company_url,
            'timestamp': time.time()
        }

    except Exception as e:
        print(f"Analysis failed for task {task_id}: {str(e)}")
        print(traceback.format_exc())
        analysis_tasks[task_id] = {
            'status': 'failed',
            'error': str(e),
            'company_url': company_url,
            'timestamp': time.time()
        }

@app.route('/company-insights/<path:company_url>')
def company_insights(company_url):
    """
    Display company insights
    """
    print(f"Fetching insights for company: {company_url}")

    matching_tasks = [
        task for task in analysis_tasks.values()
        if task.get('status') == 'completed' and
        task.get('company_url') == company_url
    ]

    if not matching_tasks:
        print(f"No completed analysis found for: {company_url}")
        return redirect(url_for('company_search'))

    task = max(matching_tasks, key=lambda x: x.get('timestamp', 0))

    return render_template('company_insights.html',
                         company_url=company_url,
                         insights=task['result'])


if __name__ == '__main__':
    app.run(debug=True)



