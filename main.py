import streamlit as st
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
# from webdriver_manager.chrome import ChromeDriverManager



### functions ###

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

            # Setup Firefox options
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")  # Optional: Run headlessly

            # Explicitly set the path to the Firefox binary
            firefox_binary_path = "/usr/bin/firefox"  # Adjust this path according to your system
            firefox_options.binary_location = firefox_binary_path

            # Use GeckoDriverManager to get the path to the geckodriver executable
            gecko_driver_path = GeckoDriverManager().install()

            # Create a Service object for Firefox
            firefox_service = FirefoxService(executable_path=gecko_driver_path)

            # Initialize the Firefox driver with the Service object and options
            driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

            # driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=firefox_options)
            # chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument("--start-fullscreen")
            # driver = webdriver.Chrome(ChromeDriverManager(name="chromedriver").install(), options=chrome_options)
            driver.get("https://github.com")
            print(driver.title)

            # Get search bar
            try:
                find_search_bar = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/button")
            except NoSuchElementException:
                st.session_state['chat_history'].append({"role": "assistant", "message": "Ezzy Bot: Error - Search bar not found on GitHub page."})
                driver.quit()
                st.stop()

            # Open search bar
            find_search_bar.send_keys(user_input)

            # Send input to search bar
            try:
                find_search_input_text = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/div/modal-dialog/div/div/div/form/query-builder/div[1]/div[1]/div/div[2]/input")
            except NoSuchElementException:
                st.session_state['chat_history'].append({"role": "assistant", "message": "Ezzy Bot: Error - Search input field not found."})
                driver.quit()
                st.stop()

            find_search_input_text.send_keys(user_input)
            print("Input text successful")

            # Initialize search
            find_search_input_text.send_keys(Keys.RETURN)
            time.sleep(2)

            # Get number of results
            results = get_no_of_results(driver)
            time.sleep(1)
            if int(results)>9:

                st.session_state['chat_history'].append({"role": "assistant", "message": "Ezzy Bot: fetching first 10 repos..."})

                # Display chat history
                with messages:
                    for entry in st.session_state['chat_history']:
                        role = entry["role"]
                        message = entry["message"]
                        with st.chat_message(role):
                            st.write(message)

            # Load first 10 repos
            final_readme = load_first_10_repo(driver)

            driver.quit()

            st.session_state['chat_history'].append({"role": "assistant", "message": f"Ezzy Bot: {str(results)} results found \n {final_readme}"})

    except WebDriverException as e:
        st.session_state['chat_history'].append({"role": "assistant", "message": f"Ezzy Bot: WebDriver error occurred - {str(e)}"})
    except Exception as e:
        st.session_state['chat_history'].append({"role": "assistant", "message": f"Ezzy Bot: An unexpected error occurred - {str(e)}"})

# Display chat history
with messages:
    for entry in st.session_state['chat_history']:
        role = entry["role"]
        message = entry["message"]
        with st.chat_message(role):
            st.write(message)



