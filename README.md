## Fetch 
---
Simple script to perform health checks on a list of URLs. 

## Installation
---
- Ensure python 3.6+ is installed.
- Run `pip install -r requirements.txt` to install dependencies.
- add and configure `yaml` file with urls to check (see `sample.yaml` for example)
- run `python main.py <path to yaml file>`
- The script also takes an optional `--concurrent` flag to run the checks concurrently. For now concurrency is as many as the number of urls in the yaml file.

