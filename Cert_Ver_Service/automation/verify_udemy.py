import time
from selenium.common.exceptions import TimeoutException
from database import VerificationStatus
from automation.browser import build_driver, _safe_text

def verify_udemy(cert) -> dict:
    driver = build_driver()
    try:
        driver.get(f"https://www.udemy.com/certificate/{cert.certificate_id}")
        time.sleep(10)

        source = driver.page_source
        if "certificate-recipient" not in source:
            if "error__greeting" in source or "we can" in source.lower():
                return {"status": VerificationStatus.NOT_FOUND, "message": "Certificate not found."}
            return {"status": VerificationStatus.ERROR, "message": "Unable to determine certificate status."}

        full_name  = _safe_text(driver, "[data-purpose='certificate-recipient'] a") or ""
        parts      = full_name.split()
        first_name = parts[0]    if parts          else None
        last_name  = parts[-1]   if len(parts) > 1 else None

        data = {
            "certificate_name": _safe_text(driver, "h3[data-purpose='course-title-url'] a"),
            "first_name":       first_name,
            "last_name":        last_name,
        }
        data = {k: v for k, v in data.items() if v}

        return {"status": VerificationStatus.VERIFIED, "message": "Certificate verified successfully.", "data": data if data else None}

    except TimeoutException:
        return {"status": VerificationStatus.ERROR, "message": "Request timed out."}
    except Exception as e:
        return {"status": VerificationStatus.ERROR, "message": str(e)}
    finally:
        driver.quit()