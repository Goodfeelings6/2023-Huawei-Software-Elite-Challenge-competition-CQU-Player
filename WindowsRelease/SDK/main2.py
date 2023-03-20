#!/bin/bash
# coding=GB2312
import sys
import numpy as np
import math

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

        # 机器人调度控制
        self.isRobotOccupy = [0 for i in range(4)] # 标识机器人是否占用,1占用,0空闲
        self.robotTargetId = [0 for i in range(4)]   # 被占用机器人需要前往的目标工作台id(仅当 isRobotOccupy[i]==1 时i位置数据有效)
        self.robotTargetOrid = [(0,0) for i in range(4)] # 被占用机器人需要前往的目标工作台坐标
        self.robotTargetScore = [0 for i in range(4)] # 机器人目前执行任务的打分
        self.robotTaskType = [0 for i in range(4)] # 被占用机器人目前的任务类型,只考虑buy和sell,0表示buy,1表示sell
        self.robotObjOccupyTime = [0 for i in range(4)] # 机器人的已持续持有物品时间

        # 工作台预定表(读入地图时顺序初始化,可预定成品格、物品格, 0未被预定、1被预定)
        self.wtReservation = []
        # self.param_need = 0.01
        # self.param_buy_dist = 1
        # self.param_need_dist = 0
        # self.param_haveProduct = 0
        # self.param_produce = 0
        # self.param_lackRate = 1
        # self.param_sell_dist = 0.5
        # 参数
        #@@@
        self.param_need = 0.733333
        self.param_buy_dist = 0.666667
        self.param_need_dist = 0.866667
        self.param_remainTime = 0.533333
        self.param_haveProduct = 0.333333
        self.param_produce = 0.133333
        self.param_lackRate = 0.533333
        self.param_sell_dist = 0.733333
        #@@@
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
                    self.wtTypeNum[int(char)] += 1
                    dic = {}
                    dic['product'] = 0
                    for i in self.demandTable[int(char)]:
                        dic[i] = 0
                    self.wtReservation.append(dic)
                    
            # 继续读取
            inputLine = sys.stdin.readline()
        # 识别地图,设定参数
        wtNum = sum(self.wtTypeNum)
        if wtNum == 31:
            self.param_need = 0.000000
            self.param_buy_dist = 1.000000
            self.param_need_dist = 0.333333
            self.param_remainTime = 0.5
            self.param_haveProduct = 0.666667
            self.param_produce = 0.533333
            self.param_lackRate = 0.466667
            self.param_sell_dist = 0.400000
        elif wtNum == 17:
            self.param_need = 0.133333
            self.param_buy_dist = 0.533333
            self.param_need_dist = 0.933333
            self.param_remainTime = 0.5
            self.param_haveProduct = 0.733333
            self.param_produce = 0.866667
            self.param_lackRate = 0.933333
            self.param_sell_dist = 0.733333
        elif wtNum == 18:
            self.param_need = 0.266667
            self.param_buy_dist = 0.733333
            self.param_need_dist = 0.800000
            self.param_remainTime = 0.5
            self.param_haveProduct = 0.800000
            self.param_produce = 0.333333
            self.param_lackRate = 0.933333
            self.param_sell_dist = 0.200000
        elif wtNum == 50:
            self.param_need = 0.200000
            self.param_buy_dist = 0.800000
            self.param_need_dist = 0.066667
            self.param_remainTime = 0.5
            self.param_haveProduct = 0.000000
            self.param_produce = 0.666667
            self.param_lackRate = 0.133333
            self.param_sell_dist = 0.933333
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
    
    def buyCmp(self,x,robot_id,needType,buy_dist,need_dist,remainTime):
        _need =  needType[self.workTable[x]['type']][1]/needType[self.workTable[x]['type']][0]
        _buy_dist = buy_dist[x]
        _need_dist = need_dist[x]
        # _remainTime = 1/(1+abs((_buy_dist/6)*50-remainTime[x]))
        _remainTime = 1/(abs((_buy_dist/6)*50-remainTime[x])+1)

        return self.param_need * _need + self.param_buy_dist * 1/_buy_dist + self.param_need_dist * 1/_need_dist + self.param_remainTime * _remainTime

    def getBestBuyTask(self,robot_id):
        """
        # 根据场面信息,返回一个较优的买任务及其分数
        ##### buy:
        ##### 候选任务条件: 工作台类型1-7,对应买物品类型1-7 and 成品格不为空(==1) and 成品未被其他机器人预定
        """
        ### 统计场上的需求 
        epl = 1e-8
        needType = {1:[epl,0],2:[epl,0],3:[epl,0],4:[epl,0],5:[epl,0],6:[epl,0],7:[epl,0]}  # 物品类型:(格子总数,空缺格子数)
        for idx,workT in enumerate(self.workTable):   
            for objType in self.demandTable[workT['type']]:
                needType[objType][0] += 1
                if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # 空缺且不被预定
                    needType[objType][1] += 1 

        
        buy_dist = {} # 工作台id:与机器人距离
        need_dist = {} # 工作台id:与最近需求者距离
        remainTime = {} # 工作台剩余生产时间帧
        for idx,workT in enumerate(self.workTable):
            # 能买的条件,进行过滤           
            if workT['type'] >= 1 and workT['type'] <= 7 and self.wtReservation[idx]['product']==0 and needType[workT['type']][1]!=0:
                if workT['productState']==1 or workT['remainTime']>0: # 有成品 或正在生产中
                    ### 统计买的距离              
                    buy_dist[idx] = np.linalg.norm([self.robot[robot_id]['x']-self.workTable[idx]['x'],self.robot[robot_id]['y']-self.workTable[idx]['y']])
                    ### 统计与最近需求者距离
                    objT = workT['type']
                    for idx2,workT2 in enumerate(self.workTable): 
                        # 如果是一个有效需求者
                        if objT in self.demandTable[workT2['type']] and (workT2['rawState']>>objT)&1==0 and self.wtReservation[idx2][objT]==0:
                            # 维护最小距离
                            tmp_dist = np.linalg.norm([workT['x']-workT2['x'],workT['y']-workT2['y']])
                            if idx not in need_dist.keys() or tmp_dist < need_dist[idx]:
                                need_dist[idx] = tmp_dist
                    remainTime[idx] = workT['remainTime']
        # buy task 收集
        buyTask = [] # 工作台id
        for idx,workT in enumerate(self.workTable):
            # 能买的条件,进行过滤           
            if workT['type'] >= 1 and workT['type'] <= 7 and self.wtReservation[idx]['product']==0 and needType[workT['type']][1]!=0 \
                and (workT['productState']==1 or workT['remainTime']>0 )\
                and (buy_dist[idx]+need_dist[idx])/6+1.5 < (9000-self.frameId)*0.02:
                buyTask.append(idx) 
        # buy task 排序
        buyTask.sort(key=lambda x : self.buyCmp(x,robot_id,needType,buy_dist,need_dist,remainTime), reverse=True)   

        # buy task 选择
        if len(buyTask)!=0:
            score = self.buyCmp(buyTask[0],robot_id,needType,buy_dist,need_dist,remainTime)
            return buyTask[0], score
        else:
            return None,None

    def sellCmp(self,x,robot_id):
        _haveProduct = 1 if self.workTable[x]['productState']==0 else 0

        remindT = self.workTable[x]['remainTime']
        if remindT==-1:
            _produce = 1
        elif remindT==0:
            _produce = 0
        else:
            _produce = 1 / remindT

        total_count = 0
        lack_count = 0
        for objType in self.demandTable[self.workTable[x]['type']]:
            total_count += 1
            if (self.workTable[x]['rawState']>>objType)&1==0 : # 缺少
                lack_count += 1
        _lackRate = (total_count-lack_count) / total_count
        
        _sell_dist = np.linalg.norm([self.robot[robot_id]['x']-self.workTable[x]['x'],self.robot[robot_id]['y']-self.workTable[x]['y']])

        return  self.param_haveProduct * _haveProduct + self.param_produce * _produce + self.param_lackRate * _lackRate + self.param_sell_dist * 1/_sell_dist

    def getBestSellTask(self,robot_id):
        """
        # 根据场面信息,返回一个较优的卖任务及其分数
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

        # sell task 排序
        sellTask.sort(key=lambda x : self.sellCmp(x,robot_id), reverse=True)

        # sell task 选择
        if len(sellTask)!=0:
            score = self.sellCmp(sellTask[0],robot_id)
            return sellTask[0], score
        else:
            return None,None

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
                    task,score = self.getBestBuyTask(i)
                    if task!=None: 
                        # 更新机器人调度状态
                        self.robotTargetId[i] = task 
                        self.robotTargetScore[i] = score
                        self.isRobotOccupy[i] = 1
                        self.robotTaskType[i] = 0
                        self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                        # 更新工作台预定表
                        self.wtReservation[task]['product'] = 1
                    else: # 没buy任务可分配
                        pass
                # 分配sell任务
                elif self.robot[i]['type'] != 0:
                    task,score = self.getBestSellTask(i)
                    if task!=None: 
                        # 更新机器人调度状态
                        self.robotTargetId[i] = task 
                        self.robotTargetScore[i] = score
                        self.isRobotOccupy[i] = 1
                        self.robotTaskType[i] = 1
                        self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                        # 更新工作台预定表
                        if self.workTable[task]['type']==8 or self.workTable[task]['type']==9: # 不需预定，一直可卖
                            self.wtReservation[task][self.robot[i]['type']] = 0
                        else:
                            self.wtReservation[task][self.robot[i]['type']] = 1
                    else: # 没sell任务可分配
                        pass
                # 不分配
                else:  
                    pass

            # 被占用的“买任务机器人”的任务重分配（抢占）
            # if self.robot[i]['type']==0 and self.isRobotOccupy[i] == 1: # 
            #     task,score = self.getBestBuyTask(i)
            #     if task!=None and score/self.robotTargetScore[i] > 20: # 重分配
            #         # 原分配取消
            #         self.wtReservation[self.robotTargetId[i]]['product'] = 0

            #         # 更新机器人调度状态
            #         self.robotTargetId[i] = task 
            #         self.robotTargetScore[i] = score
            #         self.isRobotOccupy[i] = 1
            #         self.robotTaskType[i] = 0
            #         self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
            #         # 更新工作台预定表
            #         self.wtReservation[task]['product'] = 1


    def getInstrAndUpdate(self):
        """
        # 根据机器人本身状态和执行的任务类型
        # 1、更新机器人占用情况
        # 2、产生控制指令并返回
        """
        self.instr = ''
        # for i in range(4):
        #     x_i = self.robot[i]['x']
        #     y_i = self.robot[i]['y']
        #     # 正常的目标工作台
        #     if self.robotTargetOrid[i][0]==self.workTable[self.robotTargetId[i]]['x'] and self.robotTargetOrid[i][1]==self.workTable[self.robotTargetId[i]]['y']:
        #         # 预测相撞
        #         a = self.robot[i]['orientation'] # 朝向角
        #         vector_a = np.array([math.cos(a),math.sin(a)]) # 机器人i朝向向量
        #         for j in range(i+1,4):
        #             x_j = self.robot[j]['x']
        #             y_j = self.robot[j]['y']
        #             x_bar = self.robot[j]['x'] - self.robot[i]['x']
        #             y_bar = self.robot[j]['x'] - self.robot[i]['y']
        #             vector_b = np.array([x_bar,y_bar]) # 机器人i当前位置指向机器人j的向量
        #             dist_a = np.linalg.norm(vector_a)
        #             dist_b = np.linalg.norm(vector_b) # 机器人i与机器人j的距离
        #             dot = np.dot(vector_a,vector_b)     # 点积

        #             cos_theta = dot/(dist_a*dist_b) # 向量a转到b的转向角余弦值 
        #             theta = math.acos(round(cos_theta,10)) # a -> b 转向角
        #             if dist_b < 2.6 and abs(theta) < math.pi/5 and self.robot[i]['orientation']*self.robot[j]['orientation']<=0:  # 相反方向
        #                     # 计算虚假的目标工作台坐标
        #                     theta1 = math.pi/6
        #                     x_i_bar = (x_j-x_i) * math.cos(theta1) - (y_j-y_i) * math.sin(theta1) + x_i
        #                     y_i_bar = (x_j-x_i) * math.sin(theta1) + (y_j-y_i) * math.cos(theta1) + y_i
        #                     x_i_bar =  (x_i_bar - x_i) / (2 * math.cos(theta1)) + x_i
        #                     y_i_bar =  (y_i_bar - y_i) / (2 * math.cos(theta1)) + y_i
                            
        #                     theta1 = -theta1
        #                     x_j_bar = (x_j-x_i) * math.cos(theta1) - (y_j-y_i) * math.sin(theta1) + x_i
        #                     y_j_bar = (x_j-x_i) * math.sin(theta1) + (y_j-y_i) * math.cos(theta1) + y_i
        #                     x_j_bar =  (x_i_bar - x_i) / (2 * math.cos(theta1)) + x_i
        #                     y_j_bar =  (y_i_bar - y_i) / (2 * math.cos(theta1)) + y_i

        #                     self.robotTargetOrid[i] = (x_i_bar, y_i_bar)
        #                     self.robotTargetOrid[j] = (x_j_bar, y_j_bar)
        #     # 虚假的目标工作台
        #     else:
        #         # 如果到达则设回正常的目标工作台
        #         if pow(self.robot[i]['x'] - self.robotTargetOrid[i][0], 2) + pow(self.robot[i]['y'] - self.robotTargetOrid[i][1], 2) < pow(0.4, 2):
        #             self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
        #         # 未到达
        #         else:
        #             pass


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
                    # 更新工作台预定表
                    self.wtReservation[self.robotTargetId[i]][self.robot[i]['type']] = 0

        
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
                
                '''
                持有物品：质量为0.88247 kg
                最大加速度：283.295 m/s*s (5.6659 m/s*frame)
                最大角加速度：403.4115 pi/s*s (8.06823 pi/s*frame)

                不持有物品：质量为0.63617 kg
                最大加速度：392.976 m/s*s (7.85952 m/s*frame)
                最大角加速度：776.2503 pi/s*s (15.525 pi/s*frame)
                '''
                # 角速度
                angle_v = min(theta/0.02, math.pi) if theta>0 else max(theta/0.02, -math.pi)
                self.instr += 'rotate %d %f\n' % (i,angle_v)

                #速度
                x = self.robot[i]['x']
                y = self.robot[i]['y']
                # 左
                if x<2 and y<48 and y>2 and ((a>=-math.pi and a<-math.pi/2) or (a>math.pi/2 and a<=math.pi)):
                    v = 1
                # 右
                elif x>48 and y<48 and y>2 and a>-math.pi/2 and a<math.pi/2:
                    v = 1
                # 上
                elif x>2 and x<48 and y>48 and a>0 and a<math.pi:
                    v = 1
                # 下
                elif x>2 and x<48 and y<2 and a>-math.pi and a<0:
                    v = 1
                # 左上
                elif x<=2 and y>=48 and ((a>=-math.pi and a<-math.pi/2) or (a>0 and a<=math.pi)):
                    v = 1
                # 左下
                elif x<=2 and y<=2 and ((a>=-math.pi and a<0) or (a>math.pi/2 and a<=math.pi)):
                    v = 1
                # 右上
                elif x>=48 and y>=48 and a>0 and a<math.pi/2:
                    v = 1
                # 右下
                elif x>=48 and y<=2 and a>-math.pi/2 and a<0:
                    v = 1
                else:
                    # v = 6-6*abs(theta)/math.pi
                    v = 6/(abs(theta)+1)
                self.instr = self.instr + 'forward %d %d\n' % (i,v)

            # 占用状态但到达目标点
            elif self.isRobotOccupy[i] == 1 and self.robot[i]['workTableID'] == self.robotTargetId[i]:
                # 在工作台买入或售出
                if self.robotTaskType[i] == 0: # 买
                    if self.workTable[self.robotTargetId[i]]['productState']:
                        self.instr += 'buy %d\n' % (i)
                        # 更新机器人占用情况
                        self.isRobotOccupy[i] = 0
                        self.robotObjOccupyTime[i] = 0 # 物品持有时间,从买入开始计时
                        # 更新工作台预定表
                        self.wtReservation[self.robotTargetId[i]]['product'] = 0
                    else:
                        self.instr = self.instr + 'forward %d %d\n' % (i,0)

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
        self.initMap()

        # 交互
        while True:
            # 每一帧输入(来自判题器)
            end = self.inputData()
            if end:
                break
            # 每一帧输出(机器人控制指令) 
            self.outputData()

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
    
