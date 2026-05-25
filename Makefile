PORT ?= 8000
HOST ?= 127.0.0.1
ROOT ?= .
QUERY ?= location:Italy type:org followers:>231
MAX_ORGS ?= 100
DATE_ARG := $(if $(SNAPSHOT_DATE),--date $(SNAPSHOT_DATE),)

.PHONY: serve populate
serve:
	python3 -m http.server $(PORT) --bind $(HOST) --directory $(ROOT)

populate:
	GITHUB_SEARCH_QUERY='$(QUERY)' MAX_ORGS='$(MAX_ORGS)' python3 scripts/populate.py $(DATE_ARG)
