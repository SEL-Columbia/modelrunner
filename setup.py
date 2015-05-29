from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = list(f.read().splitlines())

# Parse the version from the fiona module.
with open('modelrunner/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue

setup(
    name="modelrunner",
    version=version,
    packages=find_packages(),
    description="System for managing long model runs",
    long_description=open("README.md").read(),
    url='https://github.com/SEL-Columbia/modelrunner',
    install_requires=required, 
    scripts = ['scripts/job_server.py', 
               'scripts/job_worker.py',
               'scripts/job_primary.py']
)
