import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="royalnet",
    version="5.0a1",
    author="Stefano Pigozzi",
    author_email="ste.pigozzi@gmail.com",
    description="The great bot network of the Royal Games community",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Steffo99/royalnet",
    packages=setuptools.find_packages(),
    install_requires=["python-telegram-bot>=11.1.0",
                      "websockets>=7.0",
                      "psycopg2-binary>=2.8",
                      "aiohttp>=3.5.4",
                      "sqlalchemy>=1.3.2",
                      "Markdown>=3.1",
                      "dateparser>=0.7.1",
                      "discord.py>=1.0.1",
                      "youtube_dl>=2019.4.24",
                      "ffmpeg-python>=0.1.17"],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet"
    ]
)
