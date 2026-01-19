#!/usr/bin/env python3
"""
🤖 BPJS OSS & LAPAKASIK AUTOMATION BOT
GitHub: https://github.com/YOUR_USERNAME/botkjs_oss
Versi: 2.0 - Termux Optimized
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import aiohttp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bpjs_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BPJSAutomation:
    def __init__(self):
        """Initialize bot with configuration"""
        self.config = {
            # API Keys
            '2captcha_api_key': 'c56fb68f0eac8c8e8ecd9ff8ad6deb58',
            
            # URLs
            'oss_login_url': 'https://oss.bpjsketenagakerjaan.go.id/oss?token=ZW1haWw9U05MTlVUUkFDRVVUSUNBTEBHTUFJTC5DT00mbmliPTAyMjA0MDAyNjA4NTY=',
            'oss_input_url': 'https://oss.bpjsketenagakerjaan.go.id/oss/input-tk',
            'lapakasik_url': 'https://lapakasik.bpjsketenagakerjaan.go.id/?source=e419a6aed6c50fefd9182774c25450b333de8d5e29169de6018bd1abb1c8f89b',
            
            # Settings
            'headless': False,
            'timeout': 60000,
            'delay_between_kpj': 3,
            'max_retries': 3
        }
        
        # Data storage
        self.kpj_list = []
        self.results = []
        self.success_count = 0
        self.failed_count = 0
        
        # Check if running in Termux
        self.is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    
    def show_banner(self):
        """Display banner"""
        banner = """
