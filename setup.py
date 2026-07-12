from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "franka_ik",  # Module name
        ["ext/franka_ik_pybind.cpp"],  # Source files
        include_dirs=[
            pybind11.get_include(), # Include pybind11 headers
            "third_party/franka_analytical_ik",  # Path to Franka IK headers,
            "third_party/eigen"  # Path to Eigen headers
        ],
        language="c++",  # Specify C++ as the language
    )
]

setup(
    name="franka_ik",
    version="0.1",
    ext_modules=ext_modules,
)