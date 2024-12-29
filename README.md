# The Product Management Dashboard
This web-based dashboard leverages AI to analyze customer reviews and provide actionable product and business development insights for product managers and business analysts. The application offers two main functionalities: Product Search and Company Search, each providing detailed analysis using large language models.

Demo Webapp: https://ai-powered-product-management-dashboard.onrender.com/
Demo Video: https://www.youtube.com/watch?v=X_eu3lVCRuM

## Features
The application has two main features:

1. Product Search
Use the search function to analyze a specific product. This MVP includes popular electronics products available on Amazon during 2023. Selecting a product will start an automatized customer review analysis based on customer sentiment and feedback. You will be taken to a product insights page, which will use artificial intelligence to provide detailed insights on customers' Most Favorite Features, Top Pain Points, and what Features a product manager should build to improve customer satisfaction.

2. Company Search
To use the company search function, the user inputs a company's URL to generate automatized insights. When searching for a company's URL, reviews are read in real-time from Trustpilot (a business review website). These reviews are used to generate a comprehensive company analysis that includes Company Metadata (Business Type, Core Offerings, etc.), Product Strengths, Key Challenges, and Strategic Recommendations to improve the product offering and customer satisfaction.

## AI Agents
* The application leverages the CrewAI framework. The framework enables creation of specific AI Agents that work together to solve various defined tasks to complete an overarching goal.
* The agents created for the application are a Feature Analysis Specialist, a Customer Pain Point Specialist, a Product Manager, a Business Strategist, and a Metadata Analyst.
* The agents are powered by either GPT-4o or GPT-4o mini for their tasks depending on the amount of expected needed tokens (cost) and the level of reasoning needed for the task (quality)


## Running the application

### Prerequisites
* Python 3.8 or higher
* pip package manager
* Installation of required packages: pip install -r requirements.txt
* Importing an OpenAI API key into helpers.py to enable the AI agents to run.

### Launch
* Run the flask application: python app.py
* Navigate to a browser with http://localhost:5000

### Error handling
The application includes error handling for:
* Invalid product/company searches
* Insufficient review count
* API failures
* Network issues
* Database connection problems
* And more...


## Limitations and Considerations
* An OpenAI API key needs to be imported into helpers to enable the AI agents to run.
* The MVP of the Product search is limited to electronic products popular in 2023 from the Amazon Reviews database
* Company search requires the company to have at least 4 pages of Trustpilot reviews
* Analysis time varies based on the number of reviews

## Opportunities
* Upload proprietary company review data to adapt product search to any product
* Increase amount of reviews to be analyzed to optimize output
* Implement more AI agents to generate more insights. For example: Pricing feedback, trends over time following feature implentation, identifying SEO keywords related to customer language, market insights, analyze competitors' reviews for market insights and differentiation.

## References


## Support
* In case of issues or quesitons, feel free to reach out to axel.svensson@yale.edu
