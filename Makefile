PORT ?= 8000
HOST ?= 127.0.0.1
ROOT ?= .
QUERY ?= location:Italy type:org followers:>231
MAX_ORGS ?= 100
TRENDING_LIMIT ?= 100
WATCH_ORGS_FILE ?= data/watchorgs.txt
IGNORE_ORGS_FILE ?= data/ignoreorgs.txt
DATE_ARG := $(if $(SNAPSHOT_DATE),--date $(SNAPSHOT_DATE),)

.PHONY: serve populate trending
serve:
	python3 -m http.server $(PORT) --bind $(HOST) --directory $(ROOT)

populate:
	GITHUB_SEARCH_QUERY='$(QUERY)' MAX_ORGS='$(MAX_ORGS)' WATCH_ORGS_FILE='$(WATCH_ORGS_FILE)' IGNORE_ORGS_FILE='$(IGNORE_ORGS_FILE)' python3 scripts/populate.py $(DATE_ARG)

trending:
	python3 scripts/trending.py --limit $(TRENDING_LIMIT)
