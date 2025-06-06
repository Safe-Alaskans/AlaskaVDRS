## Setup instructions:

Create a Python environment and install the required packages:
```
pip install -r requirements.txt
```
convert_folder.py dependencies:  
Firefox browser:  
Tested on Firefox 116.0.3, in case there are interface changes, install this version from:  
```
https://ftp.mozilla.org/pub/firefox/releases/116.0.3/
```
pdftotext (poppler-utils):  
Linux:
```
sudo apt update
sudo apt install poppler-utils
pdftotext -v
```
Windows (not tested):
```
https://github.com/oschwartz10612/poppler-windows/releases
```
ebook-convert (calibre):  
Linux:
```
sudo apt update
sudo apt install calibre
ebook-convert --version
```
Windows (not tested):
```
https://calibre-ebook.com/download_windows
```