import pyautogui
from selenium import webdriver
from bs4 import BeautifulSoup as bs4
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Returns token for authenticating requests
def authenticator(location:str):
    
    chrome_options = Options()
    chrome_options.add_argument(f'--user-data-dir={location}') 
    driver = webdriver.Chrome(options=chrome_options)

    driver.maximize_window()

    # Navigate to a webpage
    driver.get("https://mlog.unitymedia.de/mRic-app/mric")
    
    # Wait for the page to load
    WebDriverWait(driver, 5)  # 5 seconds timeout
    
    completed = False
    i = 0
    while not completed and i < 3: 
        print(f"Attempt {i+1}")
        try:
            WebDriverWait(driver, 300).until(EC.title_contains("Vodafone - mLogistics"))
            body_data = bs4(driver.page_source, 'html.parser')
            body_elem = body_data.find('body')
            token = [v for v in body_elem.find('script', type='text/javascript').string.split('\n') if v][1]
            if '//PARAM_HERE' in token:        
                # Find the position of the element on the screen
                element_image = 'single_sign_in_button.png'
                element_position = pyautogui.locateOnScreen(element_image)

                if element_position is not None:
                    # Get the center coordinates of the element
                    element_center = pyautogui.center(element_position)

                    # Click the element
                    pyautogui.click(element_center.x, element_center.y)
                else:
                    print("Element not found on the screen.")   
            else:
                completed = True
                token = token.replace(';', '').replace("'", '').split('=')[-1]
        except TimeoutException as e:
            print("Timeout Error due to bad internet or user failed to login on time")
        except pyautogui.ImageNotFoundException as e:
            print("Make sure the element is visible on the screen")
        
        i += 1
        
    if not completed:
        print("Failed to authenticate")
        driver.quit()
        return None
    return token
    