import asyncio
import json
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright


async def main():
    browsers = ['chromium', 'firefox', 'webkit']
    localidad = int(sys.argv[1]) if len(sys.argv) > 1 else 142652
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    initial_offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False)
            page = await browser.new_page()
            await page.goto('https://app.airdna.co')
            
            try:
                login_link = page.get_by_role("link", name="Log in")
                if await login_link.is_visible(timeout=2000):
                    await login_link.click()
                    await page.wait_for_timeout(500)
            except:
                pass
            
            await page.get_by_placeholder("Email").fill("facudifi@gmail.com")
            await page.get_by_placeholder("Password").fill("Pasco689")
            await page.get_by_role("button", name="Log in").click()
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f'py_firefoxa.png', full_page=True)
            
            url_pattern = f"/submarket/{localidad}/listings"
            response_received = asyncio.Event()
            request_to_offset = {}
            current_offset = initial_offset
            page_size = 100
            total_fetched = 0 + initial_offset
            responses_folder = f"airdna/sources/listings"
            os.makedirs(responses_folder, exist_ok=True)
            
            async def modify_request(route, request):
                nonlocal current_offset, total_fetched
                if url_pattern in request.url and request.method == "POST":
                    if total_fetched >= limit:
                        await route.continue_()
                        return
                    
                    print(">> Intercepted:", request.method, request.url)
                    post_data = request.post_data
                    if post_data:
                        try:
                            data = json.loads(post_data)
                            print(f"Original data (offset: {data.get('pagination', {}).get('offset', 'unknown')}):", json.dumps(data, indent=2))
                            
                            remaining = limit - total_fetched
                            batch_size = min(page_size, remaining)
                            
                            offset_for_this_request = current_offset
                            data["pagination"]["offset"] = offset_for_this_request
                            data["pagination"]["page_size"] = batch_size
                            
                            request_to_offset[request] = offset_for_this_request
                            
                            modified_data = json.dumps(data)
                            print(f"Modified data (offset: {offset_for_this_request}, size: {batch_size}):", json.dumps(data, indent=2))
                            
                            current_offset += batch_size
                            total_fetched += batch_size
                            
                            await route.continue_(post_data=modified_data)
                        except Exception as e:
                            print("Error modifying request:", e)
                            await route.continue_()
                    else:
                        await route.continue_()
                else:
                    await route.continue_()
            
            async def log_response(response):
                nonlocal total_fetched
                if response.request in request_to_offset:
                    offset = request_to_offset[response.request]
                    print("<<", response.status, response.url)
                    try:
                        body = await response.body()
                        body_text = body.decode('utf-8')
                        json_data = json.loads(body_text)
                        filename = os.path.join(responses_folder, f"{localidad}_{offset}.json")
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Response saved to {filename}")
                        print(f"Total fetched so far: {total_fetched}/{limit}")
                        
                        if total_fetched >= limit:
                            print(f"Reached limit of {limit} items. Stopping interception.")
                            await page.unroute("**/*", modify_request)
                            response_received.set()
                        else:
                            response_received.set()

                    except Exception as e:
                        print("Error reading response:", e)
                        response_received.set()
            
            await page.route("**/*", modify_request)
            page.on("response", log_response)
            await page.goto(f'https://app.airdna.co/data/co/12/{localidad}/top-listings')
            await page.wait_for_load_state("networkidle")
            
            print(f"Waiting for responses. Target: {limit} items")
            while total_fetched < limit:
                response_received.clear()
                try:
                    await asyncio.wait_for(response_received.wait(), timeout=60.0)
                    if total_fetched >= limit:
                        break
                    await page.wait_for_timeout(1000)
                except asyncio.TimeoutError:
                    print("Timeout waiting for next response. Browser may need user interaction to trigger more requests.")
                    break
            
            await page.wait_for_timeout(2000)
            print(f"Script finished. Fetched {total_fetched}/{limit} items. Browser will remain open.")
            # await browser.close()

asyncio.run(main())



