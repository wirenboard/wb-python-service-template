from setuptools import setup


def get_version():
    with open("debian/changelog", "r", encoding="utf-8") as f:
        return f.readline().split()[1][1:-1].split("~")[0]


setup(
    name="wb-python-service-example",
    version=get_version(),
    maintainer="Wiren Board Team",
    maintainer_email="info@wirenboard.com",
    description="Wiren Board Python Service Example",
    url="https://github.com/wirenboard/wb-python-service-example",
    packages=["wb_python_service_example"],
    license="MIT",
)
