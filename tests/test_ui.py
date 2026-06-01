from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "http://127.0.0.1:5000"


def test_page_title_is_visible(driver):
    driver.get(BASE_URL)

    title = driver.find_element(By.CSS_SELECTOR, "[data-testid='page-title']")

   assert title.text == "LogDesk"


def test_user_can_create_ticket(driver):
    driver.get(BASE_URL)

    title_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-title']")
    category_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-category']")
    priority_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-priority']"))
    create_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='create-ticket-button']")

    title_input.send_keys("Не работает кнопка отправки")
    category_input.send_keys("Интерфейс")
    priority_select.select_by_value("high")
    create_button.click()

    ticket_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-card']")

    assert "Не работает кнопка отправки" in ticket_card.text
    assert "Интерфейс" in ticket_card.text
    assert "high" in ticket_card.text


def test_empty_title_shows_error_message(driver):
    driver.get(BASE_URL)

    wait = WebDriverWait(driver, 10)

    create_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='create-ticket-button']")
    create_button.click()

    message = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='flash-message']"))
    )

    assert message.text == "Название заявки не может быть пустым."


def test_user_can_change_ticket_status(driver):
    driver.get(BASE_URL)

    title_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-title']")
    create_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='create-ticket-button']")

    title_input.send_keys("Заявка для смены статуса")
    create_button.click()

    status_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='status-select']"))
    change_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='change-status-button']")

    status_select.select_by_value("done")
    change_button.click()

    status_view = driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-status-view']")

    assert status_view.text == "done"


def test_user_can_delete_ticket(driver):
    driver.get(BASE_URL)

    title_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='ticket-title']")
    create_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='create-ticket-button']")

    title_input.send_keys("Заявка для удаления")
    create_button.click()

    delete_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='delete-ticket-button']")
    delete_button.click()

    alert = driver.switch_to.alert
    alert.accept()

    empty_list = driver.find_element(By.CSS_SELECTOR, "[data-testid='empty-list']")

    assert empty_list.text == "Заявок пока нет."


def test_debug_crash_page_has_request_id(driver):
    driver.get(f"{BASE_URL}/debug/crash")

    title = driver.find_element(By.CSS_SELECTOR, "[data-testid='error-title']")
    request_id = driver.find_element(By.CSS_SELECTOR, "[data-testid='request-id']")

    assert title.text == "Ошибка сервера"
    assert request_id.text != ""
