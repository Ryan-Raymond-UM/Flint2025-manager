import argparse
import base64
import collections
import datetime
import docker
import itertools
import json
import logging
import os
import pandas
import pathlib
import threading
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(logging.FileHandler('log.txt'))
lock = threading.Lock()

def store(record, **kwargs):
	output = kwargs['output']
	with lock:
		timestamp = datetime.datetime.fromisoformat(record['timestamp'])
		domain = record['domain']

		(output/'captures'/domain).mkdir(parents=True, exist_ok=True)
		(output/'screenshots'/domain).mkdir(parents=True, exist_ok=True)
		(output/'webpages'/domain).mkdir(parents=True, exist_ok=True)

		capture_path = str(output/'captures'/domain/f'{timestamp}.pcap')
		screenshot_path = str(output/'screenshots'/domain/f'{timestamp}.png')
		webpage_path = str(output/'webpages'/domain/f'{timestamp}.html')

		with open(screenshot_path, 'wb') as file:
			file.write(base64.b64decode(record['screenshot']))
		with open(webpage_path, 'w') as file:
			file.write(record['html'])
		with open(capture_path, 'wb') as file:
			file.write(base64.b64decode(record['pcap']))
		with open(webpage_path, 'w') as file:
			file.write(record['html'])

		record['pcap'] = capture_path
		record['screenshot'] = screenshot_path
		record['html'] = webpage_path

		with open(output/'train_and_test.jsonl', 'a') as file:
			file.write(json.dumps(record) + '\n')

def wait_until_running(container):
	time.sleep(1)

def thread_handler(n, container, queue, **kwargs):
	for i in itertools.count(start=1):
		try:
			url = queue.pop()
		except IndexError as e:
			return
		logging.info(f'{container.id} is scraping {url}')
		code, (stdout, stderr) = container.exec_run(['Flint2025-scrape',
			'--url', str(url),
			'--width', str(kwargs['width']),
			'--height', str(kwargs['height']),
			'--timeout', str(kwargs['timeout'])],
			stdout=True, stderr=True, demux=True)
		if code == 0:
			try:
				record = json.loads(stdout)
				if record['success']:
					logging.info(f'Successfully scraped {url}')
					store(record, **kwargs)
				else:
					logging.info(f'Failed to scrape {url} for some reason')
			except json.decoder.JSONDecodeError as e:
				logging.info(f'{url} JSON error {e}')
				logging.info(stdout[-100:])
		else:
			logging.info(f'{container.id} failed to scrape {url} (code {code})')
		if i % kwargs['lifespan'] == 0:
			logging.info(f'{container.id} has scraped {kwargs["lifespan"]} URLs and is restarting')
			container.restart()
		

def make_thread(n, queue, **kwargs):
	client = docker.from_env()
	container = client.containers.run(
		cap_add=['NET_ADMIN', 'NET_RAW'],
		command=[str(os.getpid())],
		detach=True,
		image=kwargs['image'],
		pid_mode='host')
	wait_until_running(container)

	thread = threading.Thread(target=thread_handler, args=(n, container, queue), kwargs=kwargs)
	return thread

def scrape(**kwargs):
	URLs = pandas.read_csv(kwargs['URLs'])
	queue = collections.deque(URLs[URLs.columns[0]])
	threads = list()
	for n in range(1, 1+kwargs['workers']):
		if queue:
			thread = make_thread(n, queue, **kwargs)
			thread.start()
			threads.append(thread)
		else:
			pass
	for thread in threads:
		thread.join()
		
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--document', help='save document HTML', action='store_true')
	parser.add_argument('-n', '--network', help='save network traffic as PCAP', action='store_true')
	parser.add_argument('-r', '--resume', help='If true, attempts to resume from JSONL', action='store_true')
	parser.add_argument('-s', '--screenshot', help='save screenshot as PNG', action='store_true')
	parser.add_argument('-S', '--shuffle', help='Shuffle the domains before scraping (recommended)', action='store_true')
	parser.add_argument('-o', '--output', help='location for output files', default='./out', type=pathlib.Path)
	parser.add_argument('-W', '--width', help='set width of viewport', default=1024, type=int)
	parser.add_argument('-H', '--height', help='set height of viewport', default=1024, type=int)
	parser.add_argument('-w', '--workers', help='specify number of worker containers to spawn', default=1, type=int)
	parser.add_argument('-t', '--timeout', help='page load timeout in seconds', default=60, type=int)
	parser.add_argument('-I', '--image', help='docker worker image to use', default='ryanray4umich/flint2025-worker', type=str)
	parser.add_argument('-l', '--lifespan', help='how many samples should one worker take before it resets', default=10, type=int)
	parser.add_argument('URLs', help='Name of CSV file containing URLs (or domains) to scrape', type=pathlib.Path)
	args = parser.parse_args()
	print(args)

	scrape(**vars(args))

if __name__ == '__main__':
	main()
