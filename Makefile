.PHONY: check

check:
	python3 tools/check_repo.py
	python3 tools/check_m3.py
	python3 -m unittest discover -s tests -p 'test_*.py'
