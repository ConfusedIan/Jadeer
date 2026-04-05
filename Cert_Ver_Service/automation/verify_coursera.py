from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from database import VerificationStatus
from automation.browser import build_driver, _safe_text

def verify_coursera(cert) -> dict:
    driver = build_driver()
    try:
        driver.get(f"https://www.coursera.org/account/accomplishments/verify/{cert.certificate_id}")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.course-name"))
            )
        except TimeoutException:
            return {"status": VerificationStatus.NOT_FOUND, "message": "Certificate not found."}

        full_name  = _safe_text(driver, "h3 strong") or ""
        parts      = full_name.split()
        first_name = parts[0]    if parts          else None
        last_name  = parts[-1]   if len(parts) > 1 else None
        issue_date = None
        strongs    = driver.find_elements(By.CSS_SELECTOR, ".course-details p strong")
        if strongs:
            issue_date = strongs[0].text.strip()

        data = {
            "certificate_name": _safe_text(driver, "h2.course-name"),
            "first_name":       first_name,
            "last_name":        last_name,
            "valid_from":       issue_date,
        }
        data = {k: v for k, v in data.items() if v}

        return {"status": VerificationStatus.VERIFIED, "message": "Certificate verified successfully.", "data": data}

    except Exception as e:
        return {"status": VerificationStatus.ERROR, "message": str(e)}
    finally:
        driver.quit()