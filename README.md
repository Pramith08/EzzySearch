# Ezzy Search - Github Repository Search Application

This project is a Python application designed to assist new GitHub users and programmers in discovering and using GitHub. It uses Streamlit for the front end and Selenium for web scraping to search GitHub repositories based on user input. The application fetches and displays the top 10 repositories related to the input topic, showing their names, links, and descriptions.

## Features

- User-friendly front-end interface built with Streamlit.
- Automated backend search on GitHub using Selenium.
- Displays the top 10 repositories for a given topic.
- Shows repository names, links, and README descriptions.

## Installation

To run this application, please make sure you have Python installed. Follow the steps below to set up the necessary environment and dependencies:

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/github-repository-search-app.git
    cd github-repository-search-app
    ```

2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Start the Streamlit application in the terminal:
    ```bash
    streamlit run main.py
    ```

2. Open your web browser and go to localhost displayed in the terminal

3. Enter the topic you want to search for in the input box and click the "Submit" button.

4. The application will display the top 10 GitHub repositories related to your topic, along with their names, links, and README descriptions.

## Files

- `app.py`: The main application script.
- `requirements.txt`: A list of Python packages required to run the application.

## Dependencies

- Streamlit
- Selenium

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [Selenium](https://www.selenium.dev/)
- [GitHub](https://github.com/)

---

Feel free to reach out if you have any questions or need further assistance!

