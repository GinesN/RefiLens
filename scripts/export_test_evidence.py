"""Derive authentic partial SEC evidence from the exact cached source hashes; no network calls."""
import argparse
import json

from bs4 import BeautifulSoup

from app.core.config import ROOT, settings
from app.extraction.filing import MATURITY_TAGS
from app.extraction.profiles import PROFILES, profile_for
from app.ingestion.sec import read_preserved

parser = argparse.ArgumentParser()
parser.add_argument('--ticker', default='NUE', choices=list(PROFILES))
args = parser.parse_args()
profile = profile_for(args.ticker)
prefix = args.ticker.lower() + '-2025'
snapshot = json.loads((ROOT / 'fixtures' / (prefix + '.json')).read_text())


def cached(url: str) -> bytes:
    return read_preserved(settings.cache_dir, url, snapshot['source_manifest'][url]['sha256'])


soup = BeautifulSoup(cached(snapshot['filing']['source_url']), 'xml')
rows = []
for fact in snapshot['facts']:
    element = soup.find(id=fact['source_url'].split('#')[-1])
    if element is None:
        raise ValueError('Actual source element not found.')
    row = element.find_parent('tr')
    text = str(row if row is not None else element)
    if text not in rows:
        rows.append(text)
if args.ticker == 'NUE':
    maturity = next(p for p in soup.find_all('p') if 'Annual aggregate long-term debt maturities are:' in p.get_text(' ', strip=True))
elif args.ticker == 'LECO':
    maturity = next(p for p in soup.find_all('p') if p.get_text(' ', strip=True).startswith('Maturities of long-term debt, including payments for amounts due banks,'))
else:
    maturity = soup.find('nonFraction', attrs={'name': 'us-gaap:' + MATURITY_TAGS[0]}).find_parent('table')
partial = BeautifulSoup('<excerpt>' + ''.join(rows) + str(maturity) + '</excerpt>', 'xml')
context_ids = {e.get('contextRef') for e in partial.find_all('nonFraction')}
unit_ids = {e.get('unitRef') for e in partial.find_all('nonFraction')}
contexts = ''.join(str(c) for c in soup.find_all('context') if c.get('id') in context_ids)
units = ''.join(str(u) for u in soup.find_all('unit') if u.get('id') in unit_ids)
wrapper = ('<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml" '
           'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" '
           'xmlns:xbrldi="http://xbrl.org/2006/xbrldi"><body>')
excerpt = wrapper + contexts + units + '<table>' + ''.join(rows) + '</table>' + str(maturity) + '</body></html>'
(ROOT / 'fixtures' / (prefix + '-excerpt.xhtml')).write_text(excerpt)
facts_url = next(u for u in snapshot['source_manifest'] if '/companyfacts/' in u)
full = json.loads(cached(facts_url))
tags = {tag for tag, kind in profile['concepts'].values()} | set(MATURITY_TAGS) | {profile.get('maturity_total_tag', '')}
subset = {key: {'units': {'USD': [r for r in value.get('units', {}).get('USD', []) if r.get('accn') == snapshot['filing']['accession']]}}
          for key, value in full['facts']['us-gaap'].items() if key in tags}
(ROOT / 'fixtures' / (prefix + '-companyfacts.json')).write_text(json.dumps({'facts': {'us-gaap': subset}}, indent=2) + '\n')
print(args.ticker, 'authentic partial excerpt', len(excerpt), 'characters;', len(subset), 'original taxonomy records')
