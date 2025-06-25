from setuptools import setup, find_packages


setup(
    title="PyQt6 Json TextEdit",
    version="0.9.0",
    author="Björn",
    author_email="pyqt6_json_text_edit@schrammel.dev",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    install_requires=[
        "PyQt6>=6.9.0",
    ]
)