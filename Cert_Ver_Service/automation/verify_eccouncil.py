import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database import VerificationStatus
from automation.browser import build_driver


def verify_eccouncil(cert) -> dict:
    if not cert.first_name or not cert.last_name:
        return {"status": VerificationStatus.ERROR, "message": "EC-Council requires first_name and last_name."}

    driver = build_driver()
    try:
        driver.get("https://aspen.eccouncil.org/Verify")
        wait = WebDriverWait(driver, 20)

        wait.until(EC.presence_of_element_located((By.ID, "txtname"))).send_keys(f"{cert.first_name} {cert.last_name}")
        driver.find_element(By.ID, "txtcert_number").send_keys(cert.certificate_id)
        driver.find_element(By.ID, "lnkSubmit").click()
        time.sleep(5)

        page = driver.page_source.lower()

        if "invalid member" in page:
            return {"status": VerificationStatus.NOT_FOUND, "message": "Certificate not found."}

        if "credentials which you have entered are valid" not in page:
            return {"status": VerificationStatus.ERROR, "message": "Unable to determine certificate status."}

        certificate_name   = None
        certificate_status = None
        for box in driver.find_elements(By.CSS_SELECTOR, "#CertData .icon-simple-desc"):
            try:
                labels = box.find_elements(By.TAG_NAME, "h4")
                if len(labels) >= 2:
                    label = labels[0].text.strip().lower()
                    value = labels[1].text.strip()
                    if "certification name" in label: certificate_name   = value
                    elif "status"           in label: certificate_status = value
            except Exception:
                continue

        message = "Certificate verified successfully."
        if certificate_status:
            message += f" | Status: {certificate_status}"

        data = {"certificate_name": certificate_name} if certificate_name else None

        return {"status": VerificationStatus.VERIFIED, "message": message, "data": data}

    except Exception as e:
        return {"status": VerificationStatus.ERROR, "message": str(e)}
    finally:
        driver.quit()