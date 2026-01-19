# 🤖 BPJS OSS & Lapakasik Automation Bot

[![Termux](https://img.shields.io/badge/Termux-Compatible-green)](https://termux.com)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Automation bot untuk proses OSS BPJS Ketenagakerjaan dan Lapakasik secara otomatis menggunakan Python dan Playwright.

## ✨ Fitur Utama

- ✅ **Auto Login OSS** dengan token built-in
- ✅ **Auto Solve CAPTCHA** menggunakan 2Captcha API
- ✅ **Multi-KPJ Processing** (batch processing)
- ✅ **Data Extraction** dari modal hasil pencarian
- ✅ **Auto Submit ke Lapakasik** dengan data yang didapat
- ✅ **Telegram Notifications** (opsional)
- ✅ **Logging Lengkap** dengan timestamp
- ✅ **Result Export** ke JSON format
- ✅ **Termux Optimized** untuk Android

## 📦 Instalasi Cepat (Termux)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/botkjs_oss.git
cd botkjs_oss

# 2. Jalankan installer
bash install.sh

# 3. Edit daftar KPJ
nano kpj_list.txt

# 4. Jalankan bot
python main.py