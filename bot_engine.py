#!/usr/bin/env python3
"""
🤖 BPJS BOT ENGINE V1.0
Core engine untuk proses OSS dan Lapakasik
"""

import asyncio
import json
import logging
import os
import sys
import time
import base64
import re
from datetime import datetime
from typing import Dict, List, Optional
import requests
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BPJSBotEngine:
    def __init__(self, task_id: str, kpj_list: List[str]):
        self.task_id = task_id
        self.kpj_list = kpj_list
        self.results = []
        
        # Configuration
        self.config = {
            '2CAPTCHA_API': 'c56fb68f0eac8c8e8ecd9ff8ad6deb58',
            'OSS_LOGIN': 'https://oss.bpjsketenagakerjaan.go.id/oss?token=ZW1haWw9U05MTlVUUkFDRVVUSUNBTEBHTUFJTC5DT00mbmliPTAyMjA0MDAyNjA4NTY=',
            'OSS_INPUT': 'https://oss.bpjsketenagakerjaan.go.id/oss/input-tk',
            'LAPAKASIK': 'https://lapakasik.bpjsketenagakerjaan.go.id/?source=e419a6aed6c50fefd9182774c25450b333de8d5e29169de6018bd1abb1c8f89b',
            'HEADLESS': True,
            'TIMEOUT': 60000,
            'DELAY_BETWEEN': 3,
            'MAX_RETRY': 3
        }
    
    def solve_captcha(self, image_path: str) -> Optional[str]:
        """Solve CAPTCHA using 2Captcha"""
        try:
            logger.info(f"[{self.task_id}] Solving CAPTCHA...")
            
            # Upload image to 2Captcha
            with open(image_path, 'rb') as f:
                response = requests.post(
                    f"http://2captcha.com/in.php?key={self.config['2CAPTCHA_API']}&method=post",
                    files={'file': f},
                    timeout=30
                )
            
            if 'OK|' not in response.text:
                logger.error(f"CAPTCHA upload failed: {response.text}")
                return None
            
            captcha_id = response.text.split('|')[1]
            logger.info(f"CAPTCHA ID: {captcha_id}")
            
            # Wait for solution
            for i in range(30):  # Max 60 seconds
                time.sleep(2)
                
                result = requests.get(
                    f"http://2captcha.com/res.php?key={self.config['2CAPTCHA_API']}&action=get&id={captcha_id}",
                    timeout=30
                )
                
                if 'OK|' in result.text:
                    captcha_text = result.text.split('|')[1]
                    logger.info(f"CAPTCHA solved: {captcha_text}")
                    return captcha_text
                elif 'CAPCHA_NOT_READY' in result.text:
                    continue
                else:
                    logger.error(f"CAPTCHA solving failed: {result.text}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"CAPTCHA error: {e}")
            return None
    
    def extract_data_from_html(self, html: str) -> Dict:
        """Extract data from OSS response HTML"""
        data = {}
        
        try:
            # Method 1: Look for JSON data
            import re
            
            # Pattern for base64 encoded data
            pattern = r'data-peserta\s*=\s*[\'"]([^\'"]+)[\'"]'
            match = re.search(pattern, html)
            
            if match:
                try:
                    # Try to decode base64
                    json_str = base64.b64decode(match.group(1)).decode('utf-8')
                    json_data = json.loads(json_str)
                    
                    # Map fields
                    data['nama'] = json_data.get('nama', '')
                    data['nik'] = json_data.get('nik', '')
                    data['tgl_lahir'] = json_data.get('tgl_lahir', '')
                    
                    return data
                except:
                    pass
            
            # Method 2: Look for table data
            if 'Nama Peserta' in html:
                # Simple extraction using regex
                nama_pattern = r'Nama\s*[:\s]+([A-Z][A-Z\s\.]+[A-Z])'
                nama_match = re.search(nama_pattern, html, re.IGNORECASE)
                if nama_match:
                    data['nama'] = nama_match.group(1).strip()
                
                nik_pattern = r'NIK\s*[:\s]+(\d{16})'
                nik_match = re.search(nik_pattern, html, re.IGNORECASE)
                if nik_match:
                    data['nik'] = nik_match.group(1)
                
                tgl_pattern = r'Lahir\s*[:\s]+(\d{2}-\d{2}-\d{4})'
                tgl_match = re.search(tgl_pattern, html, re.IGNORECASE)
                if tgl_match:
                    data['tgl_lahir'] = tgl_match.group(1)
            
            # Method 3: Look for modal content
            if 'modal-body' in html:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                modal = soup.find(class_='modal-body')
                if modal:
                    text = modal.get_text()
                    
                    # Extract from text
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if 'Nama' in line and not data.get('nama'):
                            parts = line.split(':', 1)
                            if len(parts) > 1:
                                data['nama'] = parts[1].strip()
                        elif 'NIK' in line and not data.get('nik'):
                            parts = line.split(':', 1)
                            if len(parts) > 1:
                                data['nik'] = parts[1].strip()
                        elif 'Lahir' in line and not data.get('tgl_lahir'):
                            parts = line.split(':', 1)
                            if len(parts) > 1:
                                data['tgl_lahir'] = parts[1].strip()
            
            return data
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return data
    
    async def process_single_kpj(self, page, kpj: str) -> Dict:
        """Process single KPJ"""
        logger.info(f"Processing KPJ: {kpj}")
        
        result = {
            'kpj': kpj,
            'success': False,
            'data': {},
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Navigate to OSS input page
            await page.goto(self.config['OSS_INPUT'], wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Fill KPJ number
            await page.fill('input[name="no_kpj"]', kpj)
            logger.info(f"Filled KPJ: {kpj}")
            
            # Get CAPTCHA image
            captcha_img = await page.query_selector('#captcha_img')
            if not captcha_img:
                logger.error("CAPTCHA image not found!")
                result['error'] = 'CAPTCHA_NOT_FOUND'
                return result
            
            # Take screenshot of CAPTCHA
            captcha_path = f'temp/captcha_{kpj}.png'
            os.makedirs('temp', exist_ok=True)
            await captcha_img.screenshot(path=captcha_path)
            
            # Solve CAPTCHA
            captcha_text = self.solve_captcha(captcha_path)
            if not captcha_text:
                result['error'] = 'CAPTCHA_FAILED'
                return result
            
            # Fill CAPTCHA
            await page.fill('input[name="captcha"]', captcha_text)
            
            # Submit form
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                # Try other selectors
                await page.click('input[type="submit"]')
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Get page content
            html = await page.content()
            
            # Save for debugging
            with open(f'temp/debug_{kpj}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Check if successful
            if 'berhasil' in html.lower() or 'data ditemukan' in html.lower():
                # Extract data
                extracted_data = self.extract_data_from_html(html)
                
                if extracted_data:
                    result['success'] = True
                    result['data'] = extracted_data
                    result['data']['kpj'] = kpj
                    
                    logger.info(f"Success: Found data for {kpj}")
                    
                    # Process Lapakasik
                    lapakasik_result = await self.process_lapakasik(page, result['data'])
                    result['data']['lapakasik'] = lapakasik_result
                    
                    return result
            
            # If not successful
            result['error'] = 'DATA_NOT_FOUND'
            return result
            
        except Exception as e:
            logger.error(f"Error processing {kpj}: {e}")
            result['error'] = str(e)
            return result
    
    async def process_lapakasik(self, page, data: Dict) -> Dict:
        """Submit data to Lapakasik"""
        try:
            logger.info("Processing Lapakasik...")
            
            # Navigate to Lapakasik
            await page.goto(self.config['LAPAKASIK'], wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Fill form fields
            # These selectors might need adjustment based on actual form
            form_data = {
                'nama': data.get('nama', ''),
                'nik': data.get('nik', ''),
                'no_kpj': data.get('kpj', ''),
                'tgl_lahir': data.get('tgl_lahir', '')
            }
            
            # Try different selectors
            selectors = [
                ('input[name="nama"]', 'nama'),
                ('#nama', 'nama'),
                ('input[placeholder*="nama"]', 'nama'),
                
                ('input[name="nik"]', 'nik'),
                ('#nik', 'nik'),
                ('input[placeholder*="nik"]', 'nik'),
                
                ('input[name="no_kpj"]', 'no_kpj'),
                ('#no_kpj', 'no_kpj'),
                ('input[placeholder*="kpj"]', 'no_kpj'),
                
                ('input[name="tgl_lahir"]', 'tgl_lahir'),
                ('#tgl_lahir', 'tgl_lahir'),
                ('input[placeholder*="lahir"]', 'tgl_lahir')
            ]
            
            for selector, key in selectors:
                try:
                    value = form_data.get(key)
                    if value:
                        await page.fill(selector, value)
                except:
                    continue
            
            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '.btn-primary',
                '.btn-success'
            ]
            
            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    break
                except:
                    continue
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Check result
            current_url = page.url
            html = await page.content()
            
            result = {
                'url': current_url,
                'has_jmo': 'jmo' in current_url.lower(),
                'success': 'berhasil' in html.lower() or 'sukses' in html.lower()
            }
            
            if result['has_jmo']:
                logger.info("✅ Lapakasik success - JMO detected")
                result['status'] = 'JMO_REDIRECT'
            elif result['success']:
                logger.info("✅ Lapakasik success")
                result['status'] = 'SUCCESS'
            else:
                logger.warning("⚠️ Lapakasik result unclear")
                result['status'] = 'UNKNOWN'
            
            return result
            
        except Exception as e:
            logger.error(f"Lapakasik error: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    async def run_async(self):
        """Run bot asynchronously"""
        logger.info(f"Starting bot for task {self.task_id} with {len(self.kpj_list)} KPJ")
        
        # Setup Playwright
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=self.config['HEADLESS'],
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # First, login to OSS
                logger.info("Logging into OSS...")
                await page.goto(self.config['OSS_LOGIN'], wait_until='networkidle')
                await asyncio.sleep(3)
                logger.info("OSS login successful")
                
                # Process each KPJ
                for i, kpj in enumerate(self.kpj_list):
                    logger.info(f"Processing {i+1}/{len(self.kpj_list)}: {kpj}")
                    
                    result = await self.process_single_kpj(page, kpj)
                    self.results.append(result)
                    
                    # Save progress
                    progress = int(((i + 1) / len(self.kpj_list)) * 100)
                    
                    # Delay between KPJ
                    if i < len(self.kpj_list) - 1:
                        await asyncio.sleep(self.config['DELAY_BETWEEN'])
                
                logger.info(f"Task {self.task_id} completed")
                
            except Exception as e:
                logger.error(f"Bot execution error: {e}")
                
            finally:
                await browser.close()
        
        return self.results
    
    def run(self):
        """Run bot synchronously"""
        try:
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.run_async())
            loop.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Run error: {e}")
            return []