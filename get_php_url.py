import urllib.request
import re

url = "https://windows.php.net/download/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Find the first Thread Safe x64 zip
match = re.search(r'href="(/downloads/releases/php-8\.\d+\.\d+-Win32-vs16-x64\.zip)"', html)
if match:
    print(f"https://windows.php.net{match.group(1)}")
else:
    print("Not found")
