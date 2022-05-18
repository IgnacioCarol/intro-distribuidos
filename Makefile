# define the name of the virtual environment directory
VENV := venv

# default target, when make executed without arguments
all: venv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

# venv is a shortcut target
venv: $(VENV)/bin/activate

# Temporal run to try CLI
run: venv
	./venv/bin/python3 app.py 2 3  -v

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

# Testing with pytest
test:
	pytest

# Reformatting so it is compliant with pep8
# Back is good but not enough, some changes must be manually done (Read flake8 results)
# For exceptions change .flake file
reformat:
	echo "Reformatting with back"
	black --diff *.py
	black --diff src/*/*.py
	black *.py
	flake8

.PHONY: all venv run clean
