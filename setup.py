

# vendor
from setuptools import setup

# local
from readable import __version__


def main():
    setup(
        name = 'readable',
        version = __version__,
        description = "Port of Arc90's readability Javascript extractor",
        license = 'Apache 2.0',
        maintainer = 'Patrick Hensley',
        maintainer_email = 'spaceboy@indirect.com',
        packages = ['readable'],
        package_data = {
            'readable': ['testdata/*.html']
            }
    )


if __name__ == '__main__':
    main()

