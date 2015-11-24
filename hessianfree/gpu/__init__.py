import os

import pycuda.autoinit
from pycuda.autoinit import device
from pycuda.compiler import SourceModule

from hessianfree.gpu import kernel_wrappers
from hessianfree.gpu.kernel_wrappers import (m_dot, iadd, J_dot, sum_cols,
                                             mv_dot)


def parse_kernels():
    with open(os.path.join(os.path.dirname(__file__), "kernels.cu")) as f:
        code = f.read()

    with open(os.path.join(os.path.dirname(__file__), "m_dot.cu")) as f:
        m_dot = f.read()

    m_dot = m_dot.replace("%tile_len%", "32")

    # create versions of the function with transpose hard-coded, so it can
    # be compiled more efficiently
    funcs = m_dot.split("__global__ void")
    new_funcs = []
    for f in funcs:
        if "%transpose_a%" in f:
            for t_a in ["0", "1"]:
                new_funcs += [f.replace("%transpose_a%", t_a)]
        else:
            new_funcs += [f]

    funcs = new_funcs
    new_funcs = []
    for f in funcs:
        if "%transpose_b%" in f:
            for t_b in ["0", "1"]:
                new_funcs += [f.replace("%transpose_b%", t_b)]
        else:
            new_funcs += [f]

    code += "__global__ void".join(new_funcs)

    return code

pycuda.autoinit.context.set_shared_config(
    pycuda.driver.shared_config.FOUR_BYTE_BANK_SIZE)

kernels = SourceModule(parse_kernels())

m_dot_kernel = [[kernels.get_function("shared_m_dot_%s_%s" % (a, b))
                 for b in ["0", "1"]] for a in ["0", "1"]]
mv_dot_kernel = [[kernels.get_function("mv_dot_%s_%s" % (a, b))
                  for b in ["0", "1"]] for a in ["0", "1"]]