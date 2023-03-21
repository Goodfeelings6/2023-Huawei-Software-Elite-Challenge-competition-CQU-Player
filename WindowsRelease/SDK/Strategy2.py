import numpy as np
import math

# 策略类 地图2
class Strategy2(object):
    def __init__(self,_destoryTime,_demandTable,_wtReservation) -> None:  
       
        # 销毁时间 s (持续占用时间达到销毁时间时就销毁)
        self.destoryTime = _destoryTime
        # 固定信息 ：需求表,即每种工作台需要的物品(原材料或成品)类型
        self.demandTable = _demandTable
        # 工作台预定表
        self.wtReservation = _wtReservation
        
        # 机器人调度控制
        self.isRobotOccupy = [0 for i in range(4)] # 标识机器人是否占用,1占用,0空闲
        self.robotTargetId = [[0,0] for i in range(4)]   # 被占用机器人需要前往的目标工作台id(仅当 isRobotOccupy[i]==1 时i位置数据有效)
        self.robotTargetOrid = [[(0,0),(0,0)] for i in range(4)] # 被占用机器人需要前往的目标工作台坐标
        self.robotTaskType = [0 for i in range(4)] # 被占用机器人目前的任务类型,只考虑buy和sell,0表示buy,1表示sell
       
       
        # 固定信息 ：物品净利润
        self.income = {1:3000,2:3200,3:3400,4:7100,5:7800,6:8300,7:29000}

        # 参数
        #------
    
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

    def f(self,x,maxX,minRate):
        """
        # 贬值率计算公式
        """
        if x < maxX:
            return (1-math.sqrt(1-(1-x/maxX)**2))*(1-minRate)+minRate
        elif x >= maxX:
            return minRate

    def isNearest(self,i,workT):
        """
        # 判断 是否有其他机器人顺路
        :param i 机器人编号
        :param workT 工作台
        """
        # i 与 workT 距离
        i_dist = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])
        ans = True
        for j in range(4):
            j_finish_dist = 1e5
            if i!=j and self.isRobotOccupy[j]==1 and self.robotTaskType[j]==1: # j有任务在身
                # j 卖目标工作台与 workT 距离
                j_finish_dist = np.linalg.norm([self.robotTargetOrid[j][1][0]-workT['x'],self.robotTargetOrid[j][1][1]-workT['y']])
            elif i!=j and self.isRobotOccupy[j]==0: # j没任务在身
                j_finish_dist = np.linalg.norm([self.robot[j]['x']-workT['x'],self.robot[j]['y']-workT['y']])
            if i_dist > j_finish_dist:
                return False
        return True

    def getBestTask(self,i):
        """
        # 根据场面信息,返回一个较优的任务
        :param i 机器人编号
        """     
        task = []
        profit = []
        buy_dist = {} # 工作台id:与机器人距离
        sell_dist = {} # 工作台id:与最近需求者距离
        for idx,workT in enumerate(self.workTable): 
            if workT['type'] >= 1 and workT['type'] <= 7 and self.wtReservation[idx]['product']==0:
                ### 统计买的距离              
                buy_dist[idx] = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])
                # 可行的买任务
                if self.isNearest(i,workT) and (workT['productState']==1 or (workT['remainTime']>0 and buy_dist[idx]/6 > workT['remainTime']*0.02)):
                    ### 统计与需求者距离
                    objT = workT['type']
                    for idx2,workT2 in enumerate(self.workTable): 
                        # 如果是一个有效需求者
                        if objT in self.demandTable[workT2['type']] and self.wtReservation[idx2][objT]==0:
                            # 统计卖的距离
                            sell_dist[idx2] = np.linalg.norm([workT['x']-workT2['x'],workT['y']-workT2['y']])
                            # 可行的卖任务
                            if (workT2['rawState']>>objT)&1==0 and (buy_dist[idx]+sell_dist[idx2])/6+1.5 < (9000-self.frameId)*0.02 \
                            or (0) :
                                task.append([idx,idx2])
                                sell_time = sell_dist[idx2]/6
                                total_time = (buy_dist[idx]+sell_dist[idx2])/6
                                mps = self.income[objT] * self.f(sell_time*50,9000,0.8) / total_time
                                profit.append(mps)
        # task 选择
        if len(task)!=0:
            max_i = np.argmax(np.array(profit))
            return task[max_i]
        else:
            return None

    def scheduleRobot(self):
        """
        # 给空闲机器人分配任务,调度
        ##### 策略：未携带物品的空闲机器人 分配 buy任务, 携带物品的空闲机器人 分配 sell任务 
        """       
        # 任务 = 一个工作台id , 表示机器人要前往此工作台 , 执行 buy 或 sell  
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
                    # 往地图中心走
                    self.instr += self.control(i,(25,25))
                    
            # 买占用状态
            elif self.isRobotOccupy[i] == 1 and self.robotTaskType[i] == 0 : 
                # 未到达买目标点
                if self.robot[i]['workTableID'] != self.robotTargetId[i][0]:
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
        else:
            v = 6/(abs(theta)+1)
        v = min(v, 6) if v>0 else max(v, -2)

        instr_i += 'forward %d %f\n' % (i,v)

        return instr_i

    def run(self):
        self.scheduleRobot()
