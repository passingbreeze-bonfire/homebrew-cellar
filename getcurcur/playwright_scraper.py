# playwright_scraper.py
import asyncio
from playwright.async_api import async_playwright


async def main():
  """
  Playwright를 사용하여 KITA.net에 접속하고, 환율 테이블이 로드된 후 스크린샷을 찍는 메인 함수
  """
  async with async_playwright() as p:
    # Chromium 브라우저를 실행합니다. (headless=False로 설정하면 브라우저 창이 실제로 열립니다)
    browser = await p.chromium.launch(headless=True)

    # 새 페이지를 엽니다.
    page = await browser.new_page()

    try:
      # 요청하신 URL로 이동합니다.
      url = "https://www.kita.net/cmmrcInfo/ehgtGnrlzInfo/rltmEhgt.do"
      print(f"페이지로 이동 중: {url}")

      # 페이지 로드를 기다립니다. timeout을 60초로 넉넉하게 설정합니다.
      await page.goto(url, timeout=60000)

      # 페이지가 성공적으로 로드되었음을 알립니다.
      print("페이지 로드 완료.")

      # 페이지의 제목을 가져와 출력합니다.
      page_title = await page.title()
      print(f"페이지 제목: {page_title}")

      # --- 수정된 부분 ---
      # 환율 정보가 담긴 테이블이 로드될 때까지 기다립니다.
      # KITA.net 페이지의 실제 환율 테이블을 가리키는 선택자입니다.
      exchange_table_selector = "#contents > div.table_wrap > table"
      print(f"'{exchange_table_selector}' 요소가 나타날 때까지 대기합니다...")
      await page.wait_for_selector(exchange_table_selector, timeout=30000)
      print("환율 테이블 로드를 확인했습니다.")
      # --- 수정 끝 ---

      # 현재 페이지를 스크린샷으로 저장합니다.
      screenshot_path = "환율조회_KITA.png"
      await page.screenshot(path=screenshot_path)
      print(f"'{screenshot_path}' 파일로 스크린샷을 저장했습니다.")

    except Exception as e:
      # 오류 발생 시 메시지를 출력합니다.
      print(f"오류가 발생했습니다: {e}")

    finally:
      # 모든 작업이 끝나면 브라우저를 닫습니다.
      await browser.close()
      print("브라우저를 닫았습니다.")


# main 함수를 실행합니다.
if __name__ == "__main__":
  asyncio.run(main())
