"""
Function Schemas for Google Gemini Function Calling

Defines the schema for all query functions that Gemini can call
"""

import google.generativeai as genai

# Define function declarations for Gemini
query_spending_func = genai.protos.FunctionDeclaration(
    name="query_spending",
    description="Query total spending filtered by merchant name, category, and/or time range. Returns spending totals, transaction counts, and comparisons to average.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "merchant": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Merchant name to filter by (e.g., 'Starbucks', 'Amazon', 'Whole Foods'). Will be fuzzy matched to handle typos."
            ),
            "category": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Spending category to filter by (e.g., 'Gas', 'Dining', 'Groceries', 'Shopping', 'Travel')"
            ),
            "time_range": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="ONLY use this if user says exact phrases like 'this month' or 'last year'. Otherwise, calculate custom dates and use start_date/end_date instead.",
                enum=["this_month", "last_month", "this_year", "last_year", "last_30_days", "last_90_days", "all_time"]
            ),
            "start_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom start date in YYYY-MM-DD format. Calculate this based on the user's query. Today is 2025-12-31. For 'last 2 months' use '2025-10-31', for 'past 3 weeks' use '2025-12-10', etc. Must be used with end_date."
            ),
            "end_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom end date in YYYY-MM-DD format. Typically this should be '2025-12-31' (today). Must be used with start_date."
            )
        }
    )
)

get_top_merchants_func = genai.protos.FunctionDeclaration(
    name="get_top_merchants",
    description="Get a ranked list of merchants by total spending amount. Useful for answering 'Where does my money go?' or 'What are my top merchants?'",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "time_range": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="ONLY use if user says exact phrases like 'this month'. Otherwise use start_date/end_date.",
                enum=["this_month", "last_month", "this_year", "last_year", "last_30_days", "last_90_days", "all_time"]
            ),
            "top_n": genai.protos.Schema(
                type=genai.protos.Type.INTEGER,
                description="Number of top merchants to return (default: 5)"
            ),
            "category_filter": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Optional category filter to narrow down merchants (e.g., 'Dining' to see top restaurants)"
            ),
            "start_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom start date in YYYY-MM-DD format. Calculate based on user's query. Today is 2025-12-31."
            ),
            "end_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom end date in YYYY-MM-DD format. Typically '2025-12-31' (today)."
            )
        }
    )
)

get_top_categories_func = genai.protos.FunctionDeclaration(
    name="get_top_categories",
    description="Get a ranked list of spending categories by total amount. Useful for answering 'What are my biggest spending categories?' or 'How do I spend my money?'",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "time_range": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="ONLY use if user says exact phrases like 'this month'. Otherwise use start_date/end_date.",
                enum=["this_month", "last_month", "this_year", "last_year", "last_30_days", "last_90_days", "all_time"]
            ),
            "top_n": genai.protos.Schema(
                type=genai.protos.Type.INTEGER,
                description="Number of top categories to return (default: 5)"
            ),
            "start_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom start date in YYYY-MM-DD format. Calculate based on user's query. Today is 2025-12-31."
            ),
            "end_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom end date in YYYY-MM-DD format. Typically '2025-12-31' (today)."
            )
        }
    )
)

compare_spending_func = genai.protos.FunctionDeclaration(
    name="compare_spending",
    description="Compare spending between two time periods and calculate the dollar and percentage change. Useful for answering 'Am I spending more this month?' or 'How does my spending compare to last year?'",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "period1": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="First time period to compare",
                enum=["this_month", "last_month", "this_year", "last_year", "last_30_days", "last_90_days"]
            ),
            "period2": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Second time period to compare",
                enum=["this_month", "last_month", "this_year", "last_year", "last_30_days", "last_90_days"]
            ),
            "merchant_filter": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Optional merchant name to filter comparison (e.g., 'Starbucks')"
            ),
            "category_filter": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Optional category to filter comparison (e.g., 'DINING')"
            )
        },
        required=["period1", "period2"]
    )
)

get_subscriptions_func = genai.protos.FunctionDeclaration(
    name="get_subscriptions",
    description="Get all detected recurring subscriptions including gray charges (potentially forgotten subscriptions) and recent price increases.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={}
    )
)

get_goal_progress_func = genai.protos.FunctionDeclaration(
    name="get_goal_progress",
    description="Get progress on all active savings goals including target amounts, current savings, and deadline information.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={}
    )
)

get_transaction_details_func = genai.protos.FunctionDeclaration(
    name="get_transaction_details",
    description="Search for specific transactions by type (recent, largest) or by merchant keyword.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "search_type": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Type of search: 'recent' for most recent transactions, 'largest' for biggest purchases, 'search' to search by merchant keyword",
                enum=["recent", "largest", "search"]
            ),
            "merchant_keyword": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Keyword to search in merchant names (required if search_type is 'search')"
            ),
            "limit": genai.protos.Schema(
                type=genai.protos.Type.INTEGER,
                description="Number of transactions to return (default: 10)"
            )
        }
    )
)

get_financial_summary_func = genai.protos.FunctionDeclaration(
    name="get_financial_summary",
    description="Get a holistic financial overview including total income, spending, net savings, savings rate, and category breakdown for a given time period.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "time_range": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="ONLY use if user says exact phrases like 'this month'. Otherwise use start_date/end_date.",
                enum=["this_month", "last_month", "this_year", "last_year", "last_30_days", "last_90_days"]
            ),
            "start_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom start date in YYYY-MM-DD format. Calculate based on user's query. Today is 2025-12-31."
            ),
            "end_date": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="PREFERRED: Custom end date in YYYY-MM-DD format. Typically '2025-12-31' (today)."
            )
        }
    )
)

# Combine all function declarations into a tool
GEMINI_FUNCTION_SCHEMAS = [
    genai.protos.Tool(
        function_declarations=[
            query_spending_func,
            get_top_merchants_func,
            get_top_categories_func,
            compare_spending_func,
            get_subscriptions_func,
            get_goal_progress_func,
            get_transaction_details_func,
            get_financial_summary_func
        ]
    )
]
