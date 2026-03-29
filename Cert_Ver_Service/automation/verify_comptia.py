import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from database import VerificationStatus
from automation.browser import build_driver, _safe_text

def verify_comptia(cert) -> dict:
    driver = build_driver()
    try:
        driver.get("https://cp.certmetrics.com/CompTIA/en/public/verify/credential")
        wait = WebDriverWait(driver, 30)

        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[formcontrolname='code']")
        )).send_keys(cert.certificate_id)
        driver.find_element(By.CSS_SELECTOR, "button").click()

        wait.until(EC.any_of(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".verify-results__title")),
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".verify-cert-not-found"))
        ))

        if driver.find_elements(By.CSS_SELECTOR, ".verify-cert-not-found"):
            return {"status": VerificationStatus.NOT_FOUND, "message": "Certificate not found."}

        full_name  = _safe_text(driver, ".verify-results__name span") or ""
        parts      = full_name.split()
        first_name = parts[0]    if parts          else None
        last_name  = parts[-1]   if len(parts) > 1 else None
        page_text  = driver.find_element(By.CSS_SELECTOR, ".verify-results").text

        def date_after(label):
            m = re.search(rf"{re.escape(label)}\s*(\d{{4}}-\d{{2}}-\d{{2}})", page_text, re.IGNORECASE)
            return m.group(1) if m else None

        data = {
            "certificate_name": _safe_text(driver, ".verify-results__title span"),
            "first_name":       first_name,
            "last_name":        last_name,
            "valid_from":       date_after("Active since"),
            "valid_to":         date_after("Expires on"),
        }
        data = {k: v for k, v in data.items() if v}

        return {"status": VerificationStatus.VERIFIED, "message": "Certificate verified successfully.", "data": data}

    except TimeoutException:
        return {"status": VerificationStatus.ERROR, "message": "Request timed out."}
    except Exception as e:
        return {"status": VerificationStatus.ERROR, "message": str(e)}
    finally:
        driver.quit()