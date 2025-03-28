


import os
import sys
import subprocess
import signal
sys.path.append('../')
from utils.config import Config
from src.utils import *

import os

config_path = '../../conf/conf.yml'  # 配置文件路径
conf = Config(config_path, "", "")
target_file = conf.temp_dir + 'opt_raw.txt'

def runMLIR(cmd):
    stderr = ""
    pro = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8",preexec_fn=os.setsid)
    try:
        stdout, stderr = pro.communicate(timeout=20)
        return_code = pro.returncode
    except subprocess.TimeoutExpired:
        os.killpg(pro.pid,signal.SIGTERM)
        return_code = 999
    return stderr,return_code

def saveOpt():  #保存 mlit-opt --help打印的所有pass
    cmd = conf.mlir_opt +" --help >" + target_file
    print(cmd)
    os.system(cmd)


def getTransPass():  #提取pass中的转换pass。读取所有的pass，去掉降级pass即可
    target_file= r"/home/workdir/tracer/fuzz_tool/temp/opt.txt"
    with open(target_file, 'r',encoding="utf-8") as f:
        opts = f.readlines()

    lower_file= r"/home/workdir/tracer/fuzz_tool/conf/mlir_opt_lower.txt"
    with open(lower_file, 'r',encoding="utf-8") as f:
        opts_lower = f.readlines()

    # opts_lower = [item.replace('-', '--',1) for item in opts_lower]
    # opts_lower = ''.join(opts_lower)
    # with open(lower_file, 'w') as f:
    #     f.write(opts_lower)

    opts_trans = [item for item in opts if item not in opts_lower]

    opts_trans1 = [item for item in opts if item in opts_lower]
    opts_trans2 = [item for item in opts_lower if item not in opts_trans1]
    print(opts_trans2)

    print("#all pass : ",len(opts))
    print("#lower pass : ", len(opts_lower))
    print("#tran pass : ", len(opts_trans))

    #
    # passe_str = ''.join(opts_trans)
    # save_file = r"/home/workdir/tracer/fuzz_tool/conf/mlir_opt_trans.txt"
    # with open(save_file, 'w') as f:
    #     f.write(passe_str)


# 处理mlir-opt中的pass
def preprocessing(content):  #pass预处理  根据--提取pass
    passe_list = []
    i = 0
    for line in content:
        line = line.strip()
        if line.startswith('--'):
            i = i + 1
            pass_ = line.split(" ")[0]
            if pass_=="--emit-bytecode":
                continue
            cmd = "{} {} {}".format(conf.mlir_opt,'/home/workdir/tracer/fuzz_tool/conf/empty.mlir',pass_)

            print(i,'/',len(content))
            stderr = runMLIR(cmd)
            if "Parser" in stderr or "Syntax error" in stderr or "Unknown command" in stderr or pass_ == "--test-pass-crash":
                continue
            if "run on 'builtin.module'" in stderr:
                pass_ = "--pass-pipeline=\"builtin.module(func.func({}))\"".format(pass_.lstrip("--"))

            # print(stderr)
            passe_list.append(pass_)

    print("#all pass : ",str(i))
    print("#valid pass : ", len(passe_list))

    passe_str = '\n'.join(passe_list)
    return passe_str


# 处理测试套件中提取的pass
def preprocessing1(content):  #pass预处理  根据--提取pass
    passe_list = []
    i = 0
    crash = 0
    error = 0
    normal = 0
    for line in content:
        line = line.strip()

        if not line.startswith('-'):
            line = '-' + line

        print(line)

        i = i + 1
        if "emit-bytecode" in line or ".mlir" in line or "filename" in line:
            continue
        cmd = "{} {} {}".format(conf.mlir_opt,'/home/workdir/tracer/fuzz_tool/conf/empty.mlir',line)

        # print(i,'/',len(content))
        stderr,returncode = runMLIR(cmd)
        if "Parser" in stderr or "Syntax error" in stderr or "Unknown command" in stderr or line=="--test-pass-crash":
            continue
        # if "run on 'builtin.module'" in stderr:
        #     pass_ = "--pass-pipeline=\"builtin.module(func.func({}))\"".format(pass_.lstrip("--"))

        if returncode>130:
            crash = crash+ 1
        elif returncode==1:
            error = error+1
        elif returncode == 0:
            normal = normal + 1

        print(returncode)
        print(stderr)
        passe_list.append(line)

    print("#all pass : ",str(i))
    print("#valid pass : ", len(passe_list))

    print("#crash : ", crash)
    print("#error : ", error)
    print("#normal : ", normal)

    passe_str = '\n'.join(passe_list)
    return passe_str

#合并测试套件中提取的pass（带参数）+ mlir-opt提取的pass（不带参数）
def merge(content,content1):
    content = [s.lstrip('-') for s in content]
    content1 = [s.lstrip('-') for s in content1]

    content = ['--'+s for s in content]
    content1 = ['--'+s for s in content1]

    all_pass = content+ content1
    unique_list = list(set(all_pass))

    return  unique_list


if __name__ == '__main__':
    target_file = r"/home/workdir/tracer/fuzz_tool/conf/test_pass.txt"
    save_file = r"/conf/test_pass2.txt"
    with open(target_file, 'r',encoding="utf-8") as f:
        content = f.readlines()
    passe_str = preprocessing1(content) #提取所有pass，并验证
    with open(save_file, 'w') as f:
        f.write(passe_str)


    # with open(target_file, 'r',encoding="utf-8") as f:
    #     content = f.readlines()
    # passe_str = preprocessing1(content) #提取所有pass，并验证
    # # with open(save_file, 'w') as f:
    # #     f.write(passe_str)
    # passe_list = []
    # i = 0
    # for line in content:
    #     # print(line)
    #
    #     i = i + 1
    #     cmd = "{} {} {}".format(conf.mlir_opt, '/home/workdir/tracer/fuzz_tool/conf/empty.mlir', line)
    #
    #
    #     stderr,return_code = runMLIR(cmd)
    #     if return_code>0:
    #         print(i, '/', len(content))
    #         print(line)
    #         print(return_code)
    #         print(stderr)
    #     passe_list.append(line)





    #
    # passe_str = preprocessing1(unique_list) #提取所有pass，并验证
    # with open(save_file, 'w') as f:
    #     f.write(passe_str)
    # getTransPass()

