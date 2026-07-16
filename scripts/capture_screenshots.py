"""Capture the complete ProjectNext product journey for the GitHub README.

Prerequisites:
    pip install pyppeteer
    frontend at http://127.0.0.1:5174
    backend at http://127.0.0.1:8000
"""

import asyncio
import tempfile
from pathlib import Path

from pyppeteer import launch


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "screenshots"
APP_URL = "http://127.0.0.1:5174"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


async def fill(page, name: str, value: str) -> None:
    selector = f'.wizard-panel [name="{name}"]'
    await page.evaluate(
        """(selector, value) => {
          const element = document.querySelector(selector);
          const prototype = element.tagName === 'TEXTAREA'
            ? HTMLTextAreaElement.prototype
            : HTMLInputElement.prototype;
          Object.getOwnPropertyDescriptor(prototype, 'value').set.call(element, value);
          element.dispatchEvent(new Event('input', { bubbles: true }));
        }""",
        selector,
        value,
    )


async def click_text(page, text: str) -> None:
    matches = await page.xpath(
        f"//form[contains(@class, 'wizard-panel')]//button[contains(normalize-space(.), '{text}')]"
    )
    if not matches:
        raise RuntimeError(f"Button not found: {text}")
    await matches[0].click()


async def capture(page, filename: str) -> None:
    # Let CSS transitions and Chrome's compositor finish before capture.
    await asyncio.sleep(0.8)
    await page.screenshot({"path": str(OUTPUT / filename), "fullPage": False})


async def capture_journey() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        browser = await launch(
            executablePath=CHROME,
            headless=True,
            userDataDir=profile,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--hide-scrollbars"],
        )
        page = await browser.newPage()
        await page.setViewport({"width": 1600, "height": 1000, "deviceScaleFactor": 1})
        try:
            await page.goto(APP_URL, {"waitUntil": "networkidle0"})
            await page.evaluate("window.localStorage.clear()")
            await page.reload({"waitUntil": "networkidle0"})
            await page.waitForSelector(".wizard-panel", {"visible": True})

            await click_text(page, "Data Engineer")
            await fill(page, "name", "Amit")
            await capture(page, "01-career-goal.png")

            await click_text(page, "Continue")
            await page.waitForSelector('.wizard-panel [name="experience_summary"]', {"visible": True})
            await fill(page, "experience_summary", "Data science dashboard and a Python prediction API")
            await fill(page, "target_companies", "Google, Microsoft, product startups")
            await capture(page, "02-experience.png")

            await click_text(page, "Continue")
            await page.waitForSelector('.wizard-panel [name="project_vision"]', {"visible": True})
            await fill(page, "project_vision", "Build a production data platform with streaming pipelines, data quality, lineage, and a decision dashboard")
            await fill(page, "must_have_technologies", "Python, SQL")
            await fill(page, "excluded_technologies", "PHP")
            await capture(page, "03-project-preferences.png")

            await click_text(page, "Generate my roadmap")
            await page.waitForSelector("#results", {"visible": True, "timeout": 90000})
            await page.waitForFunction("document.querySelectorAll('.project-card').length >= 2", {"timeout": 90000})
            await page.evaluate(
                "document.documentElement.style.scrollBehavior='auto'; "
                "window.scrollTo(0, document.getElementById('results').offsetTop - 90)"
            )
            await capture(page, "04-recommendation-dashboard.png")

            await page.evaluate(
                "document.querySelector('.project-card').scrollIntoView({block: 'start'}); "
                "window.scrollBy(0, -90)"
            )
            await capture(page, "05-project-matches.png")

            await page.click(".project-card .blueprint-button")
            await page.waitForSelector(".blueprint-modal .milestone", {"visible": True, "timeout": 30000})
            await capture(page, "06-execution-workspace.png")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_journey())
