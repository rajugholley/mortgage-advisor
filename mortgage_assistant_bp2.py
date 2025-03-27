import streamlit as st
from anthropic import Anthropic
import sqlite3
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ConversationalMortgageAgent:
    def __init__(self):
        """Initialize the mortgage agent with empty state"""
        self.db_path = 'mortgage_products.db'  # Define this first
        self.state = {
            'conversation_history': [],
            'collected_info': {},
            'conversation_stage': 'initial',
            'products': self.get_products_from_db(),
            'serviceability_metrics': {},
            'borrowing_power': 0,
            'steps_completed': {
                'purpose_identified': False,
                'personal_details_collected': False,
                'financial_info_collected': False,
                'borrowing_power_calculated': False,
                'property_details_collected': False,
                'preferences_collected': False,
                'analysis_complete': False,
                'recommendations_provided': False
            }
        }
        self.conversation_stages = [
            'initial',           # Initial greeting
            'purpose',           # Identify mortgage purpose
            'personal_details',  # Collect name, dependents, employment type
            'financial_info',    # Collect income, expenses, debts
            'borrowing_power',   # Calculate and show borrowing capacity
            'basic_financials',  # Collect property value, deposit
            'preferences',       # Collect loan preferences (fixed/variable, term)
            'serviceability',    # Calculate and display LVR, DSR, credit impact
            'what_if',           # Show what-if scenarios for interest rate changes
            'recommendations',   # Provide product recommendations
            'followup'           # Handle additional questions
        ]
    
    def get_products_from_db(self):
        """Fetch mortgage products from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT * FROM mortgage_products')
            columns = [description[0] for description in c.description]
            products = [dict(zip(columns, row)) for row in c.fetchall()]
            conn.close()
            return products
        except Exception as e:
            print(f"Error fetching products from DB: {e}")
            # Return some sample products as fallback
            return [
                {"product_id": 1, "product_name": "Fixed Rate Home Loan", "rate_type": "fixed", "min_income": 60000, "min_deposit": 0.1, "interest_rate": "3.5%", "comparison_rate": "3.7%", "offset_account": "No", "redraw_facility": "No", "extra_repayments": "Yes"},
                {"product_id": 2, "product_name": "Variable Rate Home Loan", "rate_type": "variable", "min_income": 60000, "min_deposit": 0.1, "interest_rate": "3.2%", "comparison_rate": "3.4%", "offset_account": "Yes", "redraw_facility": "Yes", "extra_repayments": "Yes"},
                {"product_id": 3, "product_name": "Low Rate Home Loan", "rate_type": "variable", "min_income": 80000, "min_deposit": 0.2, "interest_rate": "2.9%", "comparison_rate": "3.1%", "offset_account": "Yes", "redraw_facility": "Yes", "extra_repayments": "Yes"}
            ]

    def get_system_prompt(self):
        """Generate system prompt based on current conversation state"""
        base_prompt = f"""You are a highly experienced and seasoned mortgage loan officer in Australia. Follow these instructions EXACTLY:

        [INTERNAL GUIDELINES - DO NOT SHOW IN RESPONSE]
        Current Conversation Stage: {self.state['conversation_stage']}
        Steps Completed: {self.state['steps_completed']}
        
        Response Formatting (CRITICAL - FOLLOW PRECISELY):
        - Keep ALL responses under 100 words
        - NEVER use more than 2 sentences in a row without a line break
        - Each bullet point MUST be on its own line with line breaks between bullets
        - Format bullet points as:
          • Question 1?
          
          • Question 2?
          
          • Question 3?
        - Always use spaces between words and after punctuation
        - Format ALL numbers as plain text with spaces: $1,300,000 (never inside formatting marks)
        - Format ALL percentages as plain text with spaces: 23% (never inside formatting marks)
        - NEVER merge words together - always use proper spacing
        - NEVER use italics or markdown formatting for regular text
        
        TABLES MUST BE FORMATTED EXACTLY AS FOLLOWS (this is critical):
        ```
        | Column 1 | Column 2 | Column 3 |
        |----------|----------|----------|
        | Value 1  | Value 2  | Value 3  |
        | Value 4  | Value 5  | Value 6  |
        ```
        - Always use proper table markdown with pipes and dashes
        - Include header row separation with dashes
        - Always include spaces between pipes and content
        - Never use bold or formatting inside table cells
        - Use plain text numbers in tables
        
        PRODUCT RECOMMENDATIONS:
        - ALWAYS present product recommendations in a table format like this:
        ```
        | Feature        | Details       |
        |----------------|---------------|
        | Interest Rate  | 3.5%          |
        | Monthly Payment| $3,847        |
        | Loan Amount    | $1,000,000    |
        ```
        - Follow recommendation tables with bullet points for key benefits
        - Maximum 3 bullet points per recommendation
        
        INTEREST RATE SCENARIOS:
        - ALWAYS present interest rate scenarios in a table format like this:
        ```
        | Rate Scenario | Monthly Payment | Change   |
        |--------------|-----------------|----------|
        | 3.5% (current)| $4,500         | -        |
        | 4.0%         | $4,750          | +$250    |
        | 4.5%         | $5,000          | +$500    |
        ```
        [END INTERNAL GUIDELINES]
        
        Conversation Approach:
        1. Initial Engagement
        - Warmly greet the customer like an actual loan officer
        - Ask about mortgage goals (first home, investment, refinancing)
        - Be conversational and supportive

        2. Personal Data Collection - MUST COLLECT UNDER ONE QUESTION AS SEPARATE BULLET POINTS ONE UNDER THE OTHER:
        - Ask about Name 
        - Ask about no of dependants 
        - Ask about employement type

        3. Financial Information Collection - MUST COLLECT BEFORE PROPERTY DETAILS AS SEPARATE BULLETS ONE UNDER THE OTHER:
        - Ask about annual income (before tax)
        - Ask about monthly expenses
        - Ask about existing debts (credit cards, personal loans, etc.)
        
        4. Borrowing Power Calculation - REQUIRED BEFORE PROPERTY DISCUSSION AND NOT TO BE SKIPPED AT ALL:
        - Calculate and show maximum borrowing capacity
        - Explain this is what banks would likely approve
        - Set realistic expectations before discussing property values
                
        5. Property Details Collection - ONLY AFTER BORROWING POWER IS ESTABLISHED AND NOT TO BE SKIPPED AT ALL:
        - Ask about property value, location and deposit
        - Ensure property value is realistic given borrowing capacity
        - Mention relevant government incentives for first-time buyers
        
        6. Loan Preferences - MUST ASK THESE QUESTIONS UNDER ONE QUESTION AS SEPARATE BULLETS POINTS ONE UNDER THE OTHER:
        - Ask about fixed or variable rate preference
        - If customer ask, what is fixed , variable , explain and then continue this flow to next question
        - Ask about desired loan term/tenure (e.g., 15, 20, 30 years)
        - Ask about long-term goals and life events
        
        7. Financial Analysis - ALWAYS EXPLAIN THESE METRICS WITHOUT FAIL:
        - LVR (Loan-to-Value Ratio) and its impact on rates and LMI
        - Serviceability (DSR - Debt Service Ratio)
        - Impact of credit score on borrowing capacity
    
        Ask if customer provides consent to access their credit bureau score. If they do, just show them a good score and say "Congrats, your credit score look good". The move to next step below

        8. Risk Assessment - ALWAYS DISCUSS INTEREST RATE SCENARIOS MANDATORILY:
        - Show how potential rate rises would affect repayments
        - Discuss buffer needs for unexpected life events
        
        9. Recommendations - THIS IS MANDATORY
        - Present options in clear tables
        - Explain why each option suits their situation
        - Compare features and benefits
        - Consider future flexibility needs

        Current State:
        Previously collected information: {self.state['collected_info']}
        Available products: {self.state['products']}
        Customer preferences: {self.state.get('customer_preferences', {})}
        Customer goals: {self.state.get('customer_goals', {})}
        """
        
        # Add specific instructions based on conversation stage
        if self.state['conversation_stage'] == 'what_if':
            loan_amount = self.state['collected_info'].get('loan_amount', 0)
            property_value = self.state['collected_info'].get('property_value', 0)
            income = self.state['collected_info'].get('income', 0)
            
            # Get base interest rate
            base_rate = 3.5  # Default fallback rate
            for product in self.state['products']:
                if isinstance(product, dict) and 'interest_rate' in product:
                    try:
                        rate_str = product['interest_rate'].strip('%')
                        base_rate = float(rate_str)
                        break
                    except (ValueError, AttributeError):
                        continue
            
            # Generate what-if analysis
            rate_analysis = self.analyze_rate_impact(loan_amount, base_rate)
            
            # Create example table with proper formatting
            example_table = """
            | Rate Scenario | Monthly Payment | Change  |
            |--------------|-----------------|---------|
            | 3.5% (current)| $4,500         | -       |
            | 4.0%         | $4,750          | +$250   |
            | 4.5%         | $5,000          | +$500   |
            | 5.0%         | $5,250          | +$750   |
            | 5.5%         | $5,500          | +$1,000 |
            """
            
            base_prompt += f"""
            \nFOCUS ON: Showing interest rate impact clearly using a properly formatted table.
            
            IMPORTANT: Your response MUST include a table formatted EXACTLY like this example:
            {example_table}
            
            Replace the values with the actual calculated values, but keep the exact table structure.
            """
            
        elif self.state['conversation_stage'] == 'recommendations':
            # Create example recommendation table with proper formatting
            example_table = """
            | Feature       | Details       |
            |---------------|---------------|
            | Interest Rate | 3.5%          |
            | Monthly Payment | $3,847      |
            | Loan Amount   | $1,000,000    |
            | Loan Term     | 30 years      |
            | Loan Type     | Fixed Rate    |
            """
            
            base_prompt += f"""
            \nFOCUS ON: Presenting mortgage options clearly in properly formatted tables.
            
            IMPORTANT: Your response MUST include product tables formatted EXACTLY like this example:
            {example_table}
            
            Replace the values with the actual product details, but keep the exact table structure.
            
            After each table, include 2-3 bullet points about key benefits, each on its own line.
            """
        
        if 'mortgage_purpose' in self.state['collected_info']:
            base_prompt += f"\nCustomer Purpose: {self.state['collected_info']['mortgage_purpose']}"
        
        return base_prompt
    
    def calculate_max_loan(self, monthly_payment, annual_interest_rate, years):
        """Calculate maximum loan amount based on monthly payment capacity"""
        monthly_rate = annual_interest_rate / 12
        num_payments = years * 12
        
        # Using the formula: PV = PMT / [r * (1 + r)^n / ((1 + r)^n - 1)]
        if monthly_rate == 0:
            max_loan = monthly_payment * num_payments
        else:
            max_loan = monthly_payment * ((1 - (1 + monthly_rate) ** -num_payments) / monthly_rate)
        
        return max_loan
    
    def get_lvr_assessment(self, lvr):
        """Provide assessment based on LVR value"""
        if lvr < 0.8:
            return "Good - No LMI required"
        elif lvr < 0.9:
            return "Moderate - LMI will apply"
        else:
            return "High - Significant LMI cost"
    
    def get_dsr_assessment(self, dsr):
        """Provide assessment based on DSR value"""
        if dsr < 0.3:
            return "Excellent serviceability"
        elif dsr < 0.4:
            return "Good serviceability"
        elif dsr < 0.5:
            return "Moderate - near threshold"
        else:
            return "Concern - may exceed lender limits"
            
    def extract_enhanced_info(self, message):
        """Extract comprehensive information from user message"""
        try:
            analysis_prompt = f"""
            Analyze this message and extract the following information as JSON:
            
            1. Mortgage purpose (first_home_purchase, investment, refinance, other)
            2. Personal Details 
                -name
                -no_of_dependants
                -employment_type (full-time, part-time, casual, self-employed)
            3. Financial Information:
                -income (annual before tax)
                -expenses (monthly)
                -other_debts (monthly payments for credit cards, personal loans, etc.)
            4. Property Details:
                -property_value
                -property_location
                -deposit_amount
            5. Preferences:
                -rate_type (fixed, variable, split)
                -loan_term (in years)
                -offset_account (yes/no)
                -redraw_facility (yes/no)
            6. Life circumstances:
                -upcoming_life_events (list)
                -timeline (short, medium, long)
            
            Return a JSON object with only the keys where values are clearly mentioned in the message.
            For numeric values, include just the number (no currency symbols or commas).
            """
            
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                system=analysis_prompt,
                messages=[{"role": "user", "content": message}],
                temperature=0.1,
                max_tokens=1000
            )
            
            extracted_info = json.loads(response.content[0].text)
            
            # Update state with new information
            if 'mortgage_purpose' in extracted_info:
                self.state['collected_info']['mortgage_purpose'] = extracted_info['mortgage_purpose']
                self.state['steps_completed']['purpose_identified'] = True
            
            # Handle personal details
            if 'personal_details' in extracted_info:
                for key, value in extracted_info['personal_details'].items():
                    if value is not None:
                        self.state['collected_info'][key] = value
                
                # Check if we have collected all personal details
                if all(field in self.state['collected_info'] for field in ['name', 'no_of_dependants', 'employment_type']):
                    self.state['steps_completed']['personal_details_collected'] = True
            
            # Handle financial information
            if 'financial_information' in extracted_info:
                for key, value in extracted_info['financial_information'].items():
                    if value is not None:
                        self.state['collected_info'][key] = value
                
                # Check if we have all financial information
                if all(field in self.state['collected_info'] for field in ['income', 'expenses']):
                    self.state['steps_completed']['financial_info_collected'] = True
            
            # Handle property details
            if 'property_details' in extracted_info:
                for key, value in extracted_info['property_details'].items():
                    if value is not None:
                        self.state['collected_info'][key] = value
                
                # Check if we have all property details
                if all(field in self.state['collected_info'] for field in ['property_value', 'deposit_amount']):
                    self.state['steps_completed']['property_details_collected'] = True
                    
                    # Calculate loan amount if not provided directly
                    if 'loan_amount' not in self.state['collected_info'] and 'property_value' in self.state['collected_info'] and 'deposit_amount' in self.state['collected_info']:
                        property_value = float(self.state['collected_info']['property_value'])
                        deposit = float(self.state['collected_info']['deposit_amount'])
                        self.state['collected_info']['loan_amount'] = property_value - deposit
            
            # Handle preferences
            if 'preferences' in extracted_info:
                for key, value in extracted_info['preferences'].items():
                    if value is not None:
                        self.state['collected_info'][key] = value
                
                # Check if we have preferences
                if 'rate_type' in self.state['collected_info'] and 'loan_term' in self.state['collected_info']:
                    self.state['steps_completed']['preferences_collected'] = True
            
            # Handle life circumstances
            if 'life_circumstances' in extracted_info:
                for key, value in extracted_info['life_circumstances'].items():
                    if value is not None:
                        self.state['collected_info'][key] = value
            
            # Calculate serviceability if we have all needed fields
            if all(field in self.state['collected_info'] for field in ['income', 'expenses', 'property_value', 'loan_amount']):
                self.calculate_serviceability(
                    self.state['collected_info']['income'],
                    self.state['collected_info']['expenses'],
                    self.state['collected_info']['loan_amount'],
                    self.state['collected_info']['property_value'],
                    self.state['collected_info'].get('other_debts', 0)
                )
                self.state['steps_completed']['analysis_complete'] = True
            
            return extracted_info
        except Exception as e:
            print(f"Error extracting info: {e}")
            return {}

    def extract_purpose(self, message):
        """Extract mortgage purpose from user message"""
        try:
            purpose_prompt = f"""
            Analyze this message and determine if it indicates:
            1. First home purchase
            2. Investment property
            3. Refinancing
            4. Unknown/Other
            
            Return only one of these exact terms.
            """
            
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                system=purpose_prompt,
                messages=[{"role": "user", "content": message}],
                temperature=0.1,
                max_tokens=100
            )
            
            purpose = response.content[0].text.strip()
            self.state['collected_info']['mortgage_purpose'] = purpose
            
            if purpose == "First home purchase":
                self.state['steps_completed']['purpose_identified'] = True
            
            return purpose
        except Exception as e:
            print(f"Error extracting purpose: {e}")
            return "Unknown"

    def analyze_rate_impact(self, loan_amount, current_rate, term_years=30):
        """Analyze impact of rate changes on monthly payments"""
        if not loan_amount or not current_rate:
            return {}
            
        rate_changes = [-0.5, 0, 0.5, 1.0, 2.0]
        analysis = {}
        
        for change in rate_changes:
            new_rate = float(current_rate) + change
            monthly_payment = self.estimate_monthly_payment(float(loan_amount), new_rate/100, term_years)
            analysis[f"{new_rate:.1f}%"] = monthly_payment
        
        return analysis

    def estimate_monthly_payment(self, loan_amount, annual_rate, years):
        """Calculate monthly mortgage payment"""
        if not loan_amount or not annual_rate:
            return 0
        
        monthly_rate = float(annual_rate) / 12
        num_payments = int(years) * 12
        monthly_payment = float(loan_amount) * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        return monthly_payment

    def calculate_serviceability(self, income, expenses, loan_amount, property_value, other_debts=0):
        """Calculate key serviceability metrics"""
        try:
            income = float(income)
            expenses = float(expenses)
            loan_amount = float(loan_amount)
            property_value = float(property_value)
            other_debts = float(other_debts)
            
            monthly_income = income / 12
            monthly_expenses = expenses
            
            # Assume 3.5% interest rate for calculation if we don't have a selected product yet
            interest_rate = 0.035
            loan_term = self.state['collected_info'].get('loan_term', 30)
            
            monthly_loan_payment = self.estimate_monthly_payment(loan_amount, interest_rate, loan_term)
            
            dsr = (monthly_loan_payment + other_debts) / monthly_income
            lvr = loan_amount / property_value
            nsr = (monthly_income - monthly_expenses) / monthly_loan_payment
            
            metrics = {
                'dsr': dsr,
                'lvr': lvr,
                'nsr': nsr,
                'monthly_payment': monthly_loan_payment
            }
            
            self.state['serviceability_metrics'] = metrics
            return metrics
        except Exception as e:
            print(f"Error calculating serviceability: {e}")
            return {}
    
    def generate_loan_scenarios(self):
        """Generate personalized loan scenarios based on customer profile"""
        try:
            scenarios = []
            
            # Get key details from collected info
            income = float(self.state['collected_info'].get('income', 0))
            property_value = float(self.state['collected_info'].get('property_value', 0))
            loan_amount = float(self.state['collected_info'].get('loan_amount', 0))
            rate_preference = self.state['collected_info'].get('rate_type', 'variable')
            loan_term = int(self.state['collected_info'].get('loan_term', 30))
            
            # Get life events/goals for personalization
            life_events = self.state['collected_info'].get('upcoming_life_events', [])
            
            # Determine customer needs based on collected info
            needs_flexibility = any(event in str(life_events).lower() for event in ['child', 'baby', 'family', 'marriage', 'wedding'])
            needs_stability = any(event in str(life_events).lower() for event in ['retire', 'retirement', 'pension', 'fixed income'])
            
            # Filter products based on min income requirement
            eligible_products = []
            for product in self.state['products']:
                if isinstance(product, dict) and 'min_income' in product:
                    try:
                        min_income = float(product['min_income'])
                        if income >= min_income:
                            eligible_products.append(product)
                    except (ValueError, TypeError):
                        eligible_products.append(product)  # Include if we can't validate
                else:
                    eligible_products.append(product)  # Include if no income requirement
            
            # If we have rate preference, prioritize matching products
            if rate_preference:
                rate_matches = [p for p in eligible_products if isinstance(p, dict) and p.get('rate_type', '').lower() == rate_preference.lower()]
                if rate_matches:
                    eligible_products = rate_matches + [p for p in eligible_products if p not in rate_matches]
            
            # Create scenarios for top 3 products
            for i, product in enumerate(eligible_products[:3]):
                if not isinstance(product, dict):
                    continue
                    
                # Extract interest rate
                interest_rate = None
                if 'interest_rate' in product:
                    try:
                        rate_str = product['interest_rate'].strip('%')
                        interest_rate = float(rate_str)
                    except (ValueError, AttributeError):
                        interest_rate = 3.5  # Default fallback
                else:
                    interest_rate = 3.5  # Default fallback
                
                # Calculate monthly payment
                monthly_payment = self.estimate_monthly_payment(loan_amount, interest_rate/100, loan_term)
                
                scenario = {
                    'product_name': product.get('product_name', f"Mortgage Product {i+1}"),
                    'loan_amount': loan_amount,
                    'interest_rate': interest_rate,
                    'monthly_payment': monthly_payment,
                    'features': [],
                    'suitability_reasons': [],
                    'considerations': []
                }
                
                # Add product features
                if product.get('offset_account', 'No').lower() == 'yes':
                    scenario['features'].append("Offset Account")
                if product.get('redraw_facility', 'No').lower() == 'yes':
                    scenario['features'].append("Redraw Facility")
                if product.get('extra_repayments', 'No').lower() == 'yes':
                    scenario['features'].append("Extra Repayments Allowed")
                
                # Add personalized suitability reasons
                if needs_flexibility and product.get('rate_type', '').lower() == 'variable':
                    scenario['suitability_reasons'].append("Provides flexibility for changing life circumstances")
                if needs_stability and product.get('rate_type', '').lower() == 'fixed':
                    scenario['suitability_reasons'].append("Provides payment stability during retirement planning")
                
                scenarios.append(scenario)
            
            # Mark recommendations as provided
            if scenarios:
                self.state['steps_completed']['recommendations_provided'] = True
            
            return scenarios
        except Exception as e:
            print(f"Error generating scenarios: {e}")
            return []

    def format_scenario_message(self, scenarios):
        """Format loan scenarios into clear, structured output"""
        if not scenarios:
            return "I need more information to provide personalized loan recommendations."
        
        message = "## Based on your circumstances, here are recommended loan options:\n\n"
        
        for i, scenario in enumerate(scenarios, 1):
            message += f"### Option {i}: {scenario['product_name']}\n"
            message += "| Category | Details |\n|----------|----------|\n"
            message += f"| Interest Rate | **{scenario['interest_rate']}%** |\n"
            message += f"| Monthly Payment | **${scenario['monthly_payment']:,.2f}** |\n"
            message += f"| Loan Amount | **${scenario['loan_amount']:,.2f}** |\n"
            
            if scenario['features']:
                message += "\n**Key Features:**\n"
                for feature in scenario['features']:
                    message += f"• {feature}\n"
                    
            if scenario['suitability_reasons']:
                message += "\n**Why This Suits You:**\n"
                for reason in scenario['suitability_reasons']:
                    message += f"• {reason}\n"
            
            message += "\n---\n\n"
        
        return message
        
    def update_conversation_stage(self):
        """Update the conversation stage based on collected information and steps completed"""
        # Initial logic to determine the right stage
        if not self.state['steps_completed']['purpose_identified']:
            # Still need to identify mortgage purpose
            self.state['conversation_stage'] = 'purpose'
            return
            
        if not self.state['steps_completed']['personal_details_collected']:
            # Still need to collect personal details
            self.state['conversation_stage'] = 'personal_details'
            return
            
        if not self.state['steps_completed']['financial_info_collected']:
            # Still need to collect financial information
            self.state['conversation_stage'] = 'financial_info'
            return
            
        if not self.state['steps_completed']['borrowing_power_calculated']:
            # Need to calculate borrowing power
            if all(field in self.state['collected_info'] for field in ['income', 'expenses']):
                self.state['steps_completed']['financial_info_collected'] = True
                self.state['conversation_stage'] = 'borrowing_power'
                self.state['steps_completed']['borrowing_power_calculated'] = True
            else:
                self.state['conversation_stage'] = 'financial_info'
            return
            
        if not self.state['steps_completed']['property_details_collected']:
            # Still need to collect property details
            self.state['conversation_stage'] = 'basic_financials'
            return
            
        if not self.state['steps_completed']['preferences_collected']:
            # Need to collect loan preferences
            self.state['conversation_stage'] = 'preferences'
            return
            
        if not self.state['steps_completed']['analysis_complete']:
            # Need to perform serviceability analysis
            if all(field in self.state['collected_info'] for field in ['income', 'expenses', 'property_value', 'loan_amount']):
                self.calculate_serviceability(
                    self.state['collected_info']['income'],
                    self.state['collected_info']['expenses'],
                    self.state['collected_info']['loan_amount'],
                    self.state['collected_info']['property_value'],
                    self.state['collected_info'].get('other_debts', 0)
                )
                self.state['steps_completed']['analysis_complete'] = True
                self.state['conversation_stage'] = 'serviceability'
            else:
                self.state['conversation_stage'] = 'basic_financials'
            return
            
        if self.state['conversation_stage'] == 'serviceability':
            # Move to what-if scenarios
            self.state['conversation_stage'] = 'what_if'
            return
            
        if self.state['conversation_stage'] == 'what_if':
            # Move to recommendations
            self.state['conversation_stage'] = 'recommendations'
            return
            
        if not self.state['steps_completed']['recommendations_provided']:
            # Generate and show recommendations
            self.state['conversation_stage'] = 'recommendations'
            return
            
        # If we've covered everything, stay in follow-up mode
        self.state['conversation_stage'] = 'followup'

    def get_next_response(self, user_message):
        """Process user message and generate next response"""
        # Update conversation history
        self.state['conversation_history'].append({"role": "user", "content": user_message})
        
        # Extract information from the message
        self.extract_enhanced_info(user_message)
        
        # Update the conversation stage based on collected information
        self.update_conversation_stage()
        
        try:
            # Generate response using the Anthropic API (Claude 3.7 Sonnet)
            # Convert conversation history to Claude format
            system_prompt = self.get_system_prompt()
            conversation = []
            
            for msg in self.state['conversation_history']:
                role = "user" if msg["role"] == "user" else "assistant"
                conversation.append({"role": role, "content": msg["content"]})
            
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                system=system_prompt,
                messages=conversation,
                temperature=0.7,
                max_tokens=2000
            )
            
            assistant_message = response.content[0].text
            
            # Add additional structured information based on the stage
            if self.state['conversation_stage'] == 'serviceability' and self.state['steps_completed']['analysis_complete']:
                # No need to add more content here as it's already in the system prompt
                pass
                
            elif self.state['conversation_stage'] == 'what_if':
                # No need to add more content here as it's already in the system prompt
                pass
                
            elif self.state['conversation_stage'] == 'recommendations':
                # Generate and add loan scenarios
                scenarios = self.generate_loan_scenarios()
                if scenarios:
                    scenario_message = self.format_scenario_message(scenarios)
                    if "recommended loan options" not in assistant_message.lower():
                        assistant_message += f"\n\n{scenario_message}"
            
            # Save message to conversation history
            self.state['conversation_history'].append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
                
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            self.state['conversation_history'].append({"role": "assistant", "content": error_msg})
            return error_msg