import xml.etree.ElementTree as ET
import os

xml_path = r"c:\esp32-project\lore\fallout_wiki_complete.xml"

print(f"Analyzing: {xml_path}")
print(f"File size: {os.path.getsize(xml_path) / (1024*1024):.2f} MB\n")

# Count pages using streaming parser
page_count = 0
namespace_counts = {}
sample_titles = []

try:
    for event, elem in ET.iterparse(xml_path, events=('end',)):
        if elem.tag.endswith('page'):
            page_count += 1
            
            # Extract title and namespace
            title_elem = elem.find('.//{http://www.mediawiki.org/xml/export-0.10/}title')
            ns_elem = elem.find('.//{http://www.mediawiki.org/xml/export-0.10/}ns')
            
            if title_elem is not None and ns_elem is not None:
                title = title_elem.text
                ns = ns_elem.text
                
                # Track namespace distribution
                namespace_counts[ns] = namespace_counts.get(ns, 0) + 1
                
                # Sample first 10 titles
                if len(sample_titles) < 10:
                    sample_titles.append(f"NS={ns}: {title}")
            
            # Clear element to save memory
            elem.clear()
            
            # Progress indicator
            if page_count % 10000 == 0:
                print(f"Processed {page_count:,} pages...")

except Exception as e:
    print(f"Error during parsing: {e}")

print(f"\n{'='*60}")
print(f"TOTAL PAGES IN XML: {page_count:,}")
print(f"{'='*60}\n")

print("Namespace Distribution:")
for ns, count in sorted(namespace_counts.items(), key=lambda x: int(x[0])):
    ns_name = {
        '0': 'Main (Articles)',
        '1': 'Talk',
        '2': 'User',
        '3': 'User talk',
        '6': 'File',
        '10': 'Template',
        '14': 'Category'
    }.get(ns, f'Namespace {ns}')
    print(f"  {ns_name}: {count:,}")

print(f"\nFirst 10 page titles:")
for title in sample_titles:
    print(f"  {title}")