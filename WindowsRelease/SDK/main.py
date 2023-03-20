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

    def getBestTask(self,i):
        """
        # 根据场面信息,返回一个较优的任务
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
                if workT['productState']==1 or (workT['remainTime']>0 and buy_dist[idx]/6 > workT['remainTime']*0.02):
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
                    pass

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
            else: # 空闲状态
                pass

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
    
