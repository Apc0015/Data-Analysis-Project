import os
import json
import requests
import pandas as pd

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
projects = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d not in ('.git', 'streamlit_app', '__pycache__')]
results = {}
for p in projects:
    proj_path = os.path.join(root, p)
    cfg_path = os.path.join(proj_path, 'project_config.json')
    res = {'config_found': False, 'sources': []}
    if os.path.exists(cfg_path):
        res['config_found'] = True
        try:
            cfg = json.load(open(cfg_path, 'r', encoding='utf-8'))
        except Exception as e:
            res['error'] = f'Failed to parse config: {e}'
            results[p] = res
            continue
        for src in cfg.get('data_sources', []):
            sres = {'name': src.get('name'), 'type': src.get('type'), 'path': src.get('path')}
            path = src.get('path')
            if not path:
                sres['status'] = 'no path'
            elif isinstance(path, str) and path.lower().startswith('http'):
                try:
                    r = requests.head(path, timeout=15, allow_redirects=True)
                    sres['status'] = f'HTTP {r.status_code}'
                except Exception as e:
                    sres['status'] = f'HTTP error: {e}'
            else:
                # local path: resolve relative to project
                local_path = os.path.join(root, path) if not os.path.isabs(path) else path
                if os.path.exists(local_path):
                    try:
                        df = pd.read_csv(local_path, nrows=5)
                        sres['status'] = f'local OK, rows={len(df)}'
                        sres['columns'] = df.columns.tolist()
                    except Exception as e:
                        sres['status'] = f'local read error: {e}'
                else:
                    sres['status'] = 'local file not found'
            res['sources'].append(sres)
    else:
        res['config_found'] = False
    results[p] = res

import json as _json
print(_json.dumps(results, indent=2))
