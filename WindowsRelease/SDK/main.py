#!/bin/bash
import sys
import numpy as np
import math

# 测试,命令行输入：
# 默认调试模式(使用现实时间)  ./robot -m maps/1.txt -c ./SDK "python main.py"
# 快速模式(使用程序时间)     ./robot -m maps/1.txt -c ./SDK -f "python main.py"

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
        # 销毁时间 s (持续占用时间达到销毁时间时就销毁)
        self.destoryTime = 15

        # 固定信息 ：需求表,即每种工作台需要的物品(原材料或成品)类型
        self.demandTable = {1:[],2:[],3:[],4:[1,2],5:[1,3],6:[2,3],7:[4,5,6],8:[7],9:[1,2,3,4,5,6,7]} 

        # 机器人调度控制
        self.isRobotOccupy = [0 for i in range(4)] # 标识机器人是否占用,1占用,0空闲
        self.robotTargetId = [0 for i in range(4)]   # 被占用机器人需要前往的目标工作台id(仅当 isRobotOccupy[i]==1 时i位置数据有效)
        self.robotTargetOrid = [(0,0) for i in range(4)] # 被占用机器人需要前往的目标工作台坐标
        self.robotTaskType = [0 for i in range(4)] # 被占用机器人目前的任务类型,只考虑buy和sell,0表示buy,1表示sell
        self.robotObjOccupyTime = [0 for i in range(4)] # 机器人的已持续持有物品时间

        # 工作台预定表(读入地图时顺序初始化,可预定成品格、物品格, 0未被预定、1被预定)
        self.wtReservation = []

        # ---日志---
        # self.info = open('info.txt', 'w')

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
                    dic = {}
                    dic['product'] = 0
                    for i in self.demandTable[int(char)]:
                        dic[i] = 0
                    self.wtReservation.append(dic)
                    
            # 继续读取
            inputLine = sys.stdin.readline()
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
        # 调度
        self.scheduleRobot()
        # 决策和更新
        instr = self.getInstrAndUpdate()
        # 输出机器人控制指令
        sys.stdout.write(instr)
        
        # 输出结束后,输出 'OK'
        self.finish()
    

    def getBestBuyTask(self):
        """
        # 根据场面信息,返回一个较优的买任务
        ##### buy:
        ##### 候选任务条件: 工作台类型1-7,对应买物品类型1-7 and 成品格不为空(==1) and 成品未被其他机器人预定
        """
        # 先统计场上需要的物品类型 与 数量
        epl = 1e-8
        needType = {1:[epl,0],2:[epl,0],3:[epl,0],4:[epl,0],5:[epl,0],6:[epl,0],7:[epl,0]}  # 物品类型:(格子总数,空缺格子数)
        for idx,workT in enumerate(self.workTable):
            for objType in self.demandTable[workT['type']]:
                needType[objType][0] += 1
                if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # 空缺且不被预定
                    needType[objType][1] += 1
        # buy task 收集
        buyTask = []
        for idx,workT in enumerate(self.workTable):
            if workT['type'] >= 1 and workT['type'] <= 7 and workT['productState']==1 and self.wtReservation[idx]['product']==0:
                buyTask.append(idx)
        
        # buy task 排序
        buyTask.sort(key=lambda x : needType[self.workTable[x]['type']][1]/needType[self.workTable[x]['type']][0], reverse=True)   

        # buy task 选择
        if len(buyTask)!=0:
            return buyTask[0]
        else:
            return None


    def getBestSellTask(self,robot_id):
        """
        # 根据场面信息,返回一个较优的卖任务
        :param robot_id: 待分配卖任务的机器人id
        ## 固定信息
        ##### 工作台类型4 : 卖物品类型1,2       条件：对应物品格二进制位==0 and 对应物品格未被其他机器人预定
        ##### 工作台类型5 : 卖物品类型1,3       条件：对应物品格二进制位==0 and 对应物品格未被其他机器人预定
        ##### 工作台类型6 : 卖物品类型2,3       条件：对应物品格二进制位==0 and 对应物品格未被其他机器人预定
        ##### 工作台类型7 : 卖物品类型4,5,6     条件：对应物品格二进制位==0 and 对应物品格未被其他机器人预定
        ##### 工作台类型8 : 卖物品类型7         条件：无
        ##### 工作台类型9 : 卖物品类型1-7       条件：无
        整理如下：
        ##### sell:
        ##### 卖物品类型1, 条件：((工作台类型==4 or 工作台类型==5) and 类型1物品格为空(==0) and 类型1物品格未被其他机器人预定) or 工作台类型==9
        ##### 卖物品类型2, 条件：((工作台类型==4 or 工作台类型==6) and 类型2物品格为空(==0) and 类型2物品格未被其他机器人预定) or 工作台类型==9 
        ##### 卖物品类型3, 条件：((工作台类型==5 or 工作台类型==6) and 类型3物品格为空(==0) and 类型3物品格未被其他机器人预定) or 工作台类型==9
        ##### 卖物品类型4, 条件：( 工作台类型==7 and 类型4物品格为空(==0) and 类型4物品格未被其他机器人预定) or 工作台类型==9
        ##### 卖物品类型5, 条件：( 工作台类型==7 and 类型5物品格为空(==0) and 类型5物品格未被其他机器人预定) or 工作台类型==9
        ##### 卖物品类型6, 条件：( 工作台类型==7 and 类型6物品格为空(==0) and 类型6物品格未被其他机器人预定) or 工作台类型==9
        ##### 卖物品类型7, 条件：工作台类型==8 or 工作台类型==9
        """
        # sell task 收集
        sellTask = [] 
        # 物品类型
        objType = self.robot[robot_id]['type']
        for idx,workT in enumerate(self.workTable):
            if objType == 1:
                if ((workT['type']==4 or workT['type']==5) and (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0) or workT['type']==9:
                    sellTask.append(idx)
            elif objType == 2:
                if ((workT['type']==4 or workT['type']==6) and (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0) or workT['type']==9:
                    sellTask.append(idx)
            elif objType == 3:
                if ((workT['type']==5 or workT['type']==6) and (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0) or workT['type']==9:
                    sellTask.append(idx)
            elif objType == 4:
                if (workT['type']==7 and (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0) or workT['type']==9:
                    sellTask.append(idx)
            elif objType == 5:
                if (workT['type']==7 and (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0) or workT['type']==9:
                    sellTask.append(idx)
            elif objType == 6:
                if (workT['type']==7 and (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0) or workT['type']==9:
                    sellTask.append(idx)
            elif objType == 7:
                if workT['type']==8 or workT['type']==9:
                    sellTask.append(idx)
        # sell task 选择
        if len(sellTask)!=0:
            idx = np.random.randint(0,len(sellTask))
            return sellTask[idx]
        else:
            return None

    def scheduleRobot(self):
        """
        # 给空闲机器人分配任务,调度
        ##### 策略：未携带物品的空闲机器人 分配 buy任务, 携带物品的空闲机器人 分配 sell任务 
        """       
        # 任务 = 一个工作台id , 表示机器人要前往此工作台 , 执行 buy 或 sell  

        # 把任务分配给空闲机器人
        for i in range(4):
            if self.isRobotOccupy[i] == 0: # if 空闲
                # 分配buy任务
                if self.robot[i]['type'] == 0:
                    task = self.getBestBuyTask()
                    if task!=None: 
                        # 更新机器人调度状态
                        self.robotTargetId[i] = task 
                        self.isRobotOccupy[i] = 1
                        self.robotTaskType[i] = 0
                        self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                        # 更新工作台预定表
                        self.wtReservation[task]['product'] = 1
                    else: # 没buy任务可分配
                        pass
                # 分配sell任务
                elif self.robot[i]['type'] != 0:
                    task = self.getBestSellTask(i)
                    if task!=None: 
                        # 更新机器人调度状态
                        self.robotTargetId[i] = task 
                        self.isRobotOccupy[i] = 1
                        self.robotTaskType[i] = 1
                        self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                        # 更新工作台预定表
                        self.wtReservation[task][self.robot[i]['type']] = 1
                    else: # 没sell任务可分配
                        pass
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
            # 物品持有时间计时
            if self.robot[i]['type'] != 0:
                self.robotObjOccupyTime[i] += 0.02

            # 持有物品时间超时
            if self.robotObjOccupyTime[i] >= self.destoryTime:
                self.instr += 'destroy %d\n' % (i)
                # 更新机器人占用情况
                self.isRobotOccupy[i] = 0
                self.robotObjOccupyTime[i] = 0
            # 占用状态且未到达目标点
            elif self.isRobotOccupy[i] == 1 and self.robot[i]['workTableID'] != self.robotTargetId[i]: 
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
                if dist_b >= 2.5 :
                    v = 6
                elif dist_b >= 1 :
                    v = 5
                elif dist_b >= 0.8 :
                    v = 4
                elif dist_b >= 0.5 :
                    v = 3
                elif dist_b >= 0.2 :
                    v = 2
                elif dist_b >= 0.05 :
                    v = 1
                else:
                    v = 0
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
                    self.robotObjOccupyTime[i] = 0 # 物品持有时间,从买入开始计时
                    # 更新工作台预定表
                    self.wtReservation[self.robotTargetId[i]]['product'] = 0

                elif self.robotTaskType[i] == 1 : # 卖
                    self.instr += 'sell %d\n' % (i)
                    # 更新机器人占用情况
                    self.isRobotOccupy[i] = 0
                    # 更新工作台预定表
                    self.wtReservation[self.robotTargetId[i]][self.robot[i]['type']] = 0
            else: # 空闲状态
                pass

        return self.instr

    def run(self):
        """
        # 初始化,并与判题器进行交互
        """
        # 初始化
        solver.initMap()

        # 交互
        while True:
            # 每一帧输入(来自判题器)
            end = solver.inputData()
            if end:
                break
            # 每一帧输出(机器人控制指令) 
            solver.outputData()

        #     #日志
        #     if self.frameId % 50 == 1:
        #     # if 1:
        #         robot_ordin = []
        #         self.info.write("时间帧："+str(self.frameId)+"\n")
        #         self.info.write("工作台："+str(self.workTable)+"\n")
        #         for i in range(4):
        #             self.info.write("机器人："+str(self.robot[i])+"\n")
        #             robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
        #         self.info.write("指令：\n"+str(self.instr))
        #         self.info.write("是否占用      :"+str(self.isRobotOccupy)+"\n")
        #         self.info.write("目标工作台ID  :"+str(self.robotTargetId)+"\n")
        #         self.info.write("目标工作台坐标 :"+str(self.robotTargetOrid)+"\n")
        #         self.info.write("机器人坐标    :"+str(robot_ordin)+"\n")
        #         self.info.write("机器人任务类型 :"+str(self.robotTaskType)+"\n")
        #         self.info.write("机器人占用时间 :"+str(self.robotObjOccupyTime)+"\n")
        #         self.info.write("\n")
                
        
        # # 关闭日志文件
        # self.info.close()


if __name__ == '__main__':
    
    solver = Solution()
    solver.run()
    
