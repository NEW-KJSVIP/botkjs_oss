#!/data/data/com.termux/files/usr/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║        🤖 BPJS OSS & LAPAKASIK BOT INSTALLER        ║"
echo "║                Version 2.0 - Termux                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if running in Termux
if [[ ! -d "/data/data/com.termux/files/usr" ]]; then
    echo -e "${RED}❌ This script is for Termux only!${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Updating Termux packages...${NC}"
pkg update -y && pkg upgrade -y
echo -e "${GREEN}✅ Package update complete${NC}"

echo -e "${YELLOW}[2/6] Installing required packages...${NC}"
pkg install -y python git wget curl proot
echo -e "${GREEN}✅ Packages installed${NC}"

echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install playwright requests aiohttp beautifulsoup4 lxml
echo -e "${GREEN}✅ Python dependencies installed${NC}"

echo -e "${YELLOW}[4/6] Installing Playwright browser...${NC}"
playwright install chromium
echo -e "${GREEN}✅ Browser installed${NC}"

echo -e "${YELLOW}[5/6] Setting up storage...${NC}"
termux-setup-storage

# Create project directory
PROJECT_DIR="$HOME/botkjs_oss"
SHARED_DIR="/storage/emulated/0/BPJS-Bot"

echo -e "${YELLOW}[6/6] Creating directories and files...${NC}"

# Create directories
mkdir -p "$PROJECT_DIR"
mkdir -p "$SHARED_DIR"

# Create kpj_list.txt if doesn't exist
if [[ ! -f "$PROJECT_DIR/kpj_list.txt" ]]; then
    cat > "$PROJECT_DIR/kpj_list.txt" << 'EOF'
# Add your KPJ numbers here (one per line)
# Example:
12345678901
98765432109
11223344556
23456789012
34567890123
EOF
    echo -e "${GREEN}✅ Created kpj_list.txt template${NC}"
fi

# Create config info
cat > "$PROJECT_DIR/CONFIG.txt" << 'EOF'
=== BPJS OSS & LAPAKASIK BOT CONFIGURATION ===

📱 INSTALLATION COMPLETE!

📋 QUICK START:
1. Edit kpj_list.txt with your KPJ numbers:
   nano kpj_list.txt

2. Run the bot:
   python main.py

3. Check results:
   - hasil.json (main results)
   - lapakasik_results.json (Lapakasik results)
   - bpjs_bot.log (detailed logs)

📁 FILE LOCATIONS:
- Project files: ~/botkjs_oss/
- Shared storage: /storage/emulated/0/BPJS-Bot/

⚙️  CONFIGURATION:
- 2Captcha API: Already configured
- OSS Token: Already included
- Headless mode: Disabled (visible browser)

🔧 TROUBLESHOOTING:
1. If browser doesn't start:
   - Run: playwright install chromium
   - Or set headless=True in code

2. If CAPTCHA fails:
   - Check 2Captcha balance
   - Check internet connection

3. If KPJ not found:
   - Verify KPJ format (11 digits)
   - Try manual test on website

📞 SUPPORT:
GitHub: https://github.com/NEW-KJSVIP/botkjs_oss
EOF

# Create symbolic link to shared storage
ln -sf "$SHARED_DIR" "$PROJECT_DIR/shared" 2>/dev/null || true

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE!           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}📋 NEXT STEPS:${NC}"
echo "1. Go to project directory:"
echo -e "   ${YELLOW}cd ~/botkjs_oss${NC}"
echo ""
echo "2. Edit KPJ list:"
echo -e "   ${YELLOW}nano kpj_list.txt${NC}"
echo "   (Add your 11-digit KPJ numbers, one per line)"
echo ""
echo "3. Run the bot:"
echo -e "   ${YELLOW}python main.py${NC}"
echo ""
echo "4. Check results in:"
echo -e "   ${GREEN}~/botkjs_oss/hasil.json${NC}"
echo -e "   ${GREEN}/storage/emulated/0/BPJS-Bot/${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "- Start with 2-3 KPJ for testing"
echo "- Make sure internet is stable"
echo "- Keep Termux open while bot is running"
echo ""
echo -e "${BLUE}🎯 TEST QUICK COMMAND:${NC}"
echo "python -c \"import playwright, requests; print('✅ All packages OK')\""
echo ""

# Make main.py executable
chmod +x "$PROJECT_DIR/main.py" 2>/dev/null || true

echo -e "${GREEN}✅ Installation completed successfully!${NC}"