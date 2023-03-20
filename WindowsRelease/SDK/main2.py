#!/bin/bash
# coding=GB2312
import sys
import numpy as np
import math

# ����,���������룺
# Ĭ�ϵ���ģʽ(ʹ����ʵʱ��)  ./robot -m maps/1.txt -c ./SDK "python main.py"
# ����ģʽ(ʹ�ó���ʱ��)     ./robot -m maps/1.txt -c ./SDK -f "python main.py"
# Ĭ�ϵ���ģʽʹ��gui        ./robot_gui -m maps/1.txt -c ./SDK "python main.py"
# ����ȫ����ͼ��ͳ�ƽ��      ./run_all

class Solution(object):
    def __init__(self) -> None:       
        # ��ͼ����
        self.map = []
        # ��ͼ����̨��������ͳ��
        self.wtTypeNum = [0 for i in range(0,10)]
        # ����̨����
        self.workTable = []
        # ����������
        self.robot = []
        # ��ǰʱ��֡
        self.frameId = 0
        # ��ǰ��Ǯ��
        self.money = 0
        # ��ǰ����ָ��
        self.instr = ''
        # ����ʱ�� s (����ռ��ʱ��ﵽ����ʱ��ʱ������)
        self.destoryTime = 20

        # �̶���Ϣ �������,��ÿ�ֹ���̨��Ҫ����Ʒ(ԭ���ϻ��Ʒ)����
        self.demandTable = {1:[],2:[],3:[],4:[1,2],5:[1,3],6:[2,3],7:[4,5,6],8:[7],9:[1,2,3,4,5,6,7]} 

        # �����˵��ȿ���
        self.isRobotOccupy = [0 for i in range(4)] # ��ʶ�������Ƿ�ռ��,1ռ��,0����
        self.robotTargetId = [0 for i in range(4)]   # ��ռ�û�������Ҫǰ����Ŀ�깤��̨id(���� isRobotOccupy[i]==1 ʱiλ��������Ч)
        self.robotTargetOrid = [(0,0) for i in range(4)] # ��ռ�û�������Ҫǰ����Ŀ�깤��̨����
        self.robotTargetScore = [0 for i in range(4)] # ������Ŀǰִ������Ĵ��
        self.robotTaskType = [0 for i in range(4)] # ��ռ�û�����Ŀǰ����������,ֻ����buy��sell,0��ʾbuy,1��ʾsell
        self.robotObjOccupyTime = [0 for i in range(4)] # �����˵��ѳ���������Ʒʱ��

        # ����̨Ԥ����(�����ͼʱ˳���ʼ��,��Ԥ����Ʒ����Ʒ��, 0δ��Ԥ����1��Ԥ��)
        self.wtReservation = []
        # self.param_need = 0.01
        # self.param_buy_dist = 1
        # self.param_need_dist = 0
        # self.param_haveProduct = 0
        # self.param_produce = 0
        # self.param_lackRate = 1
        # self.param_sell_dist = 0.5
        # ����
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
        # ---��־---
        # self.info = open('info.txt', 'w')

    def finish(self):
        """
        # ��� 'OK', ��ʾ��ǰ֡������
        """
        sys.stdout.write('OK\n')
        sys.stdout.flush()

    def initMap(self):
        """
        # ��ʼ����ͼ
        """ 
        inputLine = sys.stdin.readline()
        while inputLine.strip() != 'OK':
            # д���ͼ
            self.map.append(inputLine)
            # ��ʼ��һЩ����
            for char in inputLine:
                if char.isdigit(): # ��һ������̨
                    self.wtTypeNum[int(char)] += 1
                    dic = {}
                    dic['product'] = 0
                    for i in self.demandTable[int(char)]:
                        dic[i] = 0
                    self.wtReservation.append(dic)
                    
            # ������ȡ
            inputLine = sys.stdin.readline()
        # ʶ���ͼ,�趨����
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
        # �����,��� 'OK', �����������Ѿ���
        self.finish()


    def inputData(self):
        """
        # ��ȡ�����������ĳ�������
        """
        end = False
        # ����һ��
        inputLine = sys.stdin.readline()
        if not inputLine: # ������EOF
            end = True
            return end
        parts = inputLine.split(' ')
        self.frameId = int(parts[0])
        self.money = int(parts[1])
        
        # ���ڶ���
        inputLine = sys.stdin.readline()
        workTableNum = int(inputLine)
        
        # ������̨����,ÿһ����һ������̨����
        self.workTable = []
        for i in range(workTableNum):
            singleWorkTable = dict()
            inputLine = sys.stdin.readline()
            parts = inputLine.split(' ')

            singleWorkTable['type'] = int(parts[0]) # ����̨���� 
            singleWorkTable['x'] = float(parts[1])  # ����̨����x
            singleWorkTable['y'] = float(parts[2])  # ����̨����y
            singleWorkTable['remainTime'] = int(parts[3])   # ʣ������ʱ��(֡��)
            singleWorkTable['rawState'] = int(parts[4])     # ԭ���ϸ�״̬
            singleWorkTable['productState'] = int(parts[5]) # ��Ʒ��״̬

            self.workTable.append(singleWorkTable)

        # ������������,��4��,ÿһ����һ������������
        self.robot = []
        for i in range(4):
            singleRobot = dict()
            inputLine = sys.stdin.readline()
            parts = inputLine.split(' ')

            singleRobot['workTableID'] = int(parts[0])     # ��������̨ ID
            singleRobot['type'] = int(parts[1])            # Я����Ʒ����
            singleRobot['timeRate'] = float(parts[2])      # ʱ���ֵϵ��
            singleRobot['collisionRate'] = float(parts[3]) # ��ײ��ֵϵ��
            singleRobot['angV'] = float(parts[4])          # ���ٶ�
            singleRobot['linV_x'] = float(parts[5])        # ���ٶ�x
            singleRobot['linV_y'] = float(parts[6])        # ���ٶ�y
            singleRobot['orientation'] = float(parts[7])   # ����
            singleRobot['x'] = float(parts[8])             # ����������x
            singleRobot['y'] = float(parts[9])             # ����������y

            self.robot.append(singleRobot)
        
        # ��ȡ�������� 'OK'
        sys.stdin.readline()
        
        return end

    def outputData(self):
        """
        # ��������˵Ŀ�������
        """
        # ��һ�����֡ID
        sys.stdout.write('%d\n' % self.frameId)
        # ����
        self.scheduleRobot()
        # ���ߺ͸���
        instr = self.getInstrAndUpdate()
        # ��������˿���ָ��
        sys.stdout.write(instr)
        
        # ���������,��� 'OK'
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
        # ���ݳ�����Ϣ,����һ�����ŵ������������
        ##### buy:
        ##### ��ѡ��������: ����̨����1-7,��Ӧ����Ʒ����1-7 and ��Ʒ��Ϊ��(==1) and ��Ʒδ������������Ԥ��
        """
        ### ͳ�Ƴ��ϵ����� 
        epl = 1e-8
        needType = {1:[epl,0],2:[epl,0],3:[epl,0],4:[epl,0],5:[epl,0],6:[epl,0],7:[epl,0]}  # ��Ʒ����:(��������,��ȱ������)
        for idx,workT in enumerate(self.workTable):   
            for objType in self.demandTable[workT['type']]:
                needType[objType][0] += 1
                if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # ��ȱ�Ҳ���Ԥ��
                    needType[objType][1] += 1 

        
        buy_dist = {} # ����̨id:������˾���
        need_dist = {} # ����̨id:����������߾���
        remainTime = {} # ����̨ʣ������ʱ��֡
        for idx,workT in enumerate(self.workTable):
            # ���������,���й���           
            if workT['type'] >= 1 and workT['type'] <= 7 and self.wtReservation[idx]['product']==0 and needType[workT['type']][1]!=0:
                if workT['productState']==1 or workT['remainTime']>0: # �г�Ʒ ������������
                    ### ͳ����ľ���              
                    buy_dist[idx] = np.linalg.norm([self.robot[robot_id]['x']-self.workTable[idx]['x'],self.robot[robot_id]['y']-self.workTable[idx]['y']])
                    ### ͳ������������߾���
                    objT = workT['type']
                    for idx2,workT2 in enumerate(self.workTable): 
                        # �����һ����Ч������
                        if objT in self.demandTable[workT2['type']] and (workT2['rawState']>>objT)&1==0 and self.wtReservation[idx2][objT]==0:
                            # ά����С����
                            tmp_dist = np.linalg.norm([workT['x']-workT2['x'],workT['y']-workT2['y']])
                            if idx not in need_dist.keys() or tmp_dist < need_dist[idx]:
                                need_dist[idx] = tmp_dist
                    remainTime[idx] = workT['remainTime']
        # buy task �ռ�
        buyTask = [] # ����̨id
        for idx,workT in enumerate(self.workTable):
            # ���������,���й���           
            if workT['type'] >= 1 and workT['type'] <= 7 and self.wtReservation[idx]['product']==0 and needType[workT['type']][1]!=0 \
                and (workT['productState']==1 or workT['remainTime']>0 )\
                and (buy_dist[idx]+need_dist[idx])/6+1.5 < (9000-self.frameId)*0.02:
                buyTask.append(idx) 
        # buy task ����
        buyTask.sort(key=lambda x : self.buyCmp(x,robot_id,needType,buy_dist,need_dist,remainTime), reverse=True)   

        # buy task ѡ��
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
            if (self.workTable[x]['rawState']>>objType)&1==0 : # ȱ��
                lack_count += 1
        _lackRate = (total_count-lack_count) / total_count
        
        _sell_dist = np.linalg.norm([self.robot[robot_id]['x']-self.workTable[x]['x'],self.robot[robot_id]['y']-self.workTable[x]['y']])

        return  self.param_haveProduct * _haveProduct + self.param_produce * _produce + self.param_lackRate * _lackRate + self.param_sell_dist * 1/_sell_dist

    def getBestSellTask(self,robot_id):
        """
        # ���ݳ�����Ϣ,����һ�����ŵ������������
        :param robot_id: ������������Ļ�����id
        ## �̶���Ϣ
        ##### ����̨����4 : ����Ʒ����1,2       ��������Ӧ��Ʒ�������λ==0 and ��Ӧ��Ʒ��δ������������Ԥ��
        ##### ����̨����5 : ����Ʒ����1,3       ��������Ӧ��Ʒ�������λ==0 and ��Ӧ��Ʒ��δ������������Ԥ��
        ##### ����̨����6 : ����Ʒ����2,3       ��������Ӧ��Ʒ�������λ==0 and ��Ӧ��Ʒ��δ������������Ԥ��
        ##### ����̨����7 : ����Ʒ����4,5,6     ��������Ӧ��Ʒ�������λ==0 and ��Ӧ��Ʒ��δ������������Ԥ��
        ##### ����̨����8 : ����Ʒ����7         ��������
        ##### ����̨����9 : ����Ʒ����1-7       ��������
        �������£�
        ##### sell:
        ##### ����Ʒ����1, ������((����̨����==4 or ����̨����==5) and ����1��Ʒ��Ϊ��(==0) and ����1��Ʒ��δ������������Ԥ��) or ����̨����==9
        ##### ����Ʒ����2, ������((����̨����==4 or ����̨����==6) and ����2��Ʒ��Ϊ��(==0) and ����2��Ʒ��δ������������Ԥ��) or ����̨����==9 
        ##### ����Ʒ����3, ������((����̨����==5 or ����̨����==6) and ����3��Ʒ��Ϊ��(==0) and ����3��Ʒ��δ������������Ԥ��) or ����̨����==9
        ##### ����Ʒ����4, ������( ����̨����==7 and ����4��Ʒ��Ϊ��(==0) and ����4��Ʒ��δ������������Ԥ��) or ����̨����==9
        ##### ����Ʒ����5, ������( ����̨����==7 and ����5��Ʒ��Ϊ��(==0) and ����5��Ʒ��δ������������Ԥ��) or ����̨����==9
        ##### ����Ʒ����6, ������( ����̨����==7 and ����6��Ʒ��Ϊ��(==0) and ����6��Ʒ��δ������������Ԥ��) or ����̨����==9
        ##### ����Ʒ����7, ����������̨����==8 or ����̨����==9
        """
        # sell task �ռ�
        sellTask = [] 
        # ��Ʒ����
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

        # sell task ����
        sellTask.sort(key=lambda x : self.sellCmp(x,robot_id), reverse=True)

        # sell task ѡ��
        if len(sellTask)!=0:
            score = self.sellCmp(sellTask[0],robot_id)
            return sellTask[0], score
        else:
            return None,None

    def scheduleRobot(self):
        """
        # �����л����˷�������,����
        ##### ���ԣ�δЯ����Ʒ�Ŀ��л����� ���� buy����, Я����Ʒ�Ŀ��л����� ���� sell���� 
        """       
        # ���� = һ������̨id , ��ʾ������Ҫǰ���˹���̨ , ִ�� buy �� sell  

        # �������������л�����
        for i in range(4):
            if self.isRobotOccupy[i] == 0: # if ����
                # ����buy����
                if self.robot[i]['type'] == 0:
                    task,score = self.getBestBuyTask(i)
                    if task!=None: 
                        # ���»����˵���״̬
                        self.robotTargetId[i] = task 
                        self.robotTargetScore[i] = score
                        self.isRobotOccupy[i] = 1
                        self.robotTaskType[i] = 0
                        self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                        # ���¹���̨Ԥ����
                        self.wtReservation[task]['product'] = 1
                    else: # ûbuy����ɷ���
                        pass
                # ����sell����
                elif self.robot[i]['type'] != 0:
                    task,score = self.getBestSellTask(i)
                    if task!=None: 
                        # ���»����˵���״̬
                        self.robotTargetId[i] = task 
                        self.robotTargetScore[i] = score
                        self.isRobotOccupy[i] = 1
                        self.robotTaskType[i] = 1
                        self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
                        # ���¹���̨Ԥ����
                        if self.workTable[task]['type']==8 or self.workTable[task]['type']==9: # ����Ԥ����һֱ����
                            self.wtReservation[task][self.robot[i]['type']] = 0
                        else:
                            self.wtReservation[task][self.robot[i]['type']] = 1
                    else: # ûsell����ɷ���
                        pass
                # ������
                else:  
                    pass

            # ��ռ�õġ�����������ˡ��������ط��䣨��ռ��
            # if self.robot[i]['type']==0 and self.isRobotOccupy[i] == 1: # 
            #     task,score = self.getBestBuyTask(i)
            #     if task!=None and score/self.robotTargetScore[i] > 20: # �ط���
            #         # ԭ����ȡ��
            #         self.wtReservation[self.robotTargetId[i]]['product'] = 0

            #         # ���»����˵���״̬
            #         self.robotTargetId[i] = task 
            #         self.robotTargetScore[i] = score
            #         self.isRobotOccupy[i] = 1
            #         self.robotTaskType[i] = 0
            #         self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
            #         # ���¹���̨Ԥ����
            #         self.wtReservation[task]['product'] = 1


    def getInstrAndUpdate(self):
        """
        # ���ݻ����˱���״̬��ִ�е���������
        # 1�����»�����ռ�����
        # 2����������ָ�����
        """
        self.instr = ''
        # for i in range(4):
        #     x_i = self.robot[i]['x']
        #     y_i = self.robot[i]['y']
        #     # ������Ŀ�깤��̨
        #     if self.robotTargetOrid[i][0]==self.workTable[self.robotTargetId[i]]['x'] and self.robotTargetOrid[i][1]==self.workTable[self.robotTargetId[i]]['y']:
        #         # Ԥ����ײ
        #         a = self.robot[i]['orientation'] # �����
        #         vector_a = np.array([math.cos(a),math.sin(a)]) # ������i��������
        #         for j in range(i+1,4):
        #             x_j = self.robot[j]['x']
        #             y_j = self.robot[j]['y']
        #             x_bar = self.robot[j]['x'] - self.robot[i]['x']
        #             y_bar = self.robot[j]['x'] - self.robot[i]['y']
        #             vector_b = np.array([x_bar,y_bar]) # ������i��ǰλ��ָ�������j������
        #             dist_a = np.linalg.norm(vector_a)
        #             dist_b = np.linalg.norm(vector_b) # ������i�������j�ľ���
        #             dot = np.dot(vector_a,vector_b)     # ���

        #             cos_theta = dot/(dist_a*dist_b) # ����aת��b��ת�������ֵ 
        #             theta = math.acos(round(cos_theta,10)) # a -> b ת���
        #             if dist_b < 2.6 and abs(theta) < math.pi/5 and self.robot[i]['orientation']*self.robot[j]['orientation']<=0:  # �෴����
        #                     # ������ٵ�Ŀ�깤��̨����
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
        #     # ��ٵ�Ŀ�깤��̨
        #     else:
        #         # ������������������Ŀ�깤��̨
        #         if pow(self.robot[i]['x'] - self.robotTargetOrid[i][0], 2) + pow(self.robot[i]['y'] - self.robotTargetOrid[i][1], 2) < pow(0.4, 2):
        #             self.robotTargetOrid[i] = (self.workTable[self.robotTargetId[i]]['x'],self.workTable[self.robotTargetId[i]]['y'])
        #         # δ����
        #         else:
        #             pass


        for i in range(4):
            # ��Ʒ����ʱ���ʱ
            if self.robot[i]['type'] != 0:
                self.robotObjOccupyTime[i] += 0.02
                # ������Ʒʱ�䳬ʱ
                if self.robotObjOccupyTime[i] >= self.destoryTime:
                    self.instr += 'destroy %d\n' % (i)
                    # ���»�����ռ�����
                    self.isRobotOccupy[i] = 0
                    self.robotObjOccupyTime[i] = 0
                    # ���¹���̨Ԥ����
                    self.wtReservation[self.robotTargetId[i]][self.robot[i]['type']] = 0

        
            # ռ��״̬��δ����Ŀ���
            if self.isRobotOccupy[i] == 1 and self.robot[i]['workTableID'] != self.robotTargetId[i]: 
                a = self.robot[i]['orientation'] # �����
                vector_a = np.array([math.cos(a),math.sin(a)]) # �����˳�������

                x_bar = self.robotTargetOrid[i][0] - self.robot[i]['x']
                y_bar = self.robotTargetOrid[i][1] - self.robot[i]['y']
                vector_b = np.array([x_bar,y_bar]) # �����˵�ǰλ��ָ��Ŀ��������

                dist_a = np.linalg.norm(vector_a)
                dist_b = np.linalg.norm(vector_b) # ��������Ŀ���ľ���
                
                dot = np.dot(vector_a,vector_b)     # ���
                cross = np.cross(vector_a,vector_b) # ���
                
                cos_theta = dot/(dist_a*dist_b) # ����aת��b��ת�������ֵ 
                theta = math.acos(round(cos_theta,10)) # a -> b ת���

                if cross < 0: # Ӧ��˳ʱ��ת
                    theta = -theta
                else: # ��ʱ��ת
                    theta = theta
                
                '''
                ������Ʒ������Ϊ0.88247 kg
                �����ٶȣ�283.295 m/s*s (5.6659 m/s*frame)
                ���Ǽ��ٶȣ�403.4115 pi/s*s (8.06823 pi/s*frame)

                ��������Ʒ������Ϊ0.63617 kg
                �����ٶȣ�392.976 m/s*s (7.85952 m/s*frame)
                ���Ǽ��ٶȣ�776.2503 pi/s*s (15.525 pi/s*frame)
                '''
                # ���ٶ�
                angle_v = min(theta/0.02, math.pi) if theta>0 else max(theta/0.02, -math.pi)
                self.instr += 'rotate %d %f\n' % (i,angle_v)

                #�ٶ�
                x = self.robot[i]['x']
                y = self.robot[i]['y']
                # ��
                if x<2 and y<48 and y>2 and ((a>=-math.pi and a<-math.pi/2) or (a>math.pi/2 and a<=math.pi)):
                    v = 1
                # ��
                elif x>48 and y<48 and y>2 and a>-math.pi/2 and a<math.pi/2:
                    v = 1
                # ��
                elif x>2 and x<48 and y>48 and a>0 and a<math.pi:
                    v = 1
                # ��
                elif x>2 and x<48 and y<2 and a>-math.pi and a<0:
                    v = 1
                # ����
                elif x<=2 and y>=48 and ((a>=-math.pi and a<-math.pi/2) or (a>0 and a<=math.pi)):
                    v = 1
                # ����
                elif x<=2 and y<=2 and ((a>=-math.pi and a<0) or (a>math.pi/2 and a<=math.pi)):
                    v = 1
                # ����
                elif x>=48 and y>=48 and a>0 and a<math.pi/2:
                    v = 1
                # ����
                elif x>=48 and y<=2 and a>-math.pi/2 and a<0:
                    v = 1
                else:
                    # v = 6-6*abs(theta)/math.pi
                    v = 6/(abs(theta)+1)
                self.instr = self.instr + 'forward %d %d\n' % (i,v)

            # ռ��״̬������Ŀ���
            elif self.isRobotOccupy[i] == 1 and self.robot[i]['workTableID'] == self.robotTargetId[i]:
                # �ڹ���̨������۳�
                if self.robotTaskType[i] == 0: # ��
                    if self.workTable[self.robotTargetId[i]]['productState']:
                        self.instr += 'buy %d\n' % (i)
                        # ���»�����ռ�����
                        self.isRobotOccupy[i] = 0
                        self.robotObjOccupyTime[i] = 0 # ��Ʒ����ʱ��,�����뿪ʼ��ʱ
                        # ���¹���̨Ԥ����
                        self.wtReservation[self.robotTargetId[i]]['product'] = 0
                    else:
                        self.instr = self.instr + 'forward %d %d\n' % (i,0)

                elif self.robotTaskType[i] == 1 : # ��
                    self.instr += 'sell %d\n' % (i)
                    # ���»�����ռ�����
                    self.isRobotOccupy[i] = 0
                    # ���¹���̨Ԥ����
                    self.wtReservation[self.robotTargetId[i]][self.robot[i]['type']] = 0
            else: # ����״̬
                pass

        return self.instr

    def run(self):
        """
        # ��ʼ��,�������������н���
        """
        # ��ʼ��
        self.initMap()

        # ����
        while True:
            # ÿһ֡����(����������)
            end = self.inputData()
            if end:
                break
            # ÿһ֡���(�����˿���ָ��) 
            self.outputData()

        #     #��־
        #     if self.frameId % 50 == 1:
        #     # if 1:
        #         robot_ordin = []
        #         self.info.write("ʱ��֡��"+str(self.frameId)+"\n")
        #         self.info.write("����̨��"+str(self.workTable)+"\n")
        #         for i in range(4):
        #             self.info.write("�����ˣ�"+str(self.robot[i])+"\n")
        #             robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
        #         self.info.write("ָ�\n"+str(self.instr))
        #         self.info.write("�Ƿ�ռ��      :"+str(self.isRobotOccupy)+"\n")
        #         self.info.write("Ŀ�깤��̨ID  :"+str(self.robotTargetId)+"\n")
        #         self.info.write("Ŀ�깤��̨���� :"+str(self.robotTargetOrid)+"\n")
        #         self.info.write("����������    :"+str(robot_ordin)+"\n")
        #         self.info.write("�������������� :"+str(self.robotTaskType)+"\n")
        #         self.info.write("������ռ��ʱ�� :"+str(self.robotObjOccupyTime)+"\n")
        #         self.info.write("\n")
                
        
        # # �ر���־�ļ�
        # self.info.close()


if __name__ == '__main__':
    
    solver = Solution()
    solver.run()
    
