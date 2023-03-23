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

        # 固定信息 ：需求表,即每种工作台需要的物品(原材料或成品)类型
        self.demandTable = {1:[],2:[],3:[],4:[1,2],5:[1,3],6:[2,3],7:[4,5,6],8:[7],9:[1,2,3,4,5,6,7]} 
        # 固定信息 ：物品净利润
        self.income = {1:3000,2:3200,3:3400,4:7100,5:7800,6:8300,7:29000}

        # 机器人调度控制
        self.isRobotOccupy = [0 for i in range(4)] # 标识机器人是否占用,1占用,0空闲
        self.robotTargetId = [[0,0] for i in range(4)]   # 被占用机器人需要前往的目标工作台id(仅当 isRobotOccupy[i]==1 时i位置数据有效)
        self.robotTargetOrid = [[(0,0),(0,0)] for i in range(4)] # 被占用机器人需要前往的目标工作台坐标
        self.robotTaskType = [0 for i in range(4)] # 被占用机器人目前的任务类型,只考虑buy和sell,0表示buy,1表示sell

        # 工作台预定表(读入地图时顺序初始化,可预定成品格、物品格, 0未被预定、1被预定)
        self.wtReservation = []

        self.turning=[0 for i in range(4)]

        # 超参数
        self.abandonThreshold = 0.2  # 机器人 i 放弃当前任务的门限值, 范围0~无穷, 越大越不放弃

        # 参数 
        self.sw_nearest = 0 # 顺路算法 是否开启 0开1关
        self.sw_buy_pred = 1 # 买任务预测 是否开启 1开0关
        self.sw_sell_pred = 1 # 卖任务预测 是否开启 1开0关
        self.param_mps = 50 # 贪心系数 1~1000
        self.sw_abandon = 1 # 放弃当前任务算法 是否开启 1开0关
        self.sw_avoidCrash = 1 # 碰撞避免 是否开启 1开0关

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
        #@@@
        self.sw_nearest = 1
        self.sw_buy_pred = 1
        self.sw_sell_pred = 1
        self.param_mps = 981
        self.sw_abandon = 1
        self.sw_avoidCrash = 1
        #@@@
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
        # 输出机器人控制指令
        sys.stdout.write(self.instr)
        # 输出结束后,输出 'OK'
        self.finish()

    def f(self,x,maxX,minRate):
        """
        # 贬值率计算公式
        """
        if x < maxX:
            return (1-math.sqrt(1-(1-x/maxX)**2))*(1-minRate)+minRate
        elif x >= maxX:
            return minRate

    def buyTaskPredict(self,workT,dist):
        """
        # 预测此买任务是否可行 条件: 机器人到达目标工作台前能生产产品出来
        :param workT 目标买工作台
        :param dist 机器人到目标买工作台的距离
        """
        if workT['remainTime']>0 and dist/6 > workT['remainTime']*0.02:
            return True
        else:
            return False

    def reservationPredict(self,idx,workT,dist):
        """
        # 预测已被预定产品的买工作台,是否允许重复预定（条件: 能为每个预定的机器人提供产品）
        :param idx 目标买工作台id
        :param workT 目标买工作台
        :param dist 机器人到目标买工作台的距离
        """
        # 查找谁先预定了workT
        for i in range(4):
            if self.robotTargetId[i][0]==idx:
                robot_id = i
        pre_dist = np.linalg.norm([self.robot[robot_id]['x']-workT['x'],self.robot[robot_id]['y']-workT['y']])
        post_dist = dist

        if workT['remainTime'] == 0 :
            return True
        elif workT['productState']==1 and workT['remainTime'] > 0 and post_dist/6 - pre_dist/6 > workT['remainTime']*0.02:
            return True  
        else:
            return False
 
    def isNearest(self,i,workT):
        """
        # 判断i相比于其他机器人是否离workT最近。如果其他机器人对于工作台workT 顺路(或更近), 若有 return False , 否则 True
        :param i 机器人编号
        :param workT 工作台
        """
        # i 与 workT 距离
        i_dist = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])
        for j in range(4):
            j_finish_dist = 1e5
            if i!=j and self.isRobotOccupy[j]==1 and self.robotTaskType[j]==1: # j有任务在身且已经在卖的路上
                # j 卖目标工作台与 workT 距离
                j_finish_dist = np.linalg.norm([self.robotTargetOrid[j][1][0]-workT['x'],self.robotTargetOrid[j][1][1]-workT['y']])
            elif i!=j and self.isRobotOccupy[j]==0: # j没任务在身
                # j 与 workT 距离
                j_finish_dist = np.linalg.norm([self.robot[j]['x']-workT['x'],self.robot[j]['y']-workT['y']])
            # 存在 j 更近
            if i_dist > j_finish_dist:
                return False
        return True

        de
   
    def isMaterialComplete(self,workT):
        """
        # 判断 workT 工作台是否材料齐全了
        """ 
        matrial_type = self.demandTable[workT['type']]
        for i in matrial_type:
            if (workT['rawState']>>i)&1 == 0:
                return False
        return True
  
    def sellTaskPredict(self,idx,workT,buy_dist,sell_dist):
        """
        # 预测此卖任务是否可行 条件: 机器人到达目标工作台前能腾出对应物品格出来
        :param idx 目标卖工作台id
        :param workT 目标卖工作台
        :param buy_dist 机器人到目标买工作台的距离
        :param sell_dist 机器人到目标卖工作台的距离
        """
        # 规定时间 T 即: 某一个机器人从分配任务开始、买到物品、并到达卖工作台的 这段时间
        # 腾出对应物品格的条件: 1,无产品 且 剩余生产时间帧小于规定时间T 且 材料齐备或在小于规定时间内齐备
        #                     2,有产品 且 剩余生产时间帧小于规定时间T 且 取产品时间<规定时间T 且 材料齐备或在小于 [规定时间-取产品时间] 内齐备
        #  (材料在小于规定时间内齐备) 的预测好复杂 T_T ,先放弃 
        
        T = (buy_dist+sell_dist)/6
        getProductTime = 1e5
        for i in range(4):
            if self.robotTaskType[i]==0 and self.robotTargetId[i][0] == idx: # 有机器人正在来买的路上
                getProductTime = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])

        if workT['productState']==0 and workT['remainTime'] > 0 \
        and workT['remainTime']*0.02 < T and self.isMaterialComplete(workT):
            return True
        elif workT['productState']==1 and workT['remainTime'] >= 0 \
        and workT['remainTime']*0.02 < T and getProductTime  < T and self.isMaterialComplete(workT):
            return True
        else:
            return False

    def getBestTask(self,i):
        """
        # 根据场面信息,返回一个较优的任务
        :param i 机器人编号
        """   
        epl = 1e-8 # 很小的数，防止除数为0  
        # 场上的所有需求  #字典项为 物品类型:(格子总数,空缺格子数)
        needType = {1:[epl,0],2:[epl,0],3:[epl,0],4:[epl,0],5:[epl,0],6:[epl,0],7:[epl,0]}  
        # # 同一类型工作台总体对其下原材料的需求  #字典项为 工作台类型:{物品类型:(格子总数,空缺格子数)}
        sameWorkTableNeedType = {4:{1:[epl,0],2:[epl,0]},5:{1:[epl,0],3:[epl,0]},6:{2:[epl,0],3:[epl,0]},7:{4:[epl,0],5:[epl,0],6:[epl,0]}}
        # 此工作台原料完备程度, 工作台id:材料齐备程度
        readyRate = {} 
        ## 信息统计
        for idx,workT in enumerate(self.workTable):   
            readyCount = 0
            for objType in self.demandTable[workT['type']]:
                needType[objType][0] += 1
                if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # 空缺且不被预定
                    needType[objType][1] += 1 

                if workT['type']>=4 and workT['type']<=7:
                    sameWorkTableNeedType[workT['type']][objType][0] += 1
                    if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # 空缺且不被预定
                        sameWorkTableNeedType[workT['type']][objType][1] += 1 
                    else: # 齐备或被预定
                        readyCount += 1

            if workT['type']>=4 and workT['type']<=7:
                readyRate[idx] = readyCount / len(self.demandTable[workT['type']])

                
        # self.info.write(str(self.frameId)+"\n")

        # task 收集
        task = []
        profit = []
        buy_dist = {} # 工作台id:与机器人距离
        sell_dist = {} # 工作台id:与最近需求者距离
        for idx,workT in enumerate(self.workTable): 
            if workT['type'] >= 1 and workT['type'] <= 7:
                ### 统计买的距离              
                buy_dist[idx] = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])
#------可调节----##### 可行的买任务
                if  (self.sw_nearest or self.isNearest(i,workT)) \
                and (workT['productState']==1 or (self.sw_buy_pred and self.buyTaskPredict(workT,buy_dist[idx]))) \
                and (self.wtReservation[idx]['product']==0 or self.wtReservation[idx]['product']==1 and self.reservationPredict(idx,workT,buy_dist[idx])):
                    ### 统计与需求者距离
                    objT = workT['type']
                    for idx2,workT2 in enumerate(self.workTable): 
                        # 如果是一个有效需求者
                        if objT in self.demandTable[workT2['type']]:
                            # 统计卖的距离
                            sell_dist[idx2] = np.linalg.norm([workT['x']-workT2['x'],workT['y']-workT2['y']])
#-------可调节--------------##### 可行的卖任务
                            if ((workT2['rawState']>>objT)&1==0 or (self.sw_sell_pred and self.sellTaskPredict(idx2,workT2,buy_dist[idx],sell_dist[idx2]))) \
                            and (buy_dist[idx]+sell_dist[idx2])/6+1.5 < (9000-self.frameId)*0.02 \
                            and (self.wtReservation[idx2][objT]==0):
                                task.append([idx,idx2])
                                sell_time = sell_dist[idx2]/6
                                total_time = (buy_dist[idx]+sell_dist[idx2])/6
                                # 单位时间收益
                                mps = self.income[objT] * self.f(sell_time*50,9000,0.8) / total_time
                                
                                if workT2['type'] == 9: # 卖给9
                                    productNeed = 1
                                    rawNeed = 1
                                    rawReadyRate = 1
                                elif workT2['type'] == 8: # 卖给8
                                    productNeed = 1
                                    rawNeed = 1
                                    rawReadyRate = 1
                                elif workT2['type'] == 7: # 卖给7
                                    # 其他工作台对此工作台产品的需求度
                                    productNeed = 1         
                                    # 此类型工作台总体对该种原材料的需求度
                                    rawNeed =  sameWorkTableNeedType[7][workT['type']][1] / sameWorkTableNeedType[7][workT['type']][0]
                                    # 此工作台原料完备程度    
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]
                                elif workT2['type'] == 6: # 卖给6
                                    productNeed = needType[6][1] / needType[6][0]
                                    rawNeed = sameWorkTableNeedType[6][workT['type']][1] / sameWorkTableNeedType[6][workT['type']][0]
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]
                                elif workT2['type'] == 5: # 卖给5
                                    productNeed = needType[5][1] / needType[5][0]
                                    rawNeed = sameWorkTableNeedType[5][workT['type']][1] / sameWorkTableNeedType[5][workT['type']][0]
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]
                                elif workT2['type'] == 4: # 卖给4
                                    productNeed = needType[4][1] / needType[4][0]
                                    rawNeed = sameWorkTableNeedType[4][workT['type']][1] / sameWorkTableNeedType[4][workT['type']][0]
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]   

                                score = mps/self.param_mps + productNeed + rawNeed + rawReadyRate
                                # self.info.write("id1:%d,type:%d  id2:%d,type:%d  score = %.3f,%.3f,%.3f,%.3f = %.3f \n" %(idx,workT['type'],idx2,workT2['type'],mps,productNeed,rawNeed,rawReadyRate,score))

                                profit.append(score)
        # task 选择
        if len(task)!=0:
            max_i = np.argmax(np.array(profit))
            return task[max_i]
        else:
            return None

    def judgeAbandon(self,i):
        """
        # 判断是否需要放弃 编号为 i 的机器人目前的任务, 若是,return True, 否则 False
        :param i 机器人编号
        :return bool
        策略: 若有另外的卖任务途中的机器人 j 的目标点是机器人 i 将要前往的买工作台 ,
        且  T(i)/T(j) > self.abandonThreshold 则放弃 i 的任务. 
        T(x) 表示编号为x的机器人到达下个目标点仍需的时间.
        self.abandonThreshold 为可调参数
        时间之比也即距离之比.
        """
        # i 目标工作台坐标(买途中)
        i_target = self.robotTargetOrid[i][0]
        # i 与 其 target 距离
        i_dist = np.linalg.norm([self.robot[i]['x']-i_target[0],self.robot[i]['y']-i_target[1]])

        for j in range(4):
            # j有任务在身且已经在卖的路上且 j 的卖工作台与 i 目标工作台相同
            if i!=j and self.isRobotOccupy[j]==1 and self.robotTaskType[j]==1 \
            and self.robotTargetId[j][1] == self.robotTargetId[i][0]: 
                # j 目标工作台坐标
                j_target = self.robotTargetOrid[i][1]
                # j 与 目标工作台距离
                j_dist = np.linalg.norm([self.robot[j]['x']-j_target[0],self.robot[j]['y']-j_target[1]])
            else:
                j_dist = 1e5

            # 存在 j 顺路, 则 i 可以放弃
            if i_dist / j_dist > self.abandonThreshold:
                return True
        return False

    def scheduleRobot(self):
        """
        # 给空闲机器人分配任务,调度
        """       
        # 任务 = 两个工作台id 分别为 buy 和 sell, 表示机器人要前往对应工作台 , 执行 buy 和 sell  
        self.instr = ''
        for i in range(4):
            # if 空闲
            if self.isRobotOccupy[i] == 0: 
                # 分配任务
                task = self.getBestTask(i)  
                if task!=None: 
                    # 更新机器人调度状态
                    self.robotTargetId[i] = task  # [buy sell]
                    self.isRobotOccupy[i] = 1
                    self.robotTaskType[i] = 0
                    # 买任务坐标
                    self.robotTargetOrid[i][0] = (self.workTable[task[0]]['x'],self.workTable[task[0]]['y'])
                    # 卖任务坐标
                    self.robotTargetOrid[i][1] = (self.workTable[task[1]]['x'],self.workTable[task[1]]['y'])
                    # 更新工作台预定表
                    self.wtReservation[task[0]]['product'] = 1
                    if self.workTable[task[1]]['type']==8 or self.workTable[task[1]]['type']==9: # 不需预定，一直可卖
                        self.wtReservation[task[1]][self.workTable[task[0]]['type']] = 0
                    else:
                        self.wtReservation[task[1]][self.workTable[task[0]]['type']] = 1
                else: # 没任务可分配
#----可调节---------##### # 往地图中心走 (往某个工作台走？)
                    self.instr += self.control(i,(25,25))
                    
            # 买占用状态
            elif self.isRobotOccupy[i] == 1 and self.robotTaskType[i] == 0 : 
                # 未到达买目标点
                if self.robot[i]['workTableID'] != self.robotTargetId[i][0]:
                    # 若有另外的卖任务途中的机器人 j 的目标点是机器人 i 将要前往的买工作台 ,
 #---可调节----------##### # 且  T(i)/T(j) > 阈值 则放弃 i 的任务。 T(x) 表示编号为x的机器人到达下个目标点仍需的时间
                    if self.sw_abandon and self.judgeAbandon(i):
                        # 放弃此任务
                        # 机器人转为空闲
                        self.isRobotOccupy[i] = 0
                        # 更新工作台预定表
                        self.wtReservation[self.robotTargetId[i][0]]['product'] = 0 # 取消买预定
                        objT = self.workTable[self.robotTargetId[i][0]]['type']
                        self.wtReservation[self.robotTargetId[i][1]][objT] = 0 # 取消卖预定
                    else:
                        self.instr += self.control(i,self.robotTargetOrid[i][0])
                # 到达目标点
                else:
                    # 买
                    self.instr += 'buy %d\n' % (i)
                    # 机器人任务类型从 买 转为 卖
                    self.robotTaskType[i] = 1
                    # 更新工作台预定表
                    self.wtReservation[self.robotTargetId[i][0]]['product'] = 0

            # 卖占用状态
            elif self.isRobotOccupy[i] == 1 and self.robotTaskType[i] == 1:
                # 未到达卖目标点
                if self.robot[i]['workTableID'] != self.robotTargetId[i][1]:
                    self.instr += self.control(i,self.robotTargetOrid[i][1])
                # 到达目标点
                else: 
                    # 卖
                    self.instr += 'sell %d\n' % (i)
                    # 机器人转为空闲
                    self.isRobotOccupy[i] = 0
                    # 更新工作台预定表
                    self.wtReservation[self.robotTargetId[i][1]][self.robot[i]['type']] = 0
        if self.sw_avoidCrash == 1:
            self.avoidCrash()
    
    def avoidCrash(self):
        """碰撞避免"""
        turn=[0 for i in range(4)]
        for i in range(3):
            for j in range(i + 1, 4):
                if pow(self.robot[i]['x']-self.robot[j]['x'],2)+pow(self.robot[i]['y']-self.robot[j]['y'],2)<2.9**2.9 and\
                        self.robot[i]['orientation']*self.robot[j]['orientation']<=0:
                    k1=0
                    k2=0
                    if(self.robot[i]['orientation']!=-math.pi/2 and self.robot[i]['orientation']!=math.pi/2 ):
                        k1 = math.tan(self.robot[i]['orientation'])
                    if (self.robot[j]['orientation'] != -math.pi / 2 and self.robot[j]['orientation'] != math.pi / 2):
                        k2 = math.tan(self.robot[j]['orientation'])

                    b1=self.robot[i]['y']-k1*self.robot[i]['x']
                    b2=self.robot[j]['y']-k2*self.robot[j]['x']
                    #交点
                    t1=0
                    t2=0
                    if k1!=k2 and self.robot[i]['orientation']!=-math.pi/2 and self.robot[i]['orientation']!=math.pi/2 and self.robot[j]['orientation']!=-math.pi/2and self.robot[j]['orientation']!=math.pi/2:
                        x_0=(b2-b1)/(k1-k2)
                        y_0=x_0*k1+b1
                        if(x_0-self.robot[i]['x'])*math.cos(self.robot[i]['orientation'])>0 and(y_0-self.robot[i]['y'])*math.sin(self.robot[i]['orientation'])>0:
                            t1=np.linalg.norm(np.array([self.robot[i]['x']-x_0, self.robot[i]['y']-y_0]))/0.12 #当前位置到相撞的点的距离处于每一帧最高速度运行的距离
                        if ( x_0-self.robot[j]['x'] ) * math.cos(self.robot[j]['orientation'])>0 and ( y_0-self.robot[j]['y']) * math.sin(
                                self.robot[j]['orientation']) > 0:
                            t2 = np.linalg.norm(np.array([self.robot[j]['x'] - x_0, self.robot[j]['y'] - y_0]))/0.12
                    #self.info.write("t1-t2: " + str(t1-t2)+'\n'+str(self.turning[j])+'\n')
                    if(abs(t1-t2)>30 and self.turning[j]==0):
                        continue
                    if  self.turning[j]>=1 or abs(t1-t2)<=30 or self.robot[i]['orientation']==-math.pi/2 or self.robot[i]['orientation']==math.pi/2 or self.robot[j]['orientation']==-math.pi/2 or self.robot[j]['orientation']==math.pi/2:
                        #if turn[j]==0 and  (pow(self.robot[j]['linV_x'],2)+pow(self.robot[j]['linV_y'],2)) >=16 or (pow(self.robot[i]['linV_x'],2)+pow(self.robot[i]['linV_y'],2)) >=9:
                        if turn[j] == 0:
                            if (self.turning[j] == 0):
                                self.turning[j] = 30
                            if abs(self.robot[j]['orientation']+self.robot[i]['orientation'])<math.pi/36 and  abs(self.robot[j]['x']-self.robot[i]['x'])>1.6:
                                continue #避免两个小球运动方向相反但是绝对不可能不可能相撞导致误判为碰撞避免而耽误时间
                            if self.robot[j]['orientation']<0 and self.robot[j]['y']>self.robot[i]['y'] and self.robot[j]['x']>self.robot[i]['x']:
                                turn[j] = math.pi
                            if self.robot[j]['orientation']<=0 and self.robot[j]['y']>self.robot[i]['y'] and self.robot[j]['x']<=self.robot[i]['x']:
                                turn[j] = -math.pi
                            if self.robot[j]['orientation']>0 and self.robot[j]['y']<self.robot[i]['y'] and self.robot[j]['x']>self.robot[i]['x']:
                                turn[j] = -math.pi
                            if self.robot[j]['orientation']>=0 and self.robot[j]['y']<self.robot[i]['y'] and self.robot[j]['x']<=self.robot[i]['x']:
                                turn[j] = math.pi
                            self.turning[j]-=1
        # 角速度
        for i in range(4):
            if turn[i]!=0:
                instr_i = 'rotate %d %f\n' % (i,turn[i])
                self.instr += instr_i

    def control(self,i,target):
        """
        # 移动控制
        :param i 机器人编号
        :param target 目标点坐标
        """
        instr_i = ''

        a = self.robot[i]['orientation'] # 朝向角
        vector_a = np.array([math.cos(a),math.sin(a)]) # 机器人朝向 
        x_bar = target[0] - self.robot[i]['x']
        y_bar = target[1] - self.robot[i]['y']
        vector_b = np.array([x_bar,y_bar]) # 机器人当前位置指向目标点的 
        dist_a = np.linalg.norm(vector_a)
        dist_b = np.linalg.norm(vector_b) # 机器人与目标点的距离

        dot = np.dot(vector_a,vector_b)     # 点积
        cross = np.cross(vector_a,vector_b) # 叉积

        cos_theta = dot/(dist_a*dist_b) # 向量a转到b的转向角余弦值 
        theta = math.acos(round(cos_theta,10)) # a -> b 转  
        if cross < 0: # 应该顺时针转
            theta = -theta
        else: # 逆时针转
            theta = theta

        '''
        持有物品：质量为0.88247 kg
        最大加速度：283.295 m/s*s (5.6659 m/s*frame)
        最大角加速度：403.4115 pi/s*s (8.06823 pi/s*fram    
        不持有物品：质量为0.63617 kg
        最大加速度：392.976 m/s*s (7.85952 m/s*frame)
        最大角加速度：776.2503 pi/s*s (15.525 pi/s*frame)
        '''
        # 角速度
        angle_v = min(theta/0.02, math.pi) if theta>0 else max(theta/0.02, -math.pi)
        instr_i += 'rotate %d %f\n' % (i,angle_v)

        #速度
        x = self.robot[i]['x']
        y = self.robot[i]['y']
        
        # 左
        if x<2 and y<48 and y>2 and ((a>=-math.pi and a<-math.pi/2) or (a>math.pi/2 and a<=math.pi)):
            v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
        # 右
        elif x>48 and y<48 and y>2 and a>-math.pi/2 and a<math.pi/2:
            v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
        # 上
        elif x>2 and x<48 and y>48 and a>0 and a<math.pi:
            if a<=math.pi/2:
                v = 6/(a*10/math.pi+1)
            else:
                v = 6/((math.pi-a)*10/math.pi+1)
        # 下
        elif x>2 and x<48 and y<2 and a>-math.pi and a<0:
            if a>=-math.pi/2:
                v = 6/(-a*10/math.pi+1)
            else:
                v = 6/((math.pi+a)*10/math.pi+1)
        # 左上
        elif x<=2 and y>=48 and ((a>=-math.pi and a<-math.pi/2) or (a>0 and a<=math.pi)):
            if a>0 and a<=math.pi/2:
                v = 6/(a*10/math.pi+1)
            elif a>=math.pi and a<-math.pi/2:
                v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
            elif a>math.pi/2 and a<=3*math.pi/4:
                v = 6/((a-math.pi/2)*24/math.pi+6)
            else:
                v = 6/((math.pi-a)*24/math.pi+6)
        # 左下
        elif x<=2 and y<=2 and ((a>=-math.pi and a<0) or (a>math.pi/2 and a<=math.pi)):
            if a>=-math.pi/2 and a<0:
                v = 6/(-a*10/math.pi+1)
            elif a>math.pi/2 and a<=math.pi:
                v = v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
            elif a>=-3*math.pi/4 and a<-math.pi/2:
                v = 6/(abs(a+math.pi/2)*24/math.pi+6)
            else:
                v = 6/(abs(a+math.pi)*24/math.pi+6)
        # 右上
        elif x>=48 and y>=48 and a>-math.pi/2 and a<math.pi:
            if a>=math.pi/2:
                v = 6/((math.pi-a)*10/math.pi+1)
            elif a<=0:
                v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
            elif a>0 and a<=math.pi/4:
                v = 6/(a*24/math.pi+6)
            else:
                v = 6/(abs(a-math.pi/2)*24/math.pi+6)
        # 右下
        elif x>=48 and y<=2 and a>-math.pi and a<math.pi/2:
            if a<=-math.pi/2:
                v = 6/((math.pi+a)*10/math.pi+1)
            elif a>=0:
                v = 6/(abs(a-math.pi/2)*10/math.pi+1)
            elif a>=-math.pi/4 and a<0:
                v = 6/(-a*24/math.pi+6)
            else:
                v = 6/(abs(math.pi/2+a)*24/math.pi+6)
        elif self.sw_avoidCrash and dist_b<1:
            v = 1
        else:
            v = 6/(abs(theta)+1)

        instr_i += 'forward %d %f\n' % (i,v)

        return instr_i

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
            # if 1:
            #     robot_ordin = []
            #     self.info.write("时间帧："+str(self.frameId)+"\n")
            #     self.info.write("工作台："+str(self.workTable)+"\n")
            #     for i in range(4):
            #         self.info.write("机器人："+str(self.robot[i])+"\n")
            #         robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
            #     self.info.write("指令：\n"+str(self.instr))
            #     self.info.write("是否占用      :"+str(self.isRobotOccupy)+"\n")
            #     self.info.write("目标工作台ID  :"+str(self.robotTargetId)+"\n")
            #     self.info.write("目标工作台坐标 :"+str(self.robotTargetOrid)+"\n")
            #     self.info.write("机器人坐标    :"+str(robot_ordin)+"\n")
            #     self.info.write("机器人任务类型 :"+str(self.robotTaskType)+"\n")
            #     self.info.write("\n")
                  
        # 关闭日志文件
        # self.info.close()


if __name__ == '__main__':
    
    solver = Solution()
    solver.run()
    
