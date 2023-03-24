#!/bin/bash

import sys
from Strategy1 import Strategy1
from Strategy2 import Strategy2
from Strategy3 import Strategy3
from Strategy4 import Strategy4

# 测试,命令行输入：
# 默认调试模式(使用现实时间)  ./robot -m maps/1.txt -c ./SDK "python main.py"
# 快速模式(使用程序时间)     ./robot -m maps/1.txt -c ./SDK -f "python main.py"
# 默认调试模式使用gui        ./robot_gui -m maps/1.txt -c ./SDK "python main.py"
# 运行全部地图并统计结果      ./run_all

class Solution(object):
    def __init__(self) -> None:       
        # 地图数据
        self.map = []
        # 地图工作台类型数量统计
        self.wtTypeNum = [0 for i in range(0,10)]
        # 工作台数据
        self.workTable = []
        # 机器人数据
        self.robot = []
        # 当前时间帧
        self.frameId = 0
        # 当前金钱数
        self.money = 0
        # 当前控制指令
        self.instr = ''
        # 销毁时间 s (持续占用时间达到销毁时间时就销毁)
        self.destoryTime = 20

        # 固定信息 ：需求表,即每种工作台需要的物品(原材料或成品)类型
        self.demandTable = {1:[],2:[],3:[],4:[1,2],5:[1,3],6:[2,3],7:[4,5,6],8:[7],9:[1,2,3,4,5,6,7]} 

        # 工作台预定表(读入地图时顺序初始化,可预定成品格、物品格, 0未被预定、1被预定)
        self.wtReservation = []

        # 调度、控制策略
        self.strategy = None

    def finish(self):
        """
        # 输出 'OK', 表示当前帧输出完毕
        """
        sys.stdout.write('OK\n')
        sys.stdout.flush()

    def initMap(self):
        """
        # 初始化地图
        """ 
        inputLine = sys.stdin.readline()
        while inputLine.strip() != 'OK':
            # 写入地图
            self.map.append(inputLine)
            # 初始化一些数据
            for char in inputLine:
                if char.isdigit(): # 是一个工作台
                    self.wtTypeNum[int(char)] += 1
                    dic = {}
                    dic['product'] = 0
                    for i in self.demandTable[int(char)]:
                        dic[i] = 0
                    self.wtReservation.append(dic)
                    
            # 继续读取
            inputLine = sys.stdin.readline()

        # 识别地图,设定策略
        wtNum = sum(self.wtTypeNum)
        if wtNum == 43:
            self.strategy = Strategy1(self.destoryTime,self.demandTable,self.wtReservation)
        elif wtNum == 25:
            self.strategy = Strategy2(self.destoryTime,self.demandTable,self.wtReservation)
        elif wtNum == 50:
            self.strategy = Strategy3(self.destoryTime,self.demandTable,self.wtReservation)
        elif wtNum == 18:
            self.strategy = Strategy4(self.destoryTime,self.demandTable,self.wtReservation)

        # 读完后,输出 'OK', 告诉判题器已就绪
        self.finish()

    def inputData(self):
        """
        # 读取来自判题器的场面数据
        """
        end = False
        # 读第一行
        inputLine = sys.stdin.readline()
        if not inputLine: # 读到了EOF
            end = True
            return end
        parts = inputLine.split(' ')
        self.frameId = int(parts[0])
        self.money = int(parts[1])
        
        # 读第二行
        inputLine = sys.stdin.readline()
        workTableNum = int(inputLine)
        
        # 读工作台数据,每一行是一个工作台数据
        self.workTable = []
        for i in range(workTableNum):
            singleWorkTable = dict()
            inputLine = sys.stdin.readline()
            parts = inputLine.split(' ')

            singleWorkTable['type'] = int(parts[0]) # 工作台类型 
            singleWorkTable['x'] = float(parts[1])  # 工作台坐标x
            singleWorkTable['y'] = float(parts[2])  # 工作台坐标y
            singleWorkTable['remainTime'] = int(parts[3])   # 剩余生产时间(帧数)
            singleWorkTable['rawState'] = int(parts[4])     # 原材料格状态
            singleWorkTable['productState'] = int(parts[5]) # 产品格状态

            self.workTable.append(singleWorkTable)

        # 读机器人数据,共4个,每一行是一个机器人数据
        self.robot = []
        for i in range(4):
            singleRobot = dict()
            inputLine = sys.stdin.readline()
            parts = inputLine.split(' ')

            singleRobot['workTableID'] = int(parts[0])     # 所处工作台 ID
            singleRobot['type'] = int(parts[1])            # 携带物品类型
            singleRobot['timeRate'] = float(parts[2])      # 时间价值系数
            singleRobot['collisionRate'] = float(parts[3]) # 碰撞价值系数
            singleRobot['angV'] = float(parts[4])          # 角速度
            singleRobot['linV_x'] = float(parts[5])        # 线速度x
            singleRobot['linV_y'] = float(parts[6])        # 线速度y
            singleRobot['orientation'] = float(parts[7])   # 朝向
            singleRobot['x'] = float(parts[8])             # 机器人坐标x
            singleRobot['y'] = float(parts[9])             # 机器人坐标y

            self.robot.append(singleRobot)
        
        # 读取判题器的 'OK'
        sys.stdin.readline()
        
        return end

    def outputData(self):
        """
        # 输出机器人的控制数据
        """
        # 第一行输出帧ID
        sys.stdout.write('%d\n' % self.frameId)
        # 给策略对象发送数据
        self.strategy.getMessage(self.workTable,self.robot,self.frameId)
        # 运行策略对象
        self.strategy.run()
        # 策略对象返回 指令
        self.instr = self.strategy.sentMessage()
        # 输出机器人控制指令
        sys.stdout.write(self.instr)
        # 输出结束后,输出 'OK'
        self.finish()

    def run(self):
        """
        # 初始化,并与判题器进行交互
        """
        # 初始化
        self.initMap()

        # 交互
        while True:
            # 每一帧输入(来自判题器)
            end = self.inputData()
            if end:
                break
            # 每一帧输出(机器人控制指令) 
            self.outputData()

            # 日志
            # if self.frameId % 50 == 1:
            # if 1:
                # self.log()
            
    def log(self):
        """
        # 写日志
        """      
        #---日志---
        self.info = open('info.txt', 'w') 

        robot_ordin = []
        self.info.write("时间帧："+str(self.frameId)+"\n")
        self.info.write("工作台："+str(self.workTable)+"\n")
        for i in range(4):
            self.info.write("机器人："+str(self.robot[i])+"\n")
            robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
        self.info.write("指令：\n"+str(self.instr))
        self.info.write("是否占用      :"+str(self.strategy.isRobotOccupy)+"\n")
        self.info.write("目标工作台ID  :"+str(self.strategy.robotTargetId)+"\n")
        self.info.write("目标工作台坐标 :"+str(self.strategy.robotTargetOrid)+"\n")
        self.info.write("机器人坐标    :"+str(robot_ordin)+"\n")
        self.info.write("机器人任务类型 :"+str(self.strategy.robotTaskType)+"\n")
        self.info.write("机器人占用时间 :"+str(self.strategy.robotObjOccupyTime)+"\n")
        self.info.write("\n")
                
        # 关闭日志文件
        self.info.close()

if __name__ == '__main__':
    
    solver = Solution()
    solver.run()