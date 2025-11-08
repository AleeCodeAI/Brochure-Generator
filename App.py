# IMPORTING NECESSARY LIBRARIES
import os 
import json
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
from my_web_scraper import fetch_website_links, fetch_website_contents

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Company Brochure Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# LOADING THE API
load_dotenv(override=True)
gemini_api_key = os.getenv("GEMINI_API_KEY")

# INITIALIZING THE OPENAI CLIENT
model = "gemini-2.0-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL, api_key=gemini_api_key)

# Designing a System Prompt for the LLM to take out relevant links
link_system_prompt = """
You are provided with lists of links from a webpage.
Your task is to identify and extract links that are relevant to creating a sales brochure for the products or 
services offered on the webpage.
Such as links that lead to product pages, service descriptions, pricing information, testimonials, case studies, 
and any other content that highlights the value proposition of the products or services.
Include the Social Media links and any external company mentioned
You should respond in JSON as in the example:
{
"links": [
{type": "product_page", "url": "https://example.com/product1"},
{type": "testimonial", "url": "https://example.com/testimonials"},
{"type": "pricing", "url": "https://example.com/pricing"},
{"type": "case_study", "url": "https://example.com/case-study1"}]
}
"""

# DESIGINING A USER PROMPT 
def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt

# FUNCTION THAT USES THE LLM TO SELECT RELEVANT LINKS
def select_relevant_links(url):
    try:
        response = gemini.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": link_system_prompt},
                {"role": "user", "content": get_links_user_prompt(url)}
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        result = response.choices[0].message.content
        links = json.loads(result)
        return links
    except Exception as e:
        st.error(f"Error selecting relevant links: {str(e)}")
        return {"links": []}

# STICHING THE CONTENTS OF WEBSITE AND RELEVANT LINKS
def fetch_page_and_all_relevant_links(url):
    try:
        contents = fetch_website_contents(url)
        relevant_links = select_relevant_links(url)
        result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
        for link in relevant_links['links']:
            result += f"\n\n### Link: {link['type']}\n"
            result += fetch_website_contents(link["url"])
        return result
    except Exception as e:
        st.error(f"Error fetching website contents: {str(e)}")
        return ""

# DESGINING THE BROCHURE SYSTEM PROMPT:
brochure_system_prompt = """
You are an expert marketing assistant who analyzes multiple pages from a company's website
to create a professional and engaging brochure for prospective customers, investors, and potential recruits.

Your goal is to make the brochure **detailed yet concise**, focusing only on the most essential and appealing 
information.
Present the content in an **attractive, easy-to-read markdown format** (no code blocks).

The brochure should include:
- A brief overview/introduction of the company
- Key products or services offered
- Company mission, vision, and values
- Details about company culture and work environment
- Information about customers, clients, or industries served
- Highlights of career opportunities and recruitment information (if available)
- Notable achievements, partnerships, or milestones
- Relevant links (official website, careers page, contact page, etc.)

Tone: **Professional, inspiring, and informative** — written as if designed for a real printed/digital brochure.
"""

# DESGINING A USER PROMPT:
def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    website_content = fetch_page_and_all_relevant_links(url)
    user_prompt += website_content
    user_prompt = user_prompt[:5_000]  # Truncate if more than 5,000 characters
    return user_prompt

def generate_brochure(company_name, url):
    try:
        response = gemini.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": brochure_system_prompt},
                {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
            ]
        )    
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating brochure: {str(e)}")
        return None

# STREAMLIT UI

# STREAMLIT UI
def main():
    # Header
    st.title("Company Brochure Generator")
    st.markdown("Generate a professional brochure from any company website quickly and efficiently.")

    st.markdown("---")

    # Company Information Input
    st.header("Company Information")
    company_name = st.text_input(
        "Company Name",
        placeholder="e.g., Google, Apple, Microsoft",
        help="Enter the official name of the company"
    )

    website_url = st.text_input(
        "Website URL",
        placeholder="https://www.company.com",
        help="Enter the full website URL including https://"
    )

    generate_btn = st.button(
        "Generate Brochure",
        type="primary",
        use_container_width=True
    )

    st.markdown("---")

    # How it works
    st.header("How it Works")
    st.markdown("""
    1. Enter the company name and website URL
    2. Click **Generate Brochure**
    3. The system will analyze the website and relevant links
    4. Receive a polished, professional brochure including:
       - Company overview
       - Products & services
       - Mission & values
       - Company culture
       - Career opportunities
       - Key achievements
    """)

    st.markdown("---")

    # Generate brochure
    if generate_btn:
        if not company_name or not website_url:
            st.error("Please fill in both Company Name and Website URL")
            return
        
        if not website_url.startswith(('http://', 'https://')):
            st.error("Please enter a valid URL starting with http:// or https://")
            return

        with st.spinner("Analyzing website content and generating brochure..."):
            brochure_content = generate_brochure(company_name, website_url)

        if brochure_content:
            st.success("Brochure generated successfully!")
            
            # Display brochure
            st.header(f"{company_name} - Company Brochure")
            
            with st.expander("View Generated Brochure", expanded=True):
                st.markdown(brochure_content)
            
            st.download_button(
                label="Download Brochure as Markdown",
                data=brochure_content,
                file_name=f"{company_name.replace(' ', '_')}_brochure.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            if st.button("Copy to Clipboard", use_container_width=True):
                st.code(brochure_content, language="markdown")
                st.success("Brochure content copied to clipboard!")

    st.markdown("---")
    st.caption("Built with Streamlit & Gemini AI • Company Brochure Generator")
if __name__ == "__main__":
    main()