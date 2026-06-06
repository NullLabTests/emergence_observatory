from setuptools import setup, find_packages

setup(
    name="emergence_observatory",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["flask>=3.0"],
    extras_require={"llm": ["httpx>=0.27"]},
    python_requires=">=3.10",
    entry_points={"console_scripts": ["emobs=run:main"]},
)