╔══════════════════════════════════════════════════════════╗
║          🤖 BPJS OSS & LAPAKASIK AUTOMATION BOT         ║
║                   Version 2.0 - Termux                   ║
║            GitHub: github.com/YOUR_USERNAME/botkjs_oss  ║
╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
        
        if self.is_termux:
            print("📱 Detected: Termux Environment")
            print("📍 Files will be saved in: /storage/emulated/0/BPJS-Bot/")
    
    def load_kpj_from_file(self, filename: str = "kpj_list.txt") -> bool:
        """Load KPJ numbers from file"""
        try:
            if not os.path.exists(filename):
                logger.error(f"File {filename} not found!")
                return False
            
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            # Filter and clean lines
            self.kpj_list = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove any non-digit characters
                    kpj = ''.join(filter(str.isdigit, line))
                    if len(kpj) == 11:  # Valid KPJ should be 11 digits
                        self.kpj_list.append(kpj)
                    else:
                        logger.warning(f"Invalid KPJ format: {line}")
            
            logger.info(f"✅ Loaded {len(self.kpj_list)} valid KPJ numbers")
            
            # Show loaded KPJ
            if self.kpj_list:
                print(f"\n📋 Loaded KPJ List ({len(self.kpj_list)} numbers):")
                for i, kpj in enumerate(self.kpj_list[:5], 1):
                    print(f"  {i}. {kpj}")
                if len(self.kpj_list) > 5:
                    print(f"  ... and {len(self.kpj_list) - 5} more")
            
            return len(self.kpj_list) > 0
            
        except Exception as e:
            logger.error(f"Error loading KPJ file: {e}")
            return False
    
    def save_results_to_file(self):
        """Save results to JSON file"""
        try:
            output = {
                'metadata': {
                    'total_processed': len(self.results),
                    'successful': self.success_count,
                    'failed': self.failed_count,
                    'timestamp': datetime.now().isoformat(),
                    'version': '2.0'
                },
                'results': self.results
            }
            
            with open('hasil.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Results saved to hasil.json")
            
            # Also save to shared storage if in Termux
            if self.is_termux:
                shared_path = '/storage/emulated/0/BPJS-Bot/hasil.json'
                os.makedirs(os.path.dirname(shared_path), exist_ok=True)
                with open(shared_path, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                logger.info(f"📁 Also saved to: {shared_path}")
                
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def add_result(self, kpj: str, data: Dict, status: str, details: str = ""):
        """Add a result to results list"""
        result = {
            'kpj': kpj,
            'data': data,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'attempt': len([r for r in self.results if r['kpj'] == kpj]) + 1
        }
        
        self.results.append(result)
        
        # Update counters
        if status == 'SUCCESS':
            self.success_count += 1
            logger.info(f"✅ SUCCESS: KPJ {kpj}")
            print(f"   ✅ Data found: {data.get('nama', 'N/A')}")
        else:
            self.failed_count += 1
            logger.warning(f"❌ FAILED: KPJ {kpj} - {details}")
        
        # Auto-save every 5 results
        if len(self.results) % 5 == 0:
            self.save_results_to_file()
    
    async def solve_captcha_with_2captcha(self, image_path: str) -> Optional[str]:
        """Solve CAPTCHA using 2Captcha API"""
        for attempt in range(3):  # Retry up to 3 times
            try:
                logger.info(f"🔄 Solving CAPTCHA (attempt {attempt + 1})...")
                
                # Read image file
                with open(image_path, 'rb') as img_file:
                    files = {'file': img_file}
                    
                    # Upload to 2Captcha
                    async with aiohttp.ClientSession() as session:
                        upload_url = f"http://2captcha.com/in.php?key={self.config['2captcha_api_key']}&method=post"
                        
                        async with session.post(upload_url, data=files) as response:
                            response_text = await response.text()
                            
                        if 'OK|' not in response_text:
                            logger.error(f"Upload failed: {response_text}")
                            continue
                        
                        captcha_id = response_text.split('|')[1]
                        logger.info(f"📌 CAPTCHA ID: {captcha_id}")
                        
                        # Poll for result (max 60 seconds)
                        for _ in range(30):
                            await asyncio.sleep(2)
                            
                            result_url = f"http://2captcha.com/res.php?key={self.config['2captcha_api_key']}&action=get&id={captcha_id}"
                            async with session.get(result_url) as result_resp:
                                result_text = await result_resp.text()
                            
                            if 'OK|' in result_text:
                                captcha_text = result_text.split('|')[1]
                                logger.info(f"✅ CAPTCHA solved: {captcha_text}")
                                return captcha_text
                            elif 'CAPCHA_NOT_READY' in result_text:
                                continue
                            else:
                                logger.error(f"Solving failed: {result_text}")
                                break
                
            except Exception as e:
                logger.error(f"Error solving CAPTCHA: {e}")
                await asyncio.sleep(3)
        
        return None
    
    async def extract_data_from_page(self, page_content: str) -> Dict:
        """Extract data from OSS result page"""
        data = {}
        
        try:
            # Method 1: Look for modal/table data
            if 'Nama Peserta' in page_content:
                # Try to extract using string methods
                start_idx = page_content.find('Nama Peserta')
                if start_idx != -1:
                    # Look for the value after Nama Peserta
                    substr = page_content[start_idx:start_idx + 500]
                    
                    # Try different patterns
                    import re
                    
                    # Pattern 1: <strong>Nama</strong>
                    nama_pattern = r'<strong[^>]*>(.*?)</strong>'
                    nama_match = re.search(nama_pattern, substr, re.IGNORECASE)
                    if nama_match:
                        data['nama'] = nama_match.group(1).strip()
                    
                    # Pattern 2: NIK
                    nik_pattern = r'NIK.*?(\d{16})'
                    nik_match = re.search(nik_pattern, substr, re.IGNORECASE)
                    if nik_match:
                        data['nik'] = nik_match.group(1)
                    
                    # Pattern 3: Tanggal Lahir
                    tgl_pattern = r'Lahir.*?(\d{2}-\d{2}-\d{4})'
                    tgl_match = re.search(tgl_pattern, substr, re.IGNORECASE)
                    if tgl_match:
                        data['tgl_lahir'] = tgl_match.group(1)
            
            # Method 2: Look for JSON data in script tags
            json_pattern = r'data-peserta\s*=\s*[\'"]([^\'"]+)[\'"]'
            import re
            json_match = re.search(json_pattern, page_content)
            if json_match:
                try:
                    import base64
                    import json as json_lib
                    json_data = base64.b64decode(json_match.group(1)).decode('utf-8')
                    parsed = json_lib.loads(json_data)
                    data.update(parsed)
                except:
                    pass
            
            # Method 3: Simple table extraction
            if 'table' in page_content.lower() and not data:
                # Try to get all text and find patterns
                from html import unescape
                import re
                
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', ' ', page_content)
                text = unescape(text)
                
                # Look for patterns
                patterns = {
                    'nama': r'Nama[:\s]+([A-Za-z\s\.]+)',
                    'nik': r'NIK[:\s]+(\d{16})',
                    'tgl_lahir': r'Lahir[:\s]+(\d{2}-\d{2}-\d{4})',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match and key not in data:
                        data[key] = match.group(1).strip()
            
            logger.info(f"📊 Extracted data: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return data
    
    async def process_single_kpj(self, page, kpj: str) -> Tuple[Dict, str, str]:
        """Process a single KPJ through OSS"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 PROCESSING KPJ: {kpj}")
        logger.info(f"{'='*60}")
        
        try:
            # Navigate to input page
            logger.info("🌐 Navigating to OSS input page...")
            await page.goto(self.config['oss_input_url'], 
                          wait_until='networkidle', 
                          timeout=self.config['timeout'])
            await asyncio.sleep(2)
            
            # Fill KPJ number
            logger.info(f"📝 Filling KPJ: {kpj}")
            
            # Try different input selectors
            input_selectors = [
                'input[name="no_kpj"]',
                'input[id="no_kpj"]',
                'input[type="text"]',
                '#no_kpj',
                '.form-control'
            ]
            
            filled = False
            for selector in input_selectors:
                try:
                    await page.fill(selector, kpj)
                    filled = True
                    break
                except:
                    continue
            
            if not filled:
                # Try to find any input and fill it
                inputs = await page.query_selector_all('input')
                for inp in inputs:
                    input_type = await inp.get_attribute('type')
                    if input_type != 'hidden':
                        await inp.fill(kpj)
                        filled = True
                        break
            
            if not filled:
                raise Exception("Could not find KPJ input field")
            
            # Find and capture CAPTCHA
            logger.info("🖼️ Capturing CAPTCHA...")
            captcha_selectors = [
                '#captcha_img',
                'img[src*="captcha"]',
                '.captcha-img',
                'img[alt*="captcha"]'
            ]
            
            captcha_element = None
            for selector in captcha_selectors:
                captcha_element = await page.query_selector(selector)
                if captcha_element:
                    break
            
            if not captcha_element:
                # Try to find any image that might be CAPTCHA
                images = await page.query_selector_all('img')
                for img in images:
                    src = await img.get_attribute('src') or ''
                    if 'captcha' in src.lower():
                        captcha_element = img
                        break
            
            if not captcha_element:
                raise Exception("CAPTCHA image not found")
            
            # Take screenshot of CAPTCHA
            captcha_path = f"captcha_{kpj}.png"
            await captcha_element.screenshot(path=captcha_path)
            logger.info(f"📸 CAPTCHA saved: {captcha_path}")
            
            # Solve CAPTCHA
            captcha_text = await self.solve_captcha_with_2captcha(captcha_path)
            if not captcha_text:
                return {}, "FAILED", "CAPTCHA solving failed"
            
            logger.info(f"✅ CAPTCHA text: {captcha_text}")
            
            # Fill CAPTCHA
            captcha_input_selectors = [
                'input[name="captcha"]',
                'input[id="captcha"]',
                '#captcha',
                'input[placeholder*="captcha"]'
            ]
            
            filled_captcha = False
            for selector in captcha_input_selectors:
                try:
                    await page.fill(selector, captcha_text)
                    filled_captcha = True
                    break
                except:
                    continue
            
            if not filled_captcha:
                # Find input near CAPTCHA image
                inputs = await page.query_selector_all('input[type="text"]')
                for inp in inputs:
                    await inp.fill(captcha_text)
                    filled_captcha = True
                    break
            
            # Submit form
            logger.info("🚀 Submitting form...")
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '.btn-primary',
                'button:has-text("Submit")',
                'button:has-text("Cari")'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    submitted = True
                    await asyncio.sleep(3)
                    break
                except:
                    continue
            
            if not submitted:
                # Try Enter key
                await page.keyboard.press('Enter')
                await asyncio.sleep(3)
            
            # Wait for response and check result
            logger.info("⏳ Waiting for response...")
            await asyncio.sleep(5)
            
            # Check current page content
            page_content = await page.content()
            
            # Save page for debugging
            debug_path = f"debug_{kpj}.html"
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
            logger.info(f"📄 Debug page saved: {debug_path}")
            
            # Check for success indicators
            success_indicators = [
                'berhasil', 'sukses', 'data ditemukan', 
                'nama peserta', 'NIK', 'status aktif'
            ]
            
            is_success = any(indicator in page_content.lower() 
                           for indicator in success_indicators)
            
            if is_success:
                # Extract data
                data = await self.extract_data_from_page(page_content)
                if data:
                    return data, "SUCCESS", "Data found"
                else:
                    return {'kpj': kpj}, "PARTIAL", "Success but no data extracted"
            else:
                # Check for error messages
                error_indicators = [
                    'gagal', 'tidak ditemukan', 'invalid', 
                    'captcha salah', 'expired', 'error'
                ]
                
                error_msg = "Unknown error"
                for indicator in error_indicators:
                    if indicator in page_content.lower():
                        error_msg = f"Page contains: {indicator}"
                        break
                
                return {}, "FAILED", error_msg
                
        except Exception as e:
            logger.error(f"❌ Error processing KPJ {kpj}: {str(e)}")
            return {}, "ERROR", str(e)
    
    async def process_lapakasik(self, page, data: Dict) -> str:
        """Submit data to Lapakasik"""
        try:
            logger.info("🚀 Processing Lapakasik submission...")
            
            # Navigate to Lapakasik
            await page.goto(self.config['lapakasik_url'], 
                          wait_until='networkidle',
                          timeout=self.config['timeout'])
            await asyncio.sleep(3)
            
            # Fill form fields (adjust selectors based on actual form)
            form_data = {
                'nama': data.get('nama', ''),
                'nik': data.get('nik', ''),
                'no_kpj': data.get('kpj', ''),
                'tgl_lahir': data.get('tgl_lahir', '')
            }
            
            logger.info(f"📝 Form data: {form_data}")
            
            # Try different field mappings
            field_mappings = [
                # Pattern 1: Direct name attributes
                ('input[name="nama"]', 'nama'),
                ('input[name="nik"]', 'nik'),
                ('input[name="no_kpj"]', 'no_kpj'),
                ('input[name="tgl_lahir"]', 'tgl_lahir'),
                
                # Pattern 2: ID attributes
                ('#nama', 'nama'),
                ('#nik', 'nik'),
                ('#no_kpj', 'no_kpj'),
                ('#tgl_lahir', 'tgl_lahir'),
                
                # Pattern 3: Placeholders
                ('input[placeholder*="nama"]', 'nama'),
                ('input[placeholder*="nik"]', 'nik'),
                ('input[placeholder*="kpj"]', 'no_kpj'),
                ('input[placeholder*="lahir"]', 'tgl_lahir')
            ]
            
            filled_fields = 0
            for selector, field_key in field_mappings:
                try:
                    value = form_data.get(field_key, '')
                    if value:
                        await page.fill(selector, value)
                        logger.info(f"✅ Filled {field_key}: {value}")
                        filled_fields += 1
                except:
                    continue
            
            if filled_fields == 0:
                # Last resort: try all text inputs
                inputs = await page.query_selector_all('input[type="text"]')
                for i, inp in enumerate(inputs[:4]):
                    if i < len(form_data):
                        key = list(form_data.keys())[i]
                        value = list(form_data.values())[i]
                        if value:
                            await inp.fill(value)
            
            # Submit form
            logger.info("📤 Submitting Lapakasik form...")
            
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '.btn-success',
                'button:has-text("Submit")',
                'button:has-text("Kirim")',
                'button:has-text("Cek")'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    submitted = True
                    break
                except:
                    continue
            
            if not submitted:
                await page.keyboard.press('Enter')
            
            # Wait and check result
            await asyncio.sleep(5)
            
            # Check current URL and content
            current_url = page.url
            page_content = await page.content()
            
            logger.info(f"🌐 Current URL: {current_url}")
            
            # Check for JMO redirect
            if 'jmo' in current_url.lower():
                return "JMO_REDIRECT"
            
            # Check for success messages
            success_keywords = ['berhasil', 'sukses', 'terdaftar', 'valid']
            if any(keyword in page_content.lower() for keyword in success_keywords):
                return "SUCCESS"
            
            # Check for specific Lapakasik messages
            if 'lapakasik' in page_content.lower():
                return "LAPAKASIK_PROCESSED"
            
            return "UNKNOWN_RESULT"
            
        except Exception as e:
            logger.error(f"❌ Lapakasik error: {e}")
            return f"ERROR: {str(e)}"
    
    async def run_automation(self):
        """Main automation runner"""
        self.show_banner()
        
        # Load KPJ list
        print("\n" + "="*60)
        print("📥 LOADING KPJ LIST")
        print("="*60)
        
        if not self.load_kpj_from_file():
            print("\n❌ No KPJ loaded. Please check kpj_list.txt")
            print("\n📝 Example kpj_list.txt content:")
            print("12345678901")
            print("98765432109")
            print("11223344556")
            return
        
        # Ask for confirmation
        print(f"\n📊 READY TO PROCESS {len(self.kpj_list)} KPJ")
        response = input("👉 Press Enter to start or 'q' to quit: ")
        if response.lower() == 'q':
            print("👋 Exiting...")
            return
        
        # Initialize Playwright
        print("\n" + "="*60)
        print("🚀 INITIALIZING BROWSER")
        print("="*60)
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser
                browser_args = [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer'
                ]
                
                if self.is_termux:
                    # Termux-specific optimizations
                    browser_args.extend([
                        '--single-process',
                        '--no-zygote',
                        '--disable-setuid-sandbox'
                    ])
                
                browser = await p.chromium.launch(
                    headless=self.config['headless'],
                    args=browser_args
                )
                
                # Create context
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Android 10; Mobile) AppleWebKit/537.36',
                    java_script_enabled=True,
                    ignore_https_errors=True
                )
                
                # Create page
                page = await context.new_page()
                
                # Step 1: Login to OSS
                print("\n" + "="*60)
                print("🔐 STEP 1: OSS LOGIN")
                print("="*60)
                
                try:
                    await page.goto(self.config['oss_login_url'],
                                  wait_until='networkidle',
                                  timeout=60000)
                    await asyncio.sleep(3)
                    
                    # Check if login successful
                    current_url = page.url
                    if 'oss' in current_url:
                        print("✅ OSS Login Successful")
                        logger.info("OSS login successful")
                    else:
                        print("⚠️  May need manual login check")
                    
                except Exception as e:
                    print(f"⚠️  Login note: {e}")
                    logger.warning(f"Login note: {e}")
                
                # Step 2: Process KPJ List
                print("\n" + "="*60)
                print("🔄 STEP 2: PROCESSING KPJ LIST")
                print("="*60)
                
                successful_data = []
                
                for idx, kpj in enumerate(self.kpj_list, 1):
                    print(f"\n📊 [{idx}/{len(self.kpj_list)}] Processing: {kpj}")
                    
                    data, status, details = await self.process_single_kpj(page, kpj)
                    
                    # Add result
                    self.add_result(kpj, data, status, details)
                    
                    if status == "SUCCESS":
                        data['kpj'] = kpj
                        successful_data.append(data)
                    
                    # Delay between KPJ
                    if idx < len(self.kpj_list):
                        delay = self.config['delay_between_kpj']
                        print(f"⏳ Waiting {delay} seconds...")
                        await asyncio.sleep(delay)
                
                # Step 3: Process Lapakasik
                print("\n" + "="*60)
                print("🚀 STEP 3: LAPAKASIK SUBMISSION")
                print("="*60)
                
                if successful_data:
                    print(f"📦 Processing {len(successful_data)} successful data to Lapakasik")
                    
                    lapakasik_results = []
                    for i, data in enumerate(successful_data, 1):
                        print(f"\n📤 [{i}/{len(successful_data)}] Submitting: {data.get('nama', 'Unknown')}")
                        
                        # Create new page for Lapakasik
                        lapakasik_page = await context.new_page()
                        result = await self.process_lapakasik(lapakasik_page, data)
                        
                        lapakasik_results.append({
                            'kpj': data.get('kpj'),
                            'nama': data.get('nama'),
                            'result': result
                        })
                        
                        print(f"   Result: {result}")
                        
                        await lapakasik_page.close()
                        
                        if i < len(successful_data):
                            await asyncio.sleep(3)
                    
                    # Save Lapakasik results
                    with open('lapakasik_results.json', 'w', encoding='utf-8') as f:
                        json.dump(lapakasik_results, f, indent=2, ensure_ascii=False)
                    
                    print(f"\n💾 Lapakasik results saved to: lapakasik_results.json")
                else:
                    print("📭 No successful data to process for Lapakasik")
                
                # Close browser
                await browser.close()
                print("\n🔒 Browser closed")
                
        except ImportError:
            print("\n❌ Playwright not installed!")
            print("Run: pip install playwright && playwright install chromium")
            return
        except Exception as e:
            print(f"\n❌ Browser error: {e}")
            logger.error(f"Browser error: {e}")
        
        # Final save and summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        
        self.save_results_to_file()
        
        print(f"\n📈 PROCESSING COMPLETE!")
        print(f"✅ Successful: {self.success_count}")
        print(f"❌ Failed: {self.failed_count}")
        print(f"📁 Results: hasil.json")
        print(f"📝 Logs: bpjs_bot.log")
        
        if self.is_termux:
            print(f"📍 Also in: /storage/emulated/0/BPJS-Bot/")
        
        # Show sample of successful data
        if self.success_count > 0:
            print(f"\n🎉 SUCCESSFUL DATA FOUND ({self.success_count}):")
            for result in self.results[-5:]:  # Show last 5
                if result['status'] == 'SUCCESS':
                    nama = result['data'].get('nama', 'N/A')
                    print(f"  • {result['kpj']} - {nama}")
        
        print(f"\n✨ Bot completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

def main():
    """Main entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            print("❌ Python 3.7+ required!")
            return
        
        # Create bot instance
        bot = BPJSAutomation()
        
        # Run automation
        asyncio.run(bot.run_automation())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()