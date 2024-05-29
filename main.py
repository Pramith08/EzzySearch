import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_no_of_results():
    while True:
        try:
            no_of_result = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[1]/div/span/span/div")
            results = no_of_result.text
            result_numbers_only = ''.join([char for char in results if char.isdigit()])
            return result_numbers_only
        except StaleElementReferenceException:
            time.sleep(2)

def find_element_retry(by, value):
    retries = 3
    for i in range(retries):
        try:
            element = driver.find_element(by, value)
            return element
        except StaleElementReferenceException:
            time.sleep(2)
    raise NoSuchElementException(f"Element not found after {retries} retries: {by}={value}")

def load_first_10_repo():
    for a in range(1, 11):
        try:
            # Find repo
            find_repository = find_element_retry(By.XPATH, f"/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[4]/div/div/div[{a}]/div/div[1]/h3/div/div[2]/a")

            # Write repo name
            st.subheader(find_repository.text)

            # Get repo link
            repository_text = find_repository.get_attribute('href')

            # Write repo link
            st.write(repository_text)
            print("-----   " + str(a) + " :" + " repo")
            find_repository.click()
            time.sleep(2)

            # Check if readme found (various cases)
            readme_variations = ["readme", "Readme", "README", "ReadMe", "ReadME"]
            found_readme = False
            for variation in readme_variations:
                try:
                    find_readme = find_element_retry(By.PARTIAL_LINK_TEXT, variation)
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
                find_readme_text = find_element_retry(By.TAG_NAME, "article")
                time.sleep(2)

                # Convert article content into text
                readme_text = find_readme_text.text

                readme_text_length = len(readme_text)

                if readme_text_length > 500:
                    readme_text = (readme_text[:500] + "...")
                    st.write(readme_text)
                else:
                    st.write(readme_text)

                # Wait and go back
                driver.back()
                driver.back()

            else:
                st.write("No readme file found")

                # Wait and go back
                driver.back()

            time.sleep(2)

        except NoSuchElementException:
            pass

#--------------------------------------
#main
st.sidebar.button("Home")
st.write(""" # EZZY SEARCH""")
input_text = st.text_input(" ", "")
if st.button("Submit"):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-fullscreen")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    # path = "https://github.com/Pramith08/EzzySearch/blob/main/chromedriver.exe"
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--start-fullscreen")
    driver = webdriver.Chrome(path, options=chrome_options)
    driver.get("https://github.com")
    print(driver.title)

    # Get search bar
    search_bar = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/button")

    # Open search bar
    search_bar.send_keys(input_text)

    # Send input to search bar
    search_input_text = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/div/modal-dialog/div/div/div/form/query-builder/div[1]/div[1]/div/div[2]/input")
    search_input_text.send_keys(input_text)
    print("input text successful")

    # Initialize search
    search_input_text.send_keys(Keys.RETURN)
    time.sleep(2)

    # Get number of results
    results = get_no_of_results()

    # Load first 10 repos
    load_first_10_repo()

    # Load next 10 repos
    if int(results) > 10:
        if st.button("Load More"):
            st.write("Loading More....  \"NOT IMPLEMENTED\"")

    driver.quit()
