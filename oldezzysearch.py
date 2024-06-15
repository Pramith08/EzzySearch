# import streamlit as st
# import time
# from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager

# ### functions ###
# def get_no_of_results(driver):
#     while True:
#         try:
#             no_of_result = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[1]/div/span/span/div")
#             results = no_of_result.text
#             result_numbers_only = ''.join([char for char in results if char.isdigit()])
#             return result_numbers_only
#         except Exception as e:
#             print("get no of results excepetion: "+str(e))
#             time.sleep(2)
#             pass


# def find_element_retry(driver, by, value):
#     retries = 3
#     bool = False
#     for i in range(retries):
#         try:
#             element = driver.find_element(by, value)
#             bool = True
#             return element,bool
        
#         except Exception as e:
#             print("find elements retries exception: "+str(e))
#             time.sleep(2)
#     element="readme not found"
#     return element,bool
    


# def load_first_10_repo(driver):
#     final_readme = ""

#     for a in range(1, 11):
#         try:
#             # Find repo
#             find_repository = find_element_retry(driver, By.XPATH, f"/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[4]/div/div/div[{a}]/div/div[1]/h3/div/div[2]/a/span")

            

#             # append repo name
#             final_readme += "\n" + find_repository.text + "\n\n"

#             # Get repo link
#             repository_text = find_repository.get_attribute('href')

#             #append repo link
#             final_readme += "\n" + repository_text + "\n\n"

#             # Write repo link
#             # st.write(repository_text)
#             print("-----   " + str(a) + " :" + " repo")
#             find_repository.click()
#             time.sleep(2)

#             # Check if readme found (various cases)
#             readme_variations = ["readme.md", "Readme.md", "README.md", "ReadMe.md", "ReadME.md"]
#             found_readme = False
#             for variation in readme_variations:
#                 try:
#                     find_readme, found_readme = find_element_retry(driver, By.PARTIAL_LINK_TEXT, variation)
#                     break
#                 except Exception as e:
#                     print("find readme error: "+str(e))
#                     continue
#             try:
#                 if found_readme:
#                     time.sleep(2)
#                     find_readme.click()
#                     print("-----   " + str(a) + " :" + " readme")
#                     time.sleep(2)

#                     # Find article in readme
#                     find_readme_text = find_element_retry(driver, By.TAG_NAME, "article")
#                     time.sleep(2)

#                     # Convert article content into text
#                     readme_text = find_readme_text.text

#                     readme_text_length = len(readme_text)

#                     if readme_text_length > 500:
#                         readme_text = (readme_text[:500] + "...")
#                         final_readme += "\n" + readme_text + "\n\n"
#                         final_readme += "\n" + "-------------------------------------------------" + "\n\n"

#                         # st.divider()
#                     else:                        
#                         final_readme += "\n" + readme_text + "\n\n"
#                         final_readme += "\n" + "-------------------------------------------------" + "\n\n"
#                         # st.divider()

#                     # Wait and go back
#                     driver.back()
#                     driver.back()
#                 else:
#                     final_readme += "\n" + "No readme file found" + "\n\n"
#                     final_readme += "\n" + "-------------------------------------------------" + "\n\n"
#                     # st.divider()

#                 # Wait and go back
#                     driver.back()
                    
#             except Exception as e :
#                 print("get readme error: "+str(e))
#                 continue

#             time.sleep(2)

#         except Exception as e:
#             print("search repos error: "+str(e))
#             pass

#     return final_readme



# #### main ###
# st.set_page_config(
#     page_title="Ezzy Search",
#     page_icon=":🔍:",

#     layout="wide",

# )

# # st.sidebar.image("EZ Logo.jpg")
# st.sidebar.write(""" # EZZY SEARCH""")

# # Custom CSS to style the reset button
# st.markdown("""
#     <style>
#     .stButton button {
#         width: 100%;
#     }
#     </style>
#     """, unsafe_allow_html=True)
# # Reset chat history
# if st.sidebar.button("clear",):
#         st.session_state['chat_history'] = []  

# st.write(""" # EZZY SEARCH""")

# #container to display chat  
# messages = st.container(height=600,)

# # Chat input
# user_input = st.chat_input("Search repositories on GitHub", key="user_input")

# # Maintain chat history
# if 'chat_history' not in st.session_state:
#     st.session_state['chat_history'] = []

# # Update chat history
# if user_input:
#     st.session_state['chat_history'].append({"role": "user", "message": user_input})

#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument("--start-fullscreen")
#     # Specify the Chrome driver version explicitly
#     # path = "C:\Program Files (x86)\chromedriver"
#     driver = webdriver.Chrome(ChromeDriverManager(name="chromedriver").install(), options=chrome_options)
#     driver.get("https://github.com")
#     print(driver.title)

#     # Get search bar
#     find_search_bar = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/button")

#     # Open search bar
#     find_search_bar.send_keys(user_input)

#     # Send input to search bar
#     find_search_input_text = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/header/div/div[2]/div/div/qbsearch-input/div[1]/div/modal-dialog/div/div/div/form/query-builder/div[1]/div[1]/div/div[2]/input")
#     find_search_input_text.send_keys(user_input)
#     print("input text successful")

#     # Initialize search
#     find_search_input_text.send_keys(Keys.RETURN)
#     time.sleep(2)

#     # Get number of results
#     results = get_no_of_results(driver)

#     # Load first 10 repos
#     final_readme = load_first_10_repo(driver)

#     # # Load next 10 repos
#     # if int(results) > 10:
#     #     if st.button("Load More"):
#     #         st.write("Loading More....  \"NOT IMPLEMENTED\"")

#     # driver.quit()

#     st.session_state['chat_history'].append({"role": "assistant", "message": f"Ezzy Bot: {str(results)} results found \n {final_readme}"})

# # Display chat history
# with messages:
#     for entry in st.session_state['chat_history']:
#         role = entry["role"]
#         message = entry["message"]
#         with st.chat_message(role):
#             st.write(message)

