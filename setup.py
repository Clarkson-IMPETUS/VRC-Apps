import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="VRC-Apps-IMPETUS",
    version="1.0.1",
    author="Joseph Judge",
    author_email="joe@jojudge.com",
    description="Various applications for the VRC to enhance its capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Clarkson-IMPETUS/VRC-Apps",
    project_urls={
        "Bug Tracker": "https://github.com/Clarkson-IMPETUS/VRC-Apps/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        'pyperclip',
        'pystray',
        'pyMaxFlight-IMPETUS @ git+https://github.com/Clarkson-IMPETUS/pyMaxFlight',
        'pyWSConsole-heyjoeway @ git+https://github.com/heyjoeway/pyWSConsole'
    ],
    include_package_data=True,
    package_data={
        "": ["*.png"]
    }
)
