import os
from setuptools import find_packages, setup

def parse_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    reqs = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-e"):
            reqs.append(line)
    return reqs

setup(
    name="medical_knowledge_assistant",
    version="0.1.0",
    author="Antigravity AI / Medical Assistant Team",
    description="Grounded Medical Knowledge Assistant (RAG System based on Gale Encyclopedia of Medicine)",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=parse_requirements("requirements.txt"),
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Medical Science Apps",
    ],
)
