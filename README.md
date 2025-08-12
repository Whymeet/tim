# VK Ads Report Automation

This project creates screenshots of VK posts and statistics of the related advertising groups and compiles them into a Word report.

## Requirements

- Python 3.8+
- Google Chrome/Chromium browsers used by [Playwright](https://playwright.dev/)

Install Python dependencies:

```bash
pip install -r requirements.txt
playwright install
```

`playwright install` downloads the browsers required for headless execution.

## Configuration

The project supports proxy configuration and other settings through `config.py`. 

### Setting up the configuration

1. Copy the example configuration:
   ```bash
   copy config.example.py config.py
   ```

2. Edit `config.py` to match your needs:
   - Set `USE_PROXY = True` to enable proxy
   - Configure your proxy server in `PROXY_CONFIG`
   - Adjust browser settings, timeouts, and zoom levels

### Proxy Configuration

#### Quick Enable/Disable Proxy

You can quickly toggle proxy on/off using the included script:

```bash
# Check current proxy status
python proxy_toggle.py

# Enable proxy
python proxy_toggle.py on

# Disable proxy  
python proxy_toggle.py off
```

#### Manual Configuration

Edit `config.py`:

```python
# Enable/disable proxy
USE_PROXY = True  # Set to False to disable

# Proxy settings
PROXY_CONFIG = {
    "server": "http://your-proxy-server.com:8080",
    # "username": "your_username",  # Uncomment if auth needed
    # "password": "your_password",  # Uncomment if auth needed
}
```

Supported proxy types:
- HTTP: `http://proxy.example.com:8080`
- HTTPS: `https://proxy.example.com:8080`
- SOCKS5: `socks5://proxy.example.com:1080`

#### Multiple Proxy Configurations

You can configure multiple proxy servers and switch between them:

```python
PROXY_CONFIGS = {
    "default": {"server": "http://proxy1.com:8080"},
    "backup": {"server": "http://proxy2.com:3128"},
    "socks": {"server": "socks5://proxy3.com:1080"}
}

ACTIVE_PROXY_CONFIG = "default"  # Which one to use
```

## Authentication

Before running the main script you must authenticate in VK and save the session cookies. Run:

```bash
python vk_auth.py
```

A browser window will open. Log into your VK account (complete 2FA if needed) and navigate to `https://ads.vk.com/hq/dashboard/ad_groups`. After the page loads press **Enter** in the terminal. The script will save your session to `vk_storage.json`.

**Note:** If you're using a proxy, make sure to set it up in `config.py` before running authentication.

## Running the script

After authentication simply run:

```bash
python main.py
```

The program reads `posts.xlsx`, takes screenshots of the posts and group statistics and generates a report `Отчет.docx`. All images are stored inside the `assets/` directory.

### Input file

`posts.xlsx` must contain the name of a group in the first column and the links to VK posts in the subsequent columns.

### Output

- `assets/` – folder with screenshots of each post and VK Ads group statistics.
- `Отчет.docx` – generated Word report containing the screenshots.

## Configuration Options

### Browser Settings
```python
BROWSER_CONFIG = {
    "headless": False,  # True for headless mode
    "viewport_width": 1920,
    "viewport_height": 1200,
    "user_agent": None,  # Custom user agent if needed
}
```

### Timeouts
```python
TIMEOUTS = {
    "page_load": 60000,      # Page load timeout (ms)
    "network_idle": 10000,   # Network idle timeout (ms)
    "screenshot_delay": 2000, # Delay before screenshot (ms)
}
```

### VK Ads Screenshot Settings
```python
VK_ADS_CONFIG = {
    "demography_zoom": 0.6,  # Demographics zoom level
    "geo_zoom": 0.7,         # Geography zoom level  
    "overview_zoom": 0.8,    # Overview zoom level
}
```

## Troubleshooting

### Proxy Issues
- Check if your proxy server is running and accessible
- Verify proxy credentials if authentication is required
- Try different proxy types (HTTP vs SOCKS5)
- Disable proxy temporarily: `python proxy_toggle.py off`

### Browser Issues
- If browser doesn't start, try running `playwright install` again
- For headless issues, set `headless: False` in browser config
- Adjust viewport size if screenshots are cut off

