from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from database import VerificationStatus
from automation.browser import build_driver, _safe_text, _first_match

def verify_edx(cert) -> dict:
    driver = build_driver()
    try:
        driver.get(f"https://verify.edx.org/cert/{cert.certificate_id}")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#validation-status, .accomplishment__statement"))
            )
        except TimeoutException:
            return {"status": VerificationStatus.NOT_FOUND, "message": "Certificate not found."}

        page = driver.page_source.lower()
        if "certificate does not exist" in page or "certificate not found" in page:
            return {"status": VerificationStatus.NOT_FOUND, "message": "Certificate not found."}

        full_name  = _first_match(driver, "span.copy__name", "span.copy_name", ".copy p span") or ""
        parts      = full_name.split()
        first_name = parts[0]    if parts          else None
        last_name  = parts[-1]   if len(parts) > 1 else None

        data = {
            "certificate_name": _first_match(driver, "span.copy__course_name", "span.copy__course__name", ".copy__course span"),
            "first_name":       first_name,
            "last_name":        last_name,
            "valid_from":       _safe_text(driver, "li.item.certificate--date span.value"),
        }
        data = {k: v for k, v in data.items() if v}

        return {"status": VerificationStatus.VERIFIED, "message": "Certificate verified successfully.", "data": data}

    except Exception as e:
        return {"status": VerificationStatus.ERROR, "message": str(e)}
    finally:
        driver.quit()