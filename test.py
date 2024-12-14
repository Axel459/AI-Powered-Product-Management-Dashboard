

os.environ['OPENAI_API_KEY'] = "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"
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4o-mini'

def get_reviews_for_product(product_title: str, limit: int = 50) -> List[Dict]:
    """
    Fetch reviews for a specific product from the database
    Steps:
    1. Find the parent_asin from metadata table using the product title
    2. Use the parent_asin to find all related reviews
    """
    conn = sqlite3.connect('amazon_reviews_filtered.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.rating, r.text, r.timestamp
        FROM reviews r
        JOIN metadata m ON r.parent_asin = m.parent_asin
        WHERE m.parent_asin = (
            SELECT parent_asin
            FROM metadata
            WHERE title = ?
            LIMIT 1
        )
        ORDER BY r.helpful_vote DESC
        LIMIT ?
    """, (product_title, limit))

    reviews = [
        {
            'rating': row[0],
            'text': row[1],
            'timestamp': row[2]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return reviews

# Define the agents
feature_analyst = Agent(
    role='Feature Analysis Specialist',
    goal='Identify and analyze product features from customer reviews',
    backstory="""You are an experienced product analyst specializing in
    identifying key features and their impact on user satisfaction. You have
    a strong background in pattern recognition and customer feedback analysis.""",
    verbose=True,
    tools=[]  # Add any specific tools needed
)

pain_point_analyst = Agent(
    role='Customer Pain Point Specialist',
    goal='Identify and categorize customer pain points and frustrations',
    backstory="""You are an expert in customer experience analysis, focusing on
    identifying and understanding customer problems, frustrations, and negative
    experiences with products.""",
    verbose=True,
    tools=[]
)

improvement_strategist = Agent(
    role='Product Improvement Strategist',
    goal='Develop strategic feature improvements based on customer feedback',
    backstory="""You are a strategic product consultant who excels at
    transforming customer feedback into actionable product improvements.
    You have a track record of identifying high-impact feature enhancements.""",
    verbose=True,
    llm='gpt-4o',
    tools=[]
)

def analyze_product_reviews(product_title: str):
    """
    Analyze product reviews using CrewAI agents
    """
    # Fetch reviews
    reviews = get_reviews_for_product(product_title)
    reviews_text = "\n".join([f"Review {i+1}: {review['text']}"
                             for i, review in enumerate(reviews)])

    # Define tasks
    favorite_feature_task = Task(
        description=f"""
        Analyze these customer reviews and identify the most frequently praised
        and appreciated feature of the product. Provide specific evidence by qouting customers
        to support your conclusion.

        Reviews:
        {reviews_text}
        """,
        agent=feature_analyst,
        expected_output="A concise analysis of the most praised product feature with supporting evidence from customer qoutes."
    )

    least_favorite_task = Task(
        description=f"""
        Analyze these customer reviews and identify the feature that receives
        the most criticism or negative feedback. Provide specific evidence from
        the reviews to support your conclusion.

        Reviews:
        {reviews_text}
        """,
        agent=feature_analyst,
        expected_output="A concise analysis of the most criticized product feature with supporting evidence from customer reviews."
    )

    pain_points_task = Task(
        description=f"""
        Analyze these customer reviews and identify the top 3 most significant
        pain points that customers experience. For each pain point, provide
        specific examples from the reviews and explain their impact on the
        customer experience.

        Reviews:
        {reviews_text}
        """,
        agent=pain_point_analyst,
        expected_output="A list of the top 3 customer pain points with specific examples and impact analysis."
    )

    improvement_task = Task(
        description=f"""
        Based on the customer reviews and identified pain points, propose the
        single most impactful feature improvement or new feature that would
        address the most critical customer needs. Your suggestion should be:
        1. Directly tied to customer feedback
        2. Technically feasible
        3. Likely to have a significant positive impact on user satisfaction

        Reviews:
        {reviews_text}
        """,
        agent=improvement_strategist,
        expected_output="A detailed proposal for the most impactful feature improvement based on customer feedback analysis.",
        context=[pain_points_task, favorite_feature_task, least_favorite_task]
    )

    # Create and run the crew
    crew = Crew(
        agents=[feature_analyst, pain_point_analyst, improvement_strategist],
        tasks=[favorite_feature_task, least_favorite_task,
                pain_points_task, improvement_task],
        process=Process.sequential  # Tasks will run in sequence
    )

    result = crew.kickoff()
    return result




<!-- AI Analysis Results -->
            {% if insights %}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Most Favorite Feature -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-green-600">
                        Most Favorite Feature
                    </h2>
                    <div class="prose">{{ insights.tasks_output[0] }}</div>
                </div>

                <!-- Least Favorite Feature -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-red-600">
                        Least Favorite Feature
                    </h2>
                    <div class="prose">{{ insights.tasks_output[1] }}</div>
                </div>

                <!-- Pain Points -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-orange-600">
                        Top Pain Points
                    </h2>
                    <div class="prose whitespace-pre-line">{{ insights.tasks_output[2] }}</div>
                </div>

                <!-- Suggested Improvement -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4 text-blue-600">
                        Recommended Improvement
                    </h2>
                    <div class="prose whitespace-pre-line">{{ insights.tasks_output[3] }}</div>
                </div>
            </div>
            {% endif %}
        </div>
    </main>

    <footer class="bg-white shadow-md py-4 mt-8">
        <p class="text-center text-gray-500">© 2024 Product Management Dashboard</p>
    </footer>
</body>
</html>



# Define tasks
    favorite_feature_task = Task(
        description=f"""
        Analyze these customer reviews and identify the most frequently praised
        and appreciated feature of the product. Provide evidence to support your reasoning
        by quoting customers. Don't mention specific review numbers.

        Reviews:
        {reviews_text}

        Format your response in a clear, structured manner using proper HTML formatting:
        - Use <strong>text</strong> for emphasis instead of **text**
        - Use proper paragraph breaks with <p> tags
        - Format lists with <ol> and <li> tags
        - Ensure sections are clearly labeled and formatted
        """,
        agent=feature_analyst,
        expected_output="A concise list of the most praised product features with supporting evidence from customer quotes."
    )


    pain_points_task = Task(
        description=f"""
        Analyze these customer reviews and identify the top 3 most significant
        pain points that customers experience. For each pain point, provide
        specific customer quotes from the reviews and explain their impact on the
        customer experience. Don't mention specific review numbers.

        Reviews:
        {reviews_text}

        Format your response in a clear, structured manner using proper HTML formatting:
        - Use <strong>text</strong> for emphasis instead of **text**
        - Use proper paragraph breaks with <p> tags
        - Format lists with <ol> and <li> tags
        - Ensure sections are clearly labeled and formatted
        """,
        agent=pain_point_analyst,
        expected_output="A list of the top 3 customer pain points with specific customer quotes."
    )



    improvement_task = Task(
        description=f"""
        As a Product Manager, analyze the following information and propose the single most impactful
        feature improvement for {product_title}.

        Product Information:
        - Current Features: {product_metadata['features'] if product_metadata else 'Not available'}

        Based on this comprehensive analysis:
        1. Identify the most critical pain points that need addressing
        2. Consider how the currently appreciated features can be leveraged or enhanced
        3. Propose a specific feature improvement or new feature that would:
        - Directly address the identified customer pain points
        - Build upon existing strengths and positive features
        - Be technically feasible to implement
        - Have the highest potential impact on user satisfaction

        Your proposal should include:
        1. Feature Name and Brief Overview
        2. Detailed Description of the Improvement
        3. How it Addresses Specific Pain Points
        4. Expected Impact on User Experience
        5. Technical Feasibility Considerations
        6. Implementation Priority Level

        Format your response in a clear, structured manner using proper HTML formatting:
        - Use <strong>text</strong> for emphasis instead of **text**
        - Use proper paragraph breaks with <p> tags
        - Format lists with <ol> and <li> tags
        - Ensure sections are clearly labeled and formatted
        """,
        agent=product_manager,
        expected_output="A comprehensive feature improvement proposal that integrates pain points analysis, current features, and user preferences.",
        context=[pain_points_task, favorite_feature_task]
    )














<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Management Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen flex flex-col justify-center items-center">
    <div class="bg-white p-8 rounded-lg shadow-md text-center max-w-md w-full">
        <h1 class="text-3xl font-bold mb-6 text-gray-800">Product Management Dashboard</h1>

        <p class="text-gray-600 mb-8">
            Unlock deep insights from customer reviews using advanced AI technology
        </p>

        <div class="space-y-4">
            <a href="/product-search" class="block bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-lg transition duration-300">
                Product Search
            </a>

            <a href="/company-search" class="block bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg transition duration-300">
                Company Search
            </a>
        </div>

        <p class="mt-8 text-sm text-gray-500">
            Powered by Large Language Models and Customer Review Analysis
        </p>
    </div>
</body>
</html>

















<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Search - Product Management Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
</head>
<body class="bg-gray-100 min-h-screen flex flex-col">
    <nav class="bg-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <a href="/" class="text-xl font-bold text-gray-800">Product Dashboard</a>
                <div class="space-x-4">
                    <a href="/product-search" class="text-blue-600 hover:text-blue-800">Product Search</a>
                    <a href="/company-search" class="text-green-600 hover:text-green-800">Company Search</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Loading Overlay -->
    <div id="loading-overlay" class="fixed inset-0 bg-gray-900 bg-opacity-50 hidden flex items-center justify-center z-50">
        <div class="bg-white p-8 rounded-lg shadow-xl text-center">
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 border-solid mx-auto mb-4"></div>
            <h2 class="text-xl font-semibold mb-2">Analyzing Product Reviews</h2>
            <p class="text-gray-600">Please wait while we analyze the reviews and generate insights...</p>
            <p class="text-sm text-gray-500 mt-2">This process may take up to 3 minutes</p>
        </div>
    </div>

    <main class="flex-grow container mx-auto px-4 py-8">
        <div class="max-w-xl mx-auto bg-white p-8 rounded-lg shadow-md">
            <h1 class="text-2xl font-bold mb-6 text-center text-gray-800">Product Search</h1>

            <div class="relative">
                <input
                    type="text"
                    id="product-search-input"
                    placeholder="Enter product name"
                    class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                <div
                    id="suggestions-container"
                    class="absolute z-10 w-full bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto hidden"
                >
                    <!-- Suggestions will be dynamically inserted here -->
                </div>
            </div>
        </div>
    </main>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const searchInput = document.getElementById('product-search-input');
            const suggestionsContainer = document.getElementById('suggestions-container');
            const loadingOverlay = document.getElementById('loading-overlay');

            searchInput.addEventListener('input', async (e) => {
                const query = e.target.value;

                if (query.length < 2) {
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.classList.add('hidden');
                    return;
                }

                try {
                    const response = await axios.get(`/get-product-suggestions?query=${encodeURIComponent(query)}`);
                    const suggestions = response.data;

                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.classList.remove('hidden');

                    if (suggestions.length === 0) {
                        suggestionsContainer.innerHTML = `
                            <div class="p-2 text-gray-500">No suggestions found</div>
                        `;
                        return;
                    }

                    suggestions.forEach(suggestion => {
                        const suggestionElement = document.createElement('div');
                        suggestionElement.textContent = suggestion;
                        suggestionElement.classList.add(
                            'p-2', 'cursor-pointer', 'hover:bg-blue-100',
                            'border-b', 'last:border-b-0', 'suggestion'
                        );

                        /*suggestionElement.addEventListener('click', () => {
                            // When a suggestion is clicked, redirect to the product insights page
                            window.location.href = `/product-insights/${encodeURIComponent(suggestion)}`;
                        });*/

                        suggestionsContainer.appendChild(suggestionElement);
                    });
                } catch (error) {
                    console.error('Error fetching suggestions:', error);
                }
            });

            async function handleProductSelection(suggestion) {
                // Show loading overlay
                loadingOverlay.classList.remove('hidden');
                console.log('Starting analysis for:', suggestion);

                try {
                    // Start the analysis process
                    const response = await axios.post('/start-analysis', {
                        product_title: suggestion
                    });

                    const taskId = response.data.task_id;
                    console.log('Received task ID:', taskId);

                    // Poll for results
                    let attempts = 0;
                    const maxAttempts = 90; // Increased from 30 to 90 (3 minutes total)

                    while (attempts < maxAttempts) {
                        console.log('Checking status, attempt:', attempts + 1);
                        const statusResponse = await axios.get(`/check-analysis-status/${taskId}`);
                        console.log('Status response:', statusResponse.data);

                        if (statusResponse.data.status === 'completed') {
                            console.log('Analysis completed, redirecting...');
                            window.location.href = `/product-insights/${encodeURIComponent(suggestion)}`;
                            break;
                        } else if (statusResponse.data.status === 'failed') {
                            console.error('Analysis failed:', statusResponse.data.error);
                            alert('Analysis failed. Please try again.');
                            loadingOverlay.classList.add('hidden');
                            break;
                        }

                        attempts++;
                        // Wait before next poll
                        await new Promise(resolve => setTimeout(resolve, 2000));
                    }

                    if (attempts >= maxAttempts) {
                        throw new Error('Analysis timeout');
                    }
                } catch (error) {
                    console.error('Error during analysis:', error);
                    alert('Analysis is taking longer than expected. Please try again.');
                    loadingOverlay.classList.add('hidden');
                }
            }

            // Update suggestion click handler
            suggestionsContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('suggestion')) {
                    handleProductSelection(e.target.textContent);
                }
            });


            // Close suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!suggestionsContainer.contains(e.target) && e.target !== searchInput) {
                    suggestionsContainer.classList.add('hidden');
                }
            });
        });
    </script>

    <footer class="bg-white shadow-md py-4">
        <p class="text-center text-gray-500">© 2024 Product Management Dashboard</p>
    </footer>
</body>
</html>















<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Insights - {{ product_title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .analysis-content {
            font-size: 0.95rem;
            line-height: 1.6;
            color: #374151;
        }
        .analysis-content strong {
            font-weight: 600;
            color: #111827;
            display: inline-block;
            margin-bottom: 0.5rem;
        }
        .analysis-content p {
            margin-bottom: 1rem;
        }
        .analysis-content ol {
            list-style-type: decimal;
            padding-left: 1.5rem;
            margin: 1rem 0;
        }
        .analysis-content li {
            margin-bottom: 1.5rem;
        }
        .analysis-content blockquote {
            background-color: #f3f4f6;
            border-left: 4px solid #e5e7eb;
            padding: 1rem;
            margin: 1rem 0;
            color: #4b5563;
            font-style: italic;
            border-radius: 0.25rem;
        }
        .analysis-content i {
            font-style: italic;
        }
        .product-stat-label {
            font-weight: 500;
            color: #6b7280;
        }
        .product-stat-value {
            font-weight: 600;
            color: #374151;
        }
        .insight-card {
            background-color: white;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            padding: 1.5rem;
            height: 100%;
        }
        .insight-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen flex flex-col">
    <nav class="bg-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <a href="/" class="text-xl font-bold text-gray-800">Product Dashboard</a>
                <div class="space-x-4">
                    <a href="/product-search" class="text-blue-600 hover:text-blue-800">Product Search</a>
                    <a href="/company-search" class="text-green-600 hover:text-green-800">Company Search</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="flex-grow container mx-auto px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <!-- Product Header -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h1 class="text-2xl font-bold mb-4 text-gray-900">{{ product_title }}</h1>

                {% if product_info %}
                <div class="grid grid-cols-2 gap-6">
                    <div class="space-y-2">
                        <p>
                            <span class="product-stat-label">Category:</span>
                            <span class="product-stat-value">{{ product_info['main_category'] }}</span>
                        </p>
                        <p>
                            <span class="product-stat-label">Average Rating:</span>
                            <span class="product-stat-value">{{ product_info['average_rating'] }}</span>
                        </p>
                    </div>
                    <div class="space-y-2">
                        <p>
                            <span class="product-stat-label">Total Reviews:</span>
                            <span class="product-stat-value">{{ product_info['rating_number'] }}</span>
                        </p>
                        <p>
                            <span class="product-stat-label">Price:</span>
                            <span class="product-stat-value">${{ product_info['price'] }}</span>
                        </p>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- AI Analysis Results -->
            {% if insights %}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Most Favorite Feature -->
                <div class="insight-card">
                    <h2 class="insight-title text-green-600">
                        Most Favorite Feature
                    </h2>
                    <div class="analysis-content">{{ insights.tasks_output[0] | safe }}</div>
                </div>

                <!-- Pain Points -->
                <div class="insight-card">
                    <h2 class="insight-title text-red-600">
                        Top Pain Points
                    </h2>
                    <div class="analysis-content">{{ insights.tasks_output[1] | safe }}</div>
                </div>

                <!-- Suggested Improvement -->
                <div class="insight-card col-span-2">
                    <h2 class="insight-title text-blue-600">
                        Recommended Improvement
                    </h2>
                    <div class="analysis-content">{{ insights.tasks_output[2] | safe }}</div>
                </div>
            </div>
            {% endif %}
        </div>
    </main>

    <footer class="bg-white shadow-md py-4 mt-8">
        <p class="text-center text-gray-500">© 2024 Product Management Dashboard</p>
    </footer>
</body>
</html>










def soup2list(src, list_, attr=None):
    if attr:
        for val in src:
            list_.append(val[attr])
    else:
        for val in src:
            list_.append(val.get_text())

users = []
#userReviewNum = []
ratings = []
locations = []
dates = []
reviews = []

from_page = 1
to_page = 4
company = 'www.pearsonvue.co.uk'

for i in range(from_page, to_page+1):

   result = requests.get(fr"https://www.trustpilot.com/review/{company}?page={i}")
   soup = BeautifulSoup(result.content)

   # Trust Pilot was setup in a way that's not friendly to scraping, so this hacky method will do.
   soup2list(soup.find_all('span', {'class','typography_heading-xxs__QKBS8 typography_appearance-default__AAY17'}), users)
   soup2list(soup.find_all('div', {'class','typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_detailsIcon__Fo_ua'}), locations)
   #soup2list(soup.find_all('span', {'class','typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l'}), userReviewNum)
   soup2list(soup.find_all('div', {'class','styles_reviewHeader__iU9Px'}), dates)
   soup2list(soup.find_all('div', {'class','styles_reviewHeader__iU9Px'}), ratings, attr='data-service-review-rating')
   soup2list(soup.find_all('div', {'class','styles_reviewContent__0Q2Tg'}), reviews)

   # To avoid throttling
   sleep(1)



review_data = pd.DataFrame(
{
   'Username':users,
   #'Total reviews':userReviewNum,
   'location':locations,
   'date':dates,
   'review':reviews,
   'rating': ratings
})

print(review_data)





















# Step 1: Quick company metadata analysis
    metadata_task = Task(
        description=f"""
        Provide 4-5 key business characteristics for {company_name}.

        Provide your analysis in the following HTML structure:
        <div class="metadata-points">
            <p><strong>Business Type:</strong> [Primary business description]</p>
            <p><strong>Core Offerings:</strong> [Main products/services]</p>
            <p><strong>Customer Base:</strong> [Target audience]</p>
            <p><strong>Market Presence:</strong> [Geographic scope]</p>
        </div>

        Guidelines:
        - Keep each point concise and factual
        - Focus on widely known information
        - Keep descriptions objective
        - Keep formatting clean and consistent
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=metadata_agent,
        expected_output="Concise HTML-formatted company metadata points."
    )

    # Step 2: Review-based tasks
    strengths_task = Task(
        description=f"""
        Analyze these customer reviews and identify 3-4 key company strengths.

        Reviews:
        {reviews_text}

        Provide your analysis in the following HTML structure:
        <p>[Brief introduction about the company's strengths]</p>
        <ol>
            <li>
                <strong>[Strength Name]</strong>
                <p>[Description of why this aspect is praised]</p>
                <blockquote>[Supporting customer quote]</blockquote>
            </li>
        </ol>

        Guidelines:
        - Include direct customer quotes within blockquote tags
        - Keep formatting clean and consistent
        - Format all emphasis using <strong> tags
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=feature_analyst,
        expected_output="A structured HTML analysis of company strengths.",
        context=[metadata_task]  # Provide company context
    )

    pain_points_task = Task(
        description=f"""
        Analyze these customer reviews and identify the top 3 pain points.

        Reviews:
        {reviews_text}

        Provide your analysis in the following HTML structure:
        <p>[Brief introduction about key issues]</p>
        <ol>
            <li>
                <strong>[Pain Point Name]</strong>
                <p>[Description and business impact]</p>
                <blockquote>[Supporting customer quote]</blockquote>
            </li>
        </ol>

        Guidelines:s
        - Include direct customer quotes within blockquote tags
        - Keep formatting clean and consistent
        - Format all emphasis using <strong> tags
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=pain_point_analyst,
        expected_output="A structured HTML analysis of key pain points.",
        context=[metadata_task]  # Provide company context
    )

    # Step 3: Strategic recommendations
    strategy_task = Task(
        description=f"""
        Based on the company profile and analysis, propose key strategic improvements.
        Use the metadata and review analyses to inform your recommendations.

        Provide your analysis in the following HTML format:
        <p>[Introduction and context]</p>

        <strong>Strategic Priority</strong>
        <p>[Key improvement focus]</p>

        <strong>Detailed Recommendations</strong>
        <ol>
            <li>
                <strong>[Strategy Name]</strong>
                <p>[Implementation details]</p>
                <p>[Expected impact]</p>
            </li>
        </ol>

        <strong>Implementation Approach</strong>
        <p>[Execution strategy]</p>

        <p><strong>Expected Outcomes</strong></p>
        <p>[Business benefits]</p>

        Guidelines:
        - Include direct customer quotes within blockquote tags
        - Keep formatting clean and consistent
        - Format all emphasis using <strong> tags
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=business_strategist,
        expected_output="A comprehensive HTML-formatted strategic plan.",
        context=[metadata_task, strengths_task, pain_points_task]




    <style>
        .card-3d {
            transform-style: preserve-3d;
            transition: all 0.3s ease;
        }
        .card-3d:hover {
            transform: translateY(-10px) rotateX(4deg);
        }
        .gradient-text {
            background: linear-gradient(135deg, #3b82f6 0%, #2dd4bf 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .search-card {
            transition: all 0.3s ease;
            border: 1px solid rgba(59, 130, 246, 0.1);
        }
        .search-card:focus-within {
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.3);
        }
    </style>

























def analyze_company_reviews(company_url: str, reviews_df: pd.DataFrame):
    """
    Analyze company reviews using CrewAI agents with metadata generation
    """
    # Clean company URL to get company name
    company_name = clean_company_url(company_url).split('.')[0].replace('-', ' ').title()

    # Convert DataFrame to text format for analysis
    reviews_text = "\n".join([
        f"Review: {row['review']}"
        for row in reviews_df.to_dict('records')
    ])

    # Define the agents
    metadata_agent = Agent(
        role='Company Metadata Analyst',
        goal='Extract key company metadata from company name',
        backstory="""You are a business insight specialist who excels at identifying
        key business characteristics and company profiles. You can provide accurate,
        concise company information based on widely known facts.""",
        verbose=True,
        tools=[]
    )

    feature_analyst = Agent(
        role='Feature Analysis Specialist',
        goal='Identify and analyze company strengths from customer reviews',
        backstory="""You are an experienced business analyst specializing in
        identifying key company strengths and their impact on customer satisfaction.""",
        verbose=True,
        tools=[]
    )

    pain_point_analyst = Agent(
        role='Customer Pain Point Specialist',
        goal='Identify and categorize customer pain points and frustrations',
        backstory="""You are an expert in customer experience analysis, focusing on
        identifying and understanding customer problems and negative experiences.""",
        verbose=True,
        tools=[]
    )

    business_strategist = Agent(
        role='Lead Business Strategist',
        goal='Develop strategic improvements based on comprehensive analysis',
        backstory="""You are a strategic business consultant who excels at
        transforming analysis into actionable business improvements.""",
        verbose=True,
        llm='gpt-4o',
        tools=[]
    )

    # Step 1: Quick company metadata analysis
    metadata_task = Task(
        description=f"""
        As a Company Metadata Analyst, provide key business characteristics for {company_name}.

        Structure your response in clean, formatted HTML:
        <div class="metadata-grid">
            <!-- Business Type -->
            <div class="metadata-item">
                <div class="metadata-label">Business Type:</div>
                <div class="metadata-value">[Primary business description]</div>
            </div>

            <!-- Core Offerings -->
            <div class="metadata-item">
                <div class="metadata-label">Core Offerings:</div>
                <div class="metadata-value">[Main products/services]</div>
            </div>

            <!-- Customer Base -->
            <div class="metadata-item">
                <div class="metadata-label">Customer Base:</div>
                <div class="metadata-value">[Target audience]</div>
            </div>

            <!-- Market Presence -->
            <div class="metadata-item">
                <div class="metadata-label">Market Presence:</div>
                <div class="metadata-value">[Geographic scope]</div>
            </div>
        </div>

        Guidelines:
        - Keep each point concise and factual based on widely known information
        - Keep formatting clean and consistent
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=metadata_agent,
        expected_output="Concise HTML-formatted company metadata points."
    )

    # Step 2: Review-based tasks
    strengths_task = Task(
        description=f"""
        Analyze these customer reviews and identify the 3 or 4 most frequently praised and appreciated features of the product.
        Only include positive findings.

        Reviews:
        {reviews_text}

        Structure your response in clean, formatted HTML:
        <div class="analysis-section">
            <p class="section-intro">[Brief introduction praised feature]</p>

            <div class="strengths-list">
                <div class="strength-item">
                    <h3 class="strength-title">[Feature Name]</h3>
                    <p class="strength-description">[Detailed description]</p>
                    <blockquote class="customer-quote">
                        "[Insert relevant customer quote]"
                    </blockquote>
                </div>
                <!-- Repeat for each feature -->
            </div>
        </div>

        Guidelines:
        - Include direct customer quotes within blockquote tags
        - Keep formatting clean and consistent
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=feature_analyst,
        expected_output="A structured HTML analysis of favorite features.",
        context=[metadata_task]  # Provide company context
    )

    pain_points_task = Task(
        description=f"""
        Analyze these customer reviews and identify the top 3 pain points.

        Reviews:
        {reviews_text}

        Analyze the customer reviews and identify the top 3 most significant pain points.

        Structure your response in clean, formatted HTML:
        <div class="analysis-section">
            <p class="section-intro">[Brief introduction about key challenges]</p>

            <div class="challenges-list">
                <div class="challenge-item">
                    <h3 class="challenge-title">[Challenge Name]</h3>
                    <p class="challenge-description">[Detailed description and impact]</p>
                    <blockquote class="customer-quote">
                        "[Supporting customer quote]"
                    </blockquote>
                </div>
                <!-- Repeat for each challenge -->
            </div>
        </div>

        Guidelines:
        - Include direct customer quotes within blockquote tags
        - Keep formatting clean and consistent
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=pain_point_analyst,
        expected_output="A structured HTML analysis of key pain points.",
        context=[metadata_task]  # Provide company context
    )

    # Step 3: Strategic recommendations
    strategy_task = Task(
        description=f"""
        Based on the analysis, propose strategic improvements.

        Structure your response in clean, formatted HTML:
        <div class="strategy-section">
            <p class="strategy-intro">
                [Overview introduction of strategic recommendations]
            </p>

            <div class="strategy-recommendations">
                <!-- First Strategy -->
                <div class="strategy-item">
                    <h3 class="strategy-heading">[First Strategy Title]</h3>
                    <p class="strategy-description">
                        [Detailed explanation of the strategy]
                    </p>

                    <div class="implementation-section">
                        <h4>Implementation Approach</h4>
                        <ol class="implementation-steps">
                            <li>
                                <strong>[Step 1 Title]:</strong>
                                [Step 1 description]
                            </li>
                            <li>
                                <strong>[Step 2 Title]:</strong>
                                [Step 2 description]
                            </li>
                            <li>
                                <strong>[Step 3 Title]:</strong>
                                [Step 3 description]
                            </li>
                        </ol>
                    </div>

                    <div class="outcomes-section">
                        <h4>Expected Outcomes</h4>
                        <ul class="outcome-list">
                            <li>[First expected outcome]</li>
                            <li>[Second expected outcome]</li>
                        </ul>
                    </div>
                </div>

                <!-- Second Strategy (if needed) -->
                <div class="strategy-item">
                    <h3 class="strategy-heading">[Second Strategy Title]</h3>
                    <!-- Same structure as above -->
                </div>
            </div>
        </div>

        Guidelines:
        - Maintain consistent HTML formatting
        - Keep paragraphs focused and concise
        - Don't include "```html" in your output
        """,
        agent=business_strategist,
        expected_output="A comprehensive HTML-formatted strategic plan.",
        context=[metadata_task, strengths_task, pain_points_task]
    )

    # Create and run the crew
    crew = Crew(
        agents=[metadata_agent, feature_analyst, pain_point_analyst, business_strategist],
        tasks=[metadata_task, strengths_task, pain_points_task, strategy_task],
        process=Process.sequential
    )
