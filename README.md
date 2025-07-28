This Python3 tool uses Docker to create lots of workers to scrape for you.
Depends on the ryanray4umich/flint2025-worker image.
# Installation
```
pip install -i https://test.pypi.org/simple/ Flint2025-manager
```
# Usage
```
$ Flint2025-manager -h
usage: Flint2025-manager [-h] [-d] [-n] [-r] [-s] [-S] [-o OUTPUT] [-W WIDTH] [-H HEIGHT] [-w WORKERS] [-t TIMEOUT] [-I IMAGE]
                         [-l LIFESPAN]
                         URLs

positional arguments:
  URLs                  Name of CSV file containing URLs (or domains) to scrape

options:
  -h, --help            show this help message and exit
  -d, --document        save document HTML
  -n, --network         save network traffic as PCAP
  -r, --resume          If true, attempts to resume from JSONL
  -s, --screenshot      save screenshot as PNG
  -S, --shuffle         Shuffle the domains before scraping (recommended)
  -o OUTPUT, --output OUTPUT
                        location for output files
  -W WIDTH, --width WIDTH
                        set width of viewport
  -H HEIGHT, --height HEIGHT
                        set height of viewport
  -w WORKERS, --workers WORKERS
                        specify number of worker containers to spawn
  -t TIMEOUT, --timeout TIMEOUT
                        page load timeout in seconds
  -I IMAGE, --image IMAGE
                        docker worker image to use
  -l LIFESPAN, --lifespan LIFESPAN
                        how many samples should one worker take before it resets
```
You need a CSV file containing the URLs to scrape. For example:
```
url
example.com
youtube.com
reddit.com
usa.gov
```

Scrape this URL list using 10 workers:
```
Flint2025-manager -w10 urls.csv
```
