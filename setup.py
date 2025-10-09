from setuptools import setup, find_packages

setup(
    name="automatizacion-outlook",
    version="1.0.0",
    description="Automatización de procesamiento de correos Outlook",
    packages=find_packages(),
    install_requires=[
        "pywin32>=306",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0"
    ],
    python_requires=">=3.7",
)