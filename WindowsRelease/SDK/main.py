#!/bin/bash
import sys
import numpy as np
import math

# 测试，命令行输入：
# 默认调试模式（使用现实时间）  ./robot -m maps/1.txt -c ./SDK "python main.py"
# 快速模式（使用程序时间）     ./robot -m maps/1.txt -c ./SDK -f "python main.py"

class Solution(object):
    def __init__(self) -> None:       
        # 地图数据
        self.map = []
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

        # 调度控制
        self.freeRobotNum = 4 # 空闲机器人数量
        self.isRobotOccupy = [0 for i in range(4)] # 标识机器人是否占用，1占用，0空闲
        self.robotTargetId = [0 for i in range(4)]   # 被占用机器人需要前往的目标工作台id(仅当 isRobotOccupy[i]==1 时i位置数据有效)
        self.robotTargetOrid = [(0,0) for i in range(4)] # 被占用机器人需要前往的目标工作台坐标
        self.robotTaskType = [0 for i in range(4)] # 被占用机器人目前的任务类型，只考虑buy和sell，0表示buy，1表示sell

        # ---日志---
        self.info = open('info.txt', 'w')

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
        self.info.write("init begin\n")
        inputLine = sys.stdin.readline()
        while inputLine.strip() != 'OK':
            # 写入地图
            self.map.append(inputLine)
            # 继续读取
            inputLine = sys.stdin.readline()
        # 读完后，输出 'OK', 告诉判题器已就绪
        self.finish()
        self.info.write("init end\n")


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
        
        # 读工作台数据，每一行是一个工作台数据
        self.workTable = []
        for i in range(workTableNum):
            singleWorkTable = dict()
            inputLine = sys.stdin.readline()
            parts = inputLine.split(' ')

            singleWorkTable['type'] = int(parts[0]) # 工作台类型 
            singleWorkTable['x'] = float(parts[1])  # 工作台坐标x
            singleWorkTable['y'] = float(parts[2])  # 工作台坐标y
            singleWorkTable['remainTime'] = int(parts[3])   # 剩余生产时间（帧数）
            singleWorkTable['rawState'] = int(parts[4])     # 原材料格状态
            singleWorkTable['productState'] = int(parts[5]) # 产品格状态

            self.workTable.append(singleWorkTable)

        # 读机器人数据，共4个，每一行是一个机器人数据
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
        # 调度
        self.scheduleRobot()
        # 决策和更新
        instr = self.getInstrAndUpdate()
        # 输出机器人控制指令
        sys.stdout.write(instr)
        
        # 输出结束后，输出 'OK'
        self.finish()

        
    def scheduleRobot(self):
        """
        # 给空闲机器人分配任务,调度
        ##### 策略：未携带物品的空闲机器人 分配 buy任务， 携带物品的空闲机器人 分配 sell任务 
        ##### 工作台机制
        ##### buy:
        #####     工作台类型1-7 : 买对应物品类型1-7  条件：成品格==1
        ##### sell:
        #####     工作台类型4 : 卖物品类型1,2       条件：对应物品格二进制位==0
        #####     工作台类型5 : 卖物品类型1,3       条件：对应物品格二进制位==0
        #####     工作台类型6 : 卖物品类型2,3       条件：对应物品格二进制位==0 
        #####     工作台类型7 : 卖物品类型4,5,6     条件：对应物品格二进制位==0 
        #####     工作台类型8 : 卖物品类型7         条件：无
        #####     工作台类型9 : 卖物品类型1-7       条件：无
        """

        # 获取排序下标
        # order_idx_list = sorted(range(len(self.workTable)),key=lambda x:(x['productState'],x['type']),reverse=True)
        
        sell_dic = {1:[],2:[],3:[],4:[1,2],5:[1,3],6:[2,3],7:[4,5,6],8:[7],9:[1,2,3,4,5,6,7]}

        # 任务 = 一个工作台id , 表示机器人要前往此工作台 , 执行 buy 或 sell

        # buy task  
        buyTask = []
        for idx,workT in enumerate(self.workTable):
            if workT['type'] >= 1 and workT['type'] <= 7 and workT['productState']==1:
                buyTask.append(idx)

        # sell task
        sellTask = {}
        for i in range(1,8):
            sellTask[i] = []
        for idx,workT in enumerate(self.workTable):
            for objType in sell_dic[workT['type']]:
                if (workT['rawState']>>objType)&1==0:
                    sellTask[objType].append(idx)

        # 把任务分配给空闲机器人
        for i in range(4):
            if self.isRobotOccupy[i] == 0:
                # 分配buy任务
                if self.robot[i]['type'] == 0 and len(buyTask) != 0:   
                    idx = np.random.randint(0,len(buyTask))   
                    self.robotTargetId[i] = buyTask[idx] # 可优化
                    buyTask.remove(buyTask[idx])
                    # 更新机器人调度状态
                    self.freeRobotNum -= 1
                    self.isRobotOccupy[i] = 1
                    self.robotTaskType[i] = 0
                    self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                # 分配sell任务
                elif self.robot[i]['type'] != 0 and len(sellTask[self.robot[i]['type']]) != 0: 
                    idx = np.random.randint(0,len(sellTask[self.robot[i]['type']]))
                    self.robotTargetId[i] = sellTask[self.robot[i]['type']][idx] # 可优化
                    sellTask[self.robot[i]['type']].remove(sellTask[self.robot[i]['type']][idx]) 
                    # 更新机器人调度状态
                    self.freeRobotNum -= 1
                    self.isRobotOccupy[i] = 1
                    self.robotTaskType[i] = 1
                    self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                # 不分配
                else:  
                    pass
                    
    def getInstrAndUpdate(self):
        """
        # 根据机器人本身状态和执行的任务类型
        # 1、更新机器人占用情况
        # 2、产生控制指令并返回
        """
        self.instr = ''
        for i in range(4):
            # 占用状态且未到达目标点
            if self.isRobotOccupy[i] == 1 and self.robot[i]['workTableID'] != self.robotTargetId[i]: 
                a = self.robot[i]['orientation'] # 朝向角
                vector_a = np.array([math.cos(a),math.sin(a)]) # 机器人朝向向量

                x_bar = self.robotTargetOrid[i][0] - self.robot[i]['x']
                y_bar = self.robotTargetOrid[i][1] - self.robot[i]['y']
                vector_b = np.array([x_bar,y_bar]) # 机器人当前位置指向目标点的向量

                dist_a = np.linalg.norm(vector_a)
                dist_b = np.linalg.norm(vector_b) # 机器人与目标点的距离
                
                dot = np.dot(vector_a,vector_b)     # 点积
                cross = np.cross(vector_a,vector_b) # 叉积
                
                cos_theta = dot/(dist_a*dist_b) # 向量a转到b的转向角余弦值 
                theta = math.acos(round(cos_theta,10)) # a -> b 转向角

                if cross < 0: # 应该顺时针转
                    theta = -theta
                else: # 逆时针转
                    theta = theta
                
                # 速度
                if dist_b <= 1 :
                    v = 0
                else:
                    v = 6
                self.instr = self.instr + 'forward %d %d\n' % (i,v)
                
                # 角速度
                a = self.robot[i]['orientation'] # 朝向角
                angle_v = min(theta/0.02, math.pi) if theta>0 else max(theta/0.02, -math.pi)
                self.instr += 'rotate %d %f\n' % (i,angle_v)

            # 占用状态但到达目标点
            elif self.isRobotOccupy[i] == 1 and self.robot[i]['workTableID'] == self.robotTargetId[i]:
                # 在工作台买入或售出
                if self.robotTaskType[i] == 0: # 买
                    self.instr += 'buy %d\n' % (i)
                    # 更新机器人占用情况
                    self.isRobotOccupy[i] = 0
                    self.freeRobotNum += 1
                elif self.robotTaskType[i] == 1 : # 卖
                    self.instr += 'sell %d\n' % (i)
                    # 更新机器人占用情况
                    self.isRobotOccupy[i] = 0
                    self.freeRobotNum += 1
            else: # 空闲状态
                pass

        return self.instr

    def run(self):
        """
        # 初始化，并与判题器进行交互
        """
        # 初始化
        solver.initMap()

        # 交互
        while True:
            # 每一帧输入（来自判题器）
            end = solver.inputData()
            if end:
                break
            # 每一帧输出（机器人控制指令） 
            solver.outputData()

            # 日志
            # if self.frameId % 50 == 1:
            if 0:
                robot_ordin = []
                self.info.write("时间帧："+str(self.frameId)+"\n")
                self.info.write("工作台："+str(self.workTable)+"\n")
                for i in range(4):
                    self.info.write("机器人："+str(self.robot[i])+"\n")
                    robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
                self.info.write("指令：\n"+str(self.instr))
                self.info.write("是否占用      :"+str(self.isRobotOccupy)+"\n")
                self.info.write("目标工作台ID  :"+str(self.robotTargetId)+"\n")
                self.info.write("目标工作台坐标 :"+str(self.robotTargetOrid)+"\n")
                self.info.write("机器人坐标    :"+str(robot_ordin)+"\n")
                self.info.write("机器人任务类型 :"+str(self.robotTaskType)+"\n")
                self.info.write("\n")
                
        
        # 关闭日志文件
        self.info.close()


if __name__ == '__main__':
    
    solver = Solution()
    solver.run()
    
