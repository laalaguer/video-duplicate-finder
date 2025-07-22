# Install for user on the system.
install:
	python3 --version
	pip3 install --user -r requirements.txt

# Create virtual environment and install.
dep:
	python3 --version
	python3 -m venv .env && . .env/bin/activate && pip3 install -r requirements.txt

