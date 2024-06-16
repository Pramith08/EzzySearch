import streamlit as st
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
import os

# Function to install Geckodriver and configure Selenium to use Firefox
@st.experimental_singleton
def setup_selenium():
    # Specify the path to the Geckodriver executable
    gecko_driver_path = '/path/to/geckodriver'  # Update this path to where you've saved Geckodriver
    
    # Configure Firefox options
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    
    # Create a Service object for Firefox
    firefox_service = FirefoxService(executable_path=gecko_driver_path)
    
    # Return the configured WebDriver
    return webdriver.Firefox(service=firefox_service, options=firefox_options)

# Call the setup function to initialize Selenium
browser = setup_selenium()

def get_no_of_results(driver):
    while True:
        try:
            no_of_result = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[1]/div/span/span/div")
            results = no_of_result.text
            result_numbers_only = ''.join([char for char in results if char.isdigit()])
            return result_numbers_only
        except StaleElementReferenceException:
            time.sleep(2)

def find_element_retry(driver, by, value):
    retries = 3
    for i in range(retries):
        try:
            element = driver.find_element(by, value)
            return element
        except StaleElementReferenceException:
            time.sleep(2)
    raise NoSuchElementException(f"Element not found after {retries} retries: {by}={value}")

def load_first_10_repo(driver):
    final_readme = ""

    for a in range(1, 11):
        try:
            # Find repo
            find_repository = find_element_retry(driver, By.XPATH, f"/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[4]/div/div/div[{a}]/div/div[1]/h3/div/div[2]/a")

            # Append repo name
            final_readme += "\n" + find_repository.text + "\n\n"

            # Get repo link
            repository_text = find_repository.get_attribute('href')

            # Append repo link
            final_readme += "\n" + repository_text + "\n\n"

            # Click repository link
            find_repository.click()
            time.sleep(2)

            # Check if readme found (various cases)
            readme_variations = ["readme", "Readme", "README", "ReadMe", "ReadME", "readme.md", "Readme.md", "README.md", "ReadMe.md", "ReadME.md"]
            found_readme = False
            
            for variation in readme_variations:
                try:
                    # Search within the specified container
                    find_readme_container = find_element_retry(driver, By.XPATH, "//*[@id='repo-content-pjax-container']/div/div/div[2]/div[1]/react-partial/div/div/div[3]/div[2]")
                    find_readme = find_readme_container.find_element(By.PARTIAL_LINK_TEXT, variation)
                    found_readme = True
                    break
                except NoSuchElementException:
                    continue

            if found_readme:
                time.sleep(2)
                find_readme.click()
                print("-----   " + str(a) + " :" + " readme")
                time.sleep(2)

                # Find article in readme
                find_readme_text = find_element_retry(driver, By.TAG_NAME, "article")
                time.sleep(2)

                # Convert article content into text
                readme_text = find_readme_text.text

                readme_text_length = len(readme_text)

                if readme_text_length > 500:
                    readme_text = (readme_text[:500] + "...")
                    final_readme += "\n" + readme_text + "\n\n"
                    final_readme += "\n" + "-------------------------------------------------" + "\n\n"
                else:
                    final_readme += "\n" + readme_text + "\n\n"
                    final_readme += "\n" + "-------------------------------------------------" + "\n\n"

                # Wait and go back
                driver.back()
                
            else:
                final_readme += "\n" + "No readme file found" + "\n\n"
                final_readme += "\n" + "-------------------------------------------------" + "\n\n"
                driver.back()

            time.sleep(2)

        except NoSuchElementException:
            continue

    return final_readme

#### main ###

browser = setup_selenium()

st.set_page_config(
    page_title="Ezzy Search",
    page_icon=":🔍:",
    layout="wide",
)

st.sidebar.image("EZ Logo.jpg")

# Custom CSS to style the reset button
st.markdown("""
    <style>
   .stButton button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

if st.sidebar.button("clear"):
    st.session_state['chat_history'] = []  # Reset chat history

st.write(""" # EZZY SEARCH""")

# Container to display chat  
messages = st.container(height=600,)

# Chat input
user_input = st.chat_input("Search repositories on GitHub", key="user_input")

# Maintain chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Update chat history
if user_input:
    st.session_state['chat_history'].append({"role": "user", "message": user_input})
    st.session_state['chat_history'].append({"role": "assistant", "message": "Ezzy Bot: Processing your request, please wait..."})

    # Display chat history
    with messages:
        for entry in st.session_state['chat_history']:
            role = entry["role"]
            message = entry["message"]
            with st.chat_message(role):
                st.write(message)

    # Process the request in a spinner
    try:
        with st.spinner('Processing your request...'):
            # Your processing logic here
            pass  # Placeholder for your processing logic

            # Example: Displaying results
            st.session_state['chat_history'].append({"role": "assistant", "message": "Results processed successfully!"})

    except Exception as e:
        st.session_state['chat_history'].append({"role": "assistant", "message": f"Ezzy Bot: An unexpected error occurred - {str(e)}"})

# Display chat history
with messages:
    for entry in st.session_state['chat_history']:
        role = entry["role"]
        message = entry["message"]
        with st.chat_message(role):
            st.write(message)
