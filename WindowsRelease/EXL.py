import re
import numpy as np
import subprocess

def execCmd(cmd:str)->str:
    """
    # 调用命令行执行命令 cmd ,返回输出的结果
    """
    r = subprocess.check_output(cmd,shell=True,encoding='gbk')
    return r

def readFile(filePath:str)->str:
    """
    # 把filePath文件读取到data中返回
    """
    f = open(filePath, "r",encoding='GB2312')
    data = f.read()
    f.close()
    return data

def writeFile(filePath:str, data:str):
    """
    # 把data写入filePath文件
    """
    f = open(filePath, "w")
    f.write(data)
    f.close()

if __name__ == '__main__':
    cmds = ['robot -m maps/1.txt -c ./SDK -f "python main.py"','robot -m maps/2.txt -c ./SDK -f "python main.py"','robot -m maps/3.txt -c ./SDK -f "python main.py"','robot -m maps/4.txt -c ./SDK -f "python main.py"']
    # 穷举
    for i in range(1,4):
        maxa = 0
        maxb = 0
        maxc = 0
        maxMoney = 0
        for a in np.arange(0, 1, 0.1):
            for b in np.arange(0, 1, 0.1):
                for c in np.arange(0, 1, 0.1):
                    # 读取
                    filePath = "SDK\main.py"
                    readData = readFile(filePath)
                    # 写入
                    pattern2 = r'#@@@[\s\S]*#@@@'
                    targetStr = '#@@@\n        self.a = %f\n        self.b = %f\n        self.c = %f\n        #@@@' %(a,b,c)
                    replaceResult = re.sub(pattern2,targetStr,readData)
                    writeFile(filePath,replaceResult)
                    # 调用并返回结果
                    cmd = cmds[i]
                    result = execCmd(cmd)
                    pattern = '\d+'
                    match = re.search(pattern,result)
                    money = int(match.group())
                    # 判断
                    if maxMoney < money:
                        maxMoney = money
                        maxa = a
                        maxb = b
                        maxc = c
                        print(i," ",money)
                        f = open('result.txt', "a")
                        f.write(str(i)+": "+str(money)+"\n")
                        f.close()
        # 结果
        print("a=%f,b=%f,c=%f"%(maxa,maxb,maxc))
        print("maxMoney=%d"%(maxMoney))
        f = open('result.txt', "a")
        f.write(str(i)+"\n")
        f.write("a=%f,b=%f,c=%f\n"%(maxa,maxb,maxc))
        f.write("maxMoney=%d\n"%(maxMoney))
        f.close()
