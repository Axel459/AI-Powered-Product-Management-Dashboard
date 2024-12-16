import pandas as pd
from crewai import Agent, Task, Crew, Process
import sqlite3
from typing import List, Dict
import os

os.environ['OPENAI_API_KEY'] = ""
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4o-mini'

def get_db_connection():
    """
    Establish a connection to the SQLite database
    """
    conn = sqlite3.connect('amazon_reviews_filtered.db')
    conn.row_factory = sqlite3.Row
    return conn

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


def get_product_metadata(product_title):
    """
    Fetch product metadata from database
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, features
        FROM metadata
        WHERE title = ?
        LIMIT 1
    """, (product_title,))

    result = cursor.fetchone()
    conn.close()
    return result



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

product_manager = Agent(
    role='Lead Product Manager',
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

    product_metadata = get_product_metadata(product_title)


    # Define tasks
    favorite_feature_task = Task(
        description=f"""
        Analyze these customer reviews and identify the 3 or 4 most frequently praised and appreciated features of the product.
        Only include positive findings.

        Reviews:
        {reviews_text}

        Provide your analysis in the following HTML structure:

        <p>[Write a brief introduction about your analysis approach and general findings]</p>

        <ol>
            <li>
                <strong>[Feature Name]</strong>
                <p>[Description of why this feature is praised]</p>
                <blockquote>[Insert relevant customer quote]</blockquote>
            </li>
            <!-- Repeat for each major feature -->
        </ol>

        Guidelines:
        - Don't reference specific review numbers
        - Include direct customer quotes within blockquote tags
        - Keep formatting clean and consistent
        - Format all emphasis using <strong> tags
        - Ensure proper nesting of HTML elements
        - Don't include "```html" in your output
        """,
        agent=feature_analyst,
        async_execution=True,
        expected_output="A structured HTML analysis of the most liked and praised product features with supporting evidence."
    )

    pain_points_task = Task(
        description=f"""
        Analyze these customer reviews and identify the top 3 most significant pain points.

        Reviews:
        {reviews_text}

        Provide your analysis in the following HTML structure:

        <p>[Write a brief introduction about your findings and their significance]</p>

        <ol>
            <li>
                <strong>[Pain Point Name]</strong>
                <p>[Detailed description of the issue and its impact]</p>
                <blockquote>[Relevant customer quote illustrating the problem]</blockquote>
                <p>[Explanation of broader impact on customer experience]</p>
            </li>
            <!-- Repeat for each pain point -->
        </ol>

        Guidelines:
        - Focus on the top 3 most significant issues
        - Don't reference specific review numbers
        - Include relevant customer quotes in blockquote tags
        - Keep formatting clean and consistent
        - Use proper HTML hierarchy
        - Don't include "```html" in your output
        """,
        agent=pain_point_analyst,
        async_execution=True,
        expected_output="A structured HTML analysis of the top 3 customer pain points with supporting evidence."
    )

    improvement_task = Task(
        description=f"""
        As a Product Manager, propose the single most impactful feature improvement for {product_title}.

        Product Information:
        - Current Features: {product_metadata['features'] if product_metadata else 'Not available'}

        Based on the previous pain point analysis, structure your proposal in the following HTML format:

        <p>[Brief introduction summarizing the need for improvement]</p>

        <strong>Feature Name and Brief Overview</strong>
        <p>[Concise description of the proposed feature/improvement]</p>

        <strong>Detailed Description</strong>
        <p>[Comprehensive explanation of the improvement]</p>

        <strong>Addressing Pain Points</strong>
        <ol>
            <li><p>[Specific pain point and how this feature addresses it]</p></li>
            <!-- Repeat for each addressed pain point -->
        </ol>

        <strong>Expected Impact</strong>
        <ol>
            <li><p>[Specific benefit or improvement]</p></li>
            <!-- List key benefits -->
        </ol>

        <strong>Technical Feasibility</strong>
        <p>[Assessment of implementation complexity and requirements]</p>

        <strong>Implementation Priority</strong>
        <p>[Priority level with justification]</p>

        <p><strong>Conclusion</strong></p>
        <p>[Summary of key benefits and expected outcomes]</p>

        Guidelines:
        - Maintain consistent HTML formatting
        - Use proper heading hierarchy
        - Keep paragraphs focused and concise
        - Use lists for multiple points
        - Ensure all sections are clearly labeled
        - Don't include "```html" in your output
        """,
        agent=product_manager,
        expected_output="A comprehensive HTML-formatted feature improvement proposal.",
        context=[pain_points_task, favorite_feature_task]
    )


    # Create and run the crew
    crew = Crew(
        agents=[feature_analyst, pain_point_analyst, product_manager],
        tasks=[favorite_feature_task,
                pain_points_task, improvement_task],
        process=Process.sequential  # Tasks will run in sequence
    )

    result = crew.kickoff()
    return result



# -------------- Company Analysis Crew -----------------



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
        transforming analysis into actionable product improvements.""",
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
        - Don't include "```html" in your answer
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
        async_execution=True,
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
        async_execution=True,
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
        - Don't include "```html" or "```" in your answer please
        - Keep paragraphs focused and concise
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


    result = crew.kickoff()
    return result


def clean_company_url(url: str) -> str:
    """Clean and format company URL"""
    # Remove common prefixes
    url = url.lower().strip()
    url = url.replace('http://', '').replace('https://', '').replace('www.', '')

    # Remove any paths or parameters
    url = url.split('/')[0]

    return url.strip()
