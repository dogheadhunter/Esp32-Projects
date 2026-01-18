import argparse
import time
from pathlib import Path
import requests

WIKI_API = 'https://fallout.wiki/api.php'
WIKI_EXPORT = 'https://fallout.wiki/wiki/Special:Export'
DEFAULT_OUTPUT = 'fallout_wiki_complete.xml'

def get_all_page_titles():
    print('Fetching all page titles...')
    start_time = time.time()
    titles = []
    continue_param = {}
    
    while True:
        params = {'action': 'query', 'list': 'allpages', 'aplimit': 500, 'format': 'json'}
        params.update(continue_param)
        response = requests.get(WIKI_API, params=params)
        response.raise_for_status()
        data = response.json()
        batch = [page['title'] for page in data['query']['allpages']]
        titles.extend(batch)
        if len(titles) % 5000 == 0:
            print(f'  {len(titles):,} titles fetched...')
        if 'continue' not in data:
            break
        continue_param = data['continue']
    
    elapsed = time.time() - start_time
    print(f'Fetched {len(titles):,} titles in {elapsed:.1f}s')
    return titles

def export_all_pages_xml(titles, output_path):
    print(f'\nExporting {len(titles):,} pages to XML...')
    print(f'Output: {output_path}')
    print('Using API export method (paginated batches)...')
    start_time = time.time()
    
    # Use API export with pagination (50 pages per request)
    batch_size = 50
    total_batches = (len(titles) + batch_size - 1) // batch_size
    
    with open(output_path, 'wb') as f:
        # Write XML header
        f.write(b'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" version="0.10">\n')
        
        for i in range(0, len(titles), batch_size):
            batch = titles[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            # API export for this batch
            params = {
                'action': 'query',
                'titles': '|'.join(batch),
                'export': '1',
                'exportnowrap': '1',
                'format': 'xml'
            }
            
            response = requests.get(WIKI_API, params=params, timeout=120)
            response.raise_for_status()
            
            # Extract <page> elements from response (strip outer <mediawiki> wrapper)
            content = response.content
            # Find pages between <mediawiki> tags and extract them
            start_idx = content.find(b'<page>')
            end_idx = content.rfind(b'</page>') + 7
            if start_idx != -1 and end_idx != 6:
                f.write(content[start_idx:end_idx])
                f.write(b'\n')
            
            # Progress update
            if batch_num % 100 == 0 or batch_num == total_batches:
                elapsed = time.time() - start_time
                progress = (batch_num / total_batches) * 100
                print(f'  Batch {batch_num}/{total_batches} ({progress:.1f}%) - {elapsed:.0f}s elapsed')
        
        # Write XML footer
        f.write(b'</mediawiki>\n')
    
    elapsed = time.time() - start_time
    final_size_mb = output_path.stat().st_size / 1024 / 1024
    print(f'\nExport complete! Pages: {len(titles):,}, Size: {final_size_mb:.1f} MB, Time: {elapsed/60:.1f} minutes')

def export_wiki_complete(output_path):
    titles = get_all_page_titles()
    export_all_pages_xml(titles, output_path)

def main():
    parser = argparse.ArgumentParser(description='Export complete Independent Fallout Wiki to XML')
    parser.add_argument('--output', '-o', type=Path, default=Path(__file__).parent.parent.parent / 'lore' / DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_wiki_complete(output_path=args.output)

if __name__ == '__main__':
    main()
