import numpy as np
import math

# 策略类 地图3
class Strategy3(object):
    def __init__(self,_destoryTime,_demandTable,_wtReservation) -> None:  
       
        # 销毁时间 s (持续占用时间达到销毁时间时就销毁)
        self.destoryTime = _destoryTime
        # 固定信息 ：需求表,即每种工作台需要的物品(原材料或成品)类型
        self.demandTable = _demandTable
        # 工作台预定表
        self.wtReservation = _wtReservation
        
        # 机器人调度控制
        self.isRobotOccupy = [0 for i in range(4)] # 标识机器人是否占用,1占用,0空闲
        self.robotTargetId = [0 for i in range(4)]   # 被占用机器人需要前往的目标工作台id(仅当 isRobotOccupy[i]==1 时i位置数据有效)
        self.robotTargetOrid = [(0,0) for i in range(4)] # 被占用机器人需要前往的目标工作台坐标
        self.robotTaskType = [0 for i in range(4)] # 被占用机器人目前的任务类型,只考虑buy和sell,0表示buy,1表示sell
        self.robotObjOccupyTime = [0 for i in range(4)] # 机器人的已持续持有物品时间
       
        # 参数
        self.param_need = 0.064516
        self.param_buy_dist = 1.000000
        self.param_need_dist = 0.064516
        self.param_haveProduct = 0.612903
        self.param_produce = 0.774194
        self.param_lackRate = 0.000000
        self.param_sell_dist = 0.193548
    
    def getMessage(self,_workTable,_robot,_frameId):
        """
        获取数据
        :param _workTable 工作台数据
        :param _robot 机器人数据
        :param _frameId 当前时间帧
        """
        # 工作台数据
        self.workTable = _workTable
        # 机器人数据
        self.robot = _robot
        # 当前时间帧
        self.frameId = _frameId
    
    def sentMessage(self):
        """
        # 发送数据(指令)给 Solution 类
        """
        return self.instr

    def buyCmp(self,x,robot_id,needType,buy_dist,need_dist):
        _need =  needType[self.workTable[x]['type']][1]/needType[self.workTable[x]['type']][0]
        _buy_dist = buy_dist[x]
        _need_dist = need_dist[x]

        return self.param_need * _need + self.param_buy_dist * 1/_buy_dist + self.param_need_dist * 1/_need_dist

    def getBestBuyTask(self,robot_id):
        """
        # 根据场面信息,返回一个较优的买任务
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
        for idx,workT in enumerate(self.workTable):
            # 能买的条件,进行过滤           
            if workT['type'] >= 1 and workT['type'] <= 7 and workT['productState']==1 \
              and self.wtReservation[idx]['product']==0 and needType[workT['type']][1]!=0:
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
        # buy task 收集
        buyTask = [] # 工作台id
        for idx,workT in enumerate(self.workTable):
            # 能买的条件,进行过滤           
            if workT['type'] >= 1 and workT['type'] <= 7 and workT['productState']==1 \
              and self.wtReservation[idx]['product']==0 and needType[workT['type']][1]!=0 \
              and (buy_dist[idx]+need_dist[idx])/6+1.5 < (9000-self.frameId)*0.02:
                buyTask.append(idx) 
        # buy task 排序
        buyTask.sort(key=lambda x : self.buyCmp(x,robot_id,needType,buy_dist,need_dist), reverse=True)   

        # buy task 选择
        if len(buyTask)!=0:
            return buyTask[0]
        else:
            return None

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

        # sell task 排序
        sellTask.sort(key=lambda x : self.sellCmp(x,robot_id), reverse=True)

        # sell task 选择
        if len(sellTask)!=0:
            return sellTask[0]
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
                    task = self.getBestBuyTask(i)
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
        need_down_speed = [0 for i in range(4)]  # 负数表示减速，正数表示加数，第五个位置置空位

        turn=[0 for i in range(4)]
        for i in range(3):
            for j in range(i + 1, 4):
                if pow(self.robot[i]['x']-self.robot[j]['x'],2)+pow(self.robot[i]['y']-self.robot[j]['y'],2)<3**3and self.robot[i]['orientation']*self.robot[j]['orientation']<0:
                    """if turn[j]==0 and ((self.robot[j]['orientation']>-math.pi/2 and self.robot[j]['orientation']<0)or (self.robot[j]['orientation']>math.pi/2 and self.robot[j]['orientation']<math.pi))  :
                        turn[j]=-math.pi
                    if turn[j]==0 and ((self.robot[j]['orientation']<-math.pi/2 and self.robot[j]['orientation']>-math.pi)or (self.robot[j]['orientation']<math.pi/2 and self.robot[j]['orientation']>0))  :
                        turn[j]=math.pi"""
                    if(turn[j]==0):
                        if(pow(self.robot[j]['linV_x'],2)+pow(self.robot[j]['linV_y'],2))>9:
                            if self.robot[j]['orientation']<0 and self.robot[j]['y']>self.robot[i]['y'] and self.robot[j]['x']>self.robot[i]['x']:
                                turn[j] = math.pi
                            if self.robot[j]['orientation']<0 and self.robot[j]['y']>self.robot[i]['y'] and self.robot[j]['x']<=self.robot[i]['x']:
                                turn[j] = -math.pi
                            if self.robot[j]['orientation']>0 and self.robot[j]['y']<self.robot[i]['y'] and self.robot[j]['x']>self.robot[i]['x']:
                                turn[j] = -math.pi
                            if self.robot[j]['orientation']<0 and self.robot[j]['y']<self.robot[i]['y'] and self.robot[j]['x']<=self.robot[i]['x']:
                                turn[j] = math.pi

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
                angle_v = min(theta / 0.02, math.pi) if theta > 0 else max(theta / 0.02, -math.pi)
                
                # 速度
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
                elif dist_b<1:
                    v=1
                else:
                    v = 6/(abs(theta)+1)
                v = min(v, 6) if v>0 else max(v, -2)
                v += need_down_speed[i]

                self.instr = self.instr + 'forward %d %f\n' % (i,v)
                if turn[i]!=0:
                    angle_v=turn[i]
                # 角速度
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
        self.scheduleRobot()
        self.getInstrAndUpdate()
