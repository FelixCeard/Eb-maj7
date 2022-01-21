from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="maj7",
    version="0.9.2",
    author="Felix Ceard-Falkenberg",
    author_email="fece00001@stud.uni-saarland.de",
    description="An interpreter for the programming language Eb-maj7",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["maj7"],
    url="https://github.com/FelixCeard/maj7",
    project_urls={
        "Bug Tracker": "https://github.com/FelixCeard/maj7/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    python_requires=">=3.10",
    scripts=['maj7.py'],
    entry_points={
        'console_scripts': [
            'maj7 = maj7.maj7:run'
        ]
    },
    install_required=[
        'argparse'
    ]
)
