from setuptools import setup, find_packages

setup(
    name="twitchclipselector",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'twitchclipselector=twitchclipselector.__main__:main'
        ]
    },
    install_requires=[
        'twitchAPI>=4.5.0',
        'python-dotenv',
    ],
)