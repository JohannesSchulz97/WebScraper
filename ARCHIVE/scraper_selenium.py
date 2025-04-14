from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
"""
    We import the ChromeDriverManager, which is a utility that automatically downloads 
    the correct version of the ChromeDriver binary for our system. 
    This is useful because it saves us from having to manually download and manage the driver binary ourselves.
    The ChromeDriver is an executable that acts as a server to control the Chrome browser from us (the client).
    Selenium uses this driver to send commands to the browser and retrieve information from it.    
"""
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


"""
    The init_driver function initializes a Selenium WebDriver instance with specified options.
    This WebDriver takes the ChromeDriverManager as a service, which automatically manages the ChromeDriver binary for us.
"""
def init_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1200,800")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

"""
    Many times, websites will show a cookie consent banner when you first visit them.
    This prevents the WebDriver from clicking on the elements we want to interact with.
    The accept_cookies function waits for the cookie consent button to be clickable and clicks it.
"""
def accept_cookies(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("Accepted cookies.")
        time.sleep(1)
    except Exception as e:
        print("No cookie banner found or could not click it:", e)

def expand_all_sections(driver, max_rounds=10):
    wait = WebDriverWait(driver, 10)
    expanded_count = 0

    for round_num in range(max_rounds):
        print(f"\n🔁 Expansion round {round_num + 1}")
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[aria-expanded="false"]')
        clicked_this_round = 0

        for i, button in enumerate(buttons):
            try:
                # Class name filtering
                class_name = button.get_attribute("class") or ""
                if "SectionDataComponent" not in class_name and "AccordionSectionComponent" not in class_name:
                    continue

                # Scroll into view to avoid click interception
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.3)

                # Try clicking the button
                button.click()
                time.sleep(0.5)

                expanded_count += 1
                clicked_this_round += 1

            except Exception as e:
                print(f"⚠️ Could not click button #{i}: {e}")
                continue  # Skip problematic buttons

        if clicked_this_round == 0:
            print("✅ No more buttons to expand.")
            break

    print(f"\n✅ Finished. Expanded {expanded_count} sections total.")


def main():
    driver = init_driver(headless=False)
    driver.get("https://www.merckvetmanual.com/dog-owners")
    time.sleep(2)

    accept_cookies(driver)
    expand_all_sections(driver)

    input("\nPress Enter to close the browser...")
    driver.quit()

if __name__ == "__main__":
    main()