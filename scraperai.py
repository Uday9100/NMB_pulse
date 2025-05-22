import os
import json
import boto3
from playwright.sync_api import sync_playwright

def fetch_page_text(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless for Lambda deployment
        page = browser.new_page()
        page.goto(url)
        text = page.inner_text('body')  # get all text from body
        browser.close()
    return text

def generate_bmc_details(text, bedrock_client):
    prompt = (
        "Extract the following Business Model Canvas sections from the text:\n"
        "- Key Partners\n- Key Activities\n- Key Resources\n- Value Propositions\n"
        "- Customer Relationships\n- Channels\n- Customer Segments\n- Cost Structure\n- Revenue Streams\n\n"
        "Provide the output as a JSON object with section names as keys.\n\n"
        "Text:\n"
        + text
    )

    request_body = {
        "prompt": prompt
    }

    response = bedrock_client.invoke_model(
        modelId='meta.llama3-3-70b-instruct-v1:0',  # use your model ID here
        contentType='application/json',
        accept='application/json',
        body=json.dumps(request_body)
    )

    response_body = response['body'].read()
    print("Raw response from Bedrock:\n", response_body.decode('utf-8'))  # DEBUG: see entire output

    result = json.loads(response_body)

    # Adjust this according to your model's actual response structure
    output_text = result.get('results', [{}])[0].get('output', 'No output')
    return output_text

def lambda_handler(event, context):
    target_url = event.get('url', None)  # URL passed in the event payload
    if not target_url:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'url' in request"})
        }

    print(f"Fetching text from: {target_url}")
    page_text = fetch_page_text(target_url)

    # Init Bedrock client
    bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-2'))

    print("Extracting Business Model Canvas sections using Bedrock AI...")
    bmc_details = generate_bmc_details(page_text, bedrock)

    return {
        "statusCode": 200,
        "body": json.dumps({"bmc_details": bmc_details})
    }

if __name__ == "__main__":
    # Uncomment the following line for local testing
    # lambda_handler({"url": "https://www.airbnb.com/about/about-us"}, None)
    pass
