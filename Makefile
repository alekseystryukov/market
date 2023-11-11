RELEASES_FILE ?= market/market/releases.txt
write-versions-file:
	git for-each-ref --count=10 --sort='-creatordate' --format='%(refname:strip=2)==>%(contents)===' 'refs/tags' > $(RELEASES_FILE)
