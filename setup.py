import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gonha",
    version=version,
    author="Fred Cox",
    author_email="fredcox@gmail.com",
    description="Light-weight system monitor for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fredcox/gonha",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.8',
    scripts=['bin/gonha'],

    install_requires=[
        'PyQt5'
    ],
    include_package_data=True,
    zip_safe=False,
)
