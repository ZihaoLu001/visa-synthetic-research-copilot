from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "demo" / "manuals" / "assets"
SAMPLE_PDF = ROOT / "demo" / "public_survey_uploads" / "federal_reserve_mobile_payments_excerpt.pdf"


def wait_for_app(url: str, timeout_s: int = 90) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(1)
    raise TimeoutError(f"Streamlit app did not start at {url}")


def start_streamlit(port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault("MODEL_PROVIDER", "watsonx")
    log_dir = ROOT / "demo" / "manuals"
    out = (log_dir / "streamlit_manual_capture.out.log").open("w", encoding="utf-8")
    err = (log_dir / "streamlit_manual_capture.err.log").open("w", encoding="utf-8")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless=true",
            f"--server.port={port}",
            "--server.fileWatcherType=none",
        ],
        cwd=ROOT,
        env=env,
        stdout=out,
        stderr=err,
    )


def screenshot(page: Page, name: str) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ASSET_DIR / name), full_page=False)


def click_tab(page: Page, label: str) -> None:
    page.get_by_role("tab", name=label).click()
    page.wait_for_timeout(1200)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture screenshots for the PDF operation manual.")
    parser.add_argument("--port", type=int, default=8502)
    parser.add_argument("--no-start", action="store_true", help="Use an already running app instead of starting one.")
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Only capture pre-run upload/review screenshots. Useful when watsonx quota is unavailable.",
    )
    args = parser.parse_args()

    app_url = f"http://localhost:{args.port}"
    proc: subprocess.Popen | None = None
    if not args.no_start:
        proc = start_streamlit(args.port)

    try:
        wait_for_app(app_url)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
            page.goto(app_url, wait_until="networkidle")
            page.get_by_text("VCA Synthetic Research Workbench").wait_for(timeout=60000)
            screenshot(page, "01_start.png")

            page.locator('input[type="file"]').set_input_files(str(SAMPLE_PDF))
            page.get_by_text("File loaded:", exact=False).wait_for(timeout=30000)
            page.get_by_text("File loaded:", exact=False).scroll_into_view_if_needed()
            page.wait_for_timeout(700)
            screenshot(page, "02_upload_pdf.png")
            page.get_by_text("Survey text for the agents", exact=True).scroll_into_view_if_needed()
            page.wait_for_timeout(700)
            screenshot(page, "03_review_questions.png")

            if not args.skip_run:
                page.get_by_text("Run synthetic survey and generate insights", exact=True).click()
                page.get_by_text("Run complete:", exact=False).wait_for(timeout=240000)
                page.get_by_text("Run complete:", exact=False).scroll_into_view_if_needed()
                page.wait_for_timeout(700)
                screenshot(page, "04_run_complete_kpis.png")

                click_tab(page, "Consultant Summary")
                screenshot(page, "05_consultant_summary.png")
                click_tab(page, "Question Parser")
                screenshot(page, "06_question_parser_pdf_audit.png")
                click_tab(page, "Segment Explorer")
                screenshot(page, "07_segment_explorer.png")
                click_tab(page, "Persona Responses")
                screenshot(page, "08_persona_responses.png")
                click_tab(page, "Validation")
                screenshot(page, "09_validation.png")
                click_tab(page, "Scorecard")
                screenshot(page, "10_scorecard.png")
                click_tab(page, "Decision Brief")
                page.get_by_text("Consultant Quality Layer", exact=True).scroll_into_view_if_needed()
                page.wait_for_timeout(700)
                screenshot(page, "11_consultant_quality_layer.png")
                page.get_by_role("button", name="Download Consultant Delivery").scroll_into_view_if_needed()
                page.wait_for_timeout(700)
                screenshot(page, "12_delivery_pack.png")

            browser.close()
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(f"Timed out while capturing screenshots: {exc}") from exc
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
