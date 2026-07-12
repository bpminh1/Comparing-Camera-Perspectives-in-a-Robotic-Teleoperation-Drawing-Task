#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "franka_ik_He.hpp"

PYBIND11_MODULE(franka_ik, m) {
    m.doc() = "franka inverse kinematics module"; // optional module docstring
    m.def("franka_IK_EE", &franka_IK_EE, "inverse kinematics w.r.t. End Effector Frame (using Franka Hand data)");
    m.def("franka_IK_EE_CC", &franka_IK_EE_CC, "\"Case-Consistent\" inverse kinematics w.r.t. End Effector Frame (using Franka Hand data)");
}