# Magazine Subscriber Customer Service Routing Simulator

A Streamlit prototype for routing magazine subscriber questions from email, phone, live chat, and web forms.

## Features

- Classifies common subscriber questions.
- Recommends a customer service team.
- Assigns a provisional priority.
- Suggests a workflow for handling the request.
- Flags cases that may require human review.
- Provides contact-channel-specific guidance.
- Allows routing results to be downloaded as CSV.

## Important Limitations

This is a rules-based prototype, not a trained AI model.

It does not connect to actual subscriber accounts, email inboxes, phone systems, live chat, billing systems, or web forms.

Use fictional requests only. Never enter real subscriber personal information, account numbers, passwords, or payment details.

## Run the Application

Install the dependencies:

pip install -r requirements.txt

Start the app:

streamlit run app.py

## Deployment

The application can be deployed using Streamlit Community Cloud by connecting this GitHub repository and selecting app.py as the application entry point.
