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

def writeFile(filePath:str, data:str , mode = 'w'):
    """
    # 把data写入filePath文件
    """
    f = open(filePath, mode)
    f.write(data)
    f.close()

def getSw(n):
    allBinArray = []
    for i in range(n):
        s = bin(i)[2:]
        s = s.zfill(5)
        binArray = []
        for j in range(5):
            binArray.append(int(s[j]))
        allBinArray.append(binArray)
    return allBinArray

if __name__ == '__main__':
    # 穷举
    moneys = [880000,650000,550000,650000]
    for i in range(4):
        maxMoney = 0
        maxStr = ''
        cmd = 'robot -m maps/%d.txt -c ./SDK -f "python main.py"'%(i+1)
        writeFile('result.txt',"第"+str(i+1)+"张地图\n" ,mode="a")
        sw = getSw(32)
        print(sw)
        for j in range(32):
            for k in range(1,1001,20):
                # 读取
                filePath = "SDK\main.py"
                readData = readFile(filePath)
                # 写入
                pattern2 = r'#@@@[\s\S]*#@@@'
                targetStr = '#@@@\n        self.sw_nearest = %d\n        self.sw_buy_pred = %d\n        self.sw_sell_pred = %d\n        '\
                            'self.param_mps = %d\n        self.sw_abandon = %d\n        self.sw_avoidCrash = %d\n        '\
                            '#@@@' %(sw[j][0],sw[j][1],sw[j][2],k,sw[j][3],sw[j][4])
                replaceResult = re.sub(pattern2,targetStr,readData)
                writeFile(filePath,replaceResult)
                # 调用并返回结果
                result = execCmd(cmd)
                pattern = '\d+'
                match = re.search(pattern,result)
                money = int(match.group())
                # 判断
                if money > moneys[i]:
                    writeStr = '#@@@\nself.sw_nearest = %d\nself.sw_buy_pred = %d\nself.sw_sell_pred = %d\n'\
                            'self.param_mps = %d\nself.sw_abandon = %d\nself.sw_avoidCrash = %d\n'\
                            '#@@@\n' %(sw[j][0],sw[j][1],sw[j][2],k,sw[j][3],sw[j][4])
                    writeFile('result.txt',writeStr ,mode="a")
                    writeFile('result.txt','money = %d\n'%(money) ,mode="a")
                
                if money > maxMoney:
                    maxMoney = money
                    maxStr = '#@@@\nself.sw_nearest = %d\nself.sw_buy_pred = %d\nself.sw_sell_pred = %d\n'\
                            'self.param_mps = %d\nself.sw_abandon = %d\nself.sw_avoidCrash = %d\n'\
                            '#@@@\n' %(sw[j][0],sw[j][1],sw[j][2],k,sw[j][3],sw[j][4])
        # 结果 
        writeFile('result.txt',maxStr ,mode="a")
        writeFile('result.txt','maxMoney = %d\n'%(maxMoney) ,mode="a")
