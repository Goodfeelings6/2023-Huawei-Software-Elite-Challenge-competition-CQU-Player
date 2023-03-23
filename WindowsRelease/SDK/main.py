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

        # �̶���Ϣ �������,��ÿ�ֹ���̨��Ҫ����Ʒ(ԭ���ϻ��Ʒ)����
        self.demandTable = {1:[],2:[],3:[],4:[1,2],5:[1,3],6:[2,3],7:[4,5,6],8:[7],9:[1,2,3,4,5,6,7]} 
        # �̶���Ϣ ����Ʒ������
        self.income = {1:3000,2:3200,3:3400,4:7100,5:7800,6:8300,7:29000}

        # �����˵��ȿ���
        self.isRobotOccupy = [0 for i in range(4)] # ��ʶ�������Ƿ�ռ��,1ռ��,0����
        self.robotTargetId = [[0,0] for i in range(4)]   # ��ռ�û�������Ҫǰ����Ŀ�깤��̨id(���� isRobotOccupy[i]==1 ʱiλ��������Ч)
        self.robotTargetOrid = [[(0,0),(0,0)] for i in range(4)] # ��ռ�û�������Ҫǰ����Ŀ�깤��̨����
        self.robotTaskType = [0 for i in range(4)] # ��ռ�û�����Ŀǰ����������,ֻ����buy��sell,0��ʾbuy,1��ʾsell

        # ����̨Ԥ����(�����ͼʱ˳���ʼ��,��Ԥ����Ʒ����Ʒ��, 0δ��Ԥ����1��Ԥ��)
        self.wtReservation = []

        self.turning=[0 for i in range(4)]

        # ������
        self.abandonThreshold = 0.2  # ������ i ������ǰ���������ֵ, ��Χ0~����, Խ��Խ������

        # ���� 
        self.sw_nearest = 0 # ˳·�㷨 �Ƿ��� 0��1��
        self.sw_buy_pred = 1 # ������Ԥ�� �Ƿ��� 1��0��
        self.sw_sell_pred = 1 # ������Ԥ�� �Ƿ��� 1��0��
        self.param_mps = 50 # ̰��ϵ�� 1~1000
        self.sw_abandon = 1 # ������ǰ�����㷨 �Ƿ��� 1��0��
        self.sw_avoidCrash = 1 # ��ײ���� �Ƿ��� 1��0��

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
        #@@@
        self.sw_nearest = 1
        self.sw_buy_pred = 1
        self.sw_sell_pred = 1
        self.param_mps = 981
        self.sw_abandon = 1
        self.sw_avoidCrash = 1
        #@@@
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
        # ��������˿���ָ��
        sys.stdout.write(self.instr)
        # ���������,��� 'OK'
        self.finish()

    def f(self,x,maxX,minRate):
        """
        # ��ֵ�ʼ��㹫ʽ
        """
        if x < maxX:
            return (1-math.sqrt(1-(1-x/maxX)**2))*(1-minRate)+minRate
        elif x >= maxX:
            return minRate

    def buyTaskPredict(self,workT,dist):
        """
        # Ԥ����������Ƿ���� ����: �����˵���Ŀ�깤��̨ǰ��������Ʒ����
        :param workT Ŀ������̨
        :param dist �����˵�Ŀ������̨�ľ���
        """
        if workT['remainTime']>0 and dist/6 > workT['remainTime']*0.02:
            return True
        else:
            return False

    def reservationPredict(self,idx,workT,dist):
        """
        # Ԥ���ѱ�Ԥ����Ʒ������̨,�Ƿ������ظ�Ԥ��������: ��Ϊÿ��Ԥ���Ļ������ṩ��Ʒ��
        :param idx Ŀ������̨id
        :param workT Ŀ������̨
        :param dist �����˵�Ŀ������̨�ľ���
        """
        # ����˭��Ԥ����workT
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
        # �ж�i����������������Ƿ���workT�����������������˶��ڹ���̨workT ˳·(�����), ���� return False , ���� True
        :param i �����˱��
        :param workT ����̨
        """
        # i �� workT ����
        i_dist = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])
        for j in range(4):
            j_finish_dist = 1e5
            if i!=j and self.isRobotOccupy[j]==1 and self.robotTaskType[j]==1: # j�������������Ѿ�������·��
                # j ��Ŀ�깤��̨�� workT ����
                j_finish_dist = np.linalg.norm([self.robotTargetOrid[j][1][0]-workT['x'],self.robotTargetOrid[j][1][1]-workT['y']])
            elif i!=j and self.isRobotOccupy[j]==0: # jû��������
                # j �� workT ����
                j_finish_dist = np.linalg.norm([self.robot[j]['x']-workT['x'],self.robot[j]['y']-workT['y']])
            # ���� j ����
            if i_dist > j_finish_dist:
                return False
        return True

        de
   
    def isMaterialComplete(self,workT):
        """
        # �ж� workT ����̨�Ƿ������ȫ��
        """ 
        matrial_type = self.demandTable[workT['type']]
        for i in matrial_type:
            if (workT['rawState']>>i)&1 == 0:
                return False
        return True
  
    def sellTaskPredict(self,idx,workT,buy_dist,sell_dist):
        """
        # Ԥ����������Ƿ���� ����: �����˵���Ŀ�깤��̨ǰ���ڳ���Ӧ��Ʒ�����
        :param idx Ŀ��������̨id
        :param workT Ŀ��������̨
        :param buy_dist �����˵�Ŀ������̨�ľ���
        :param sell_dist �����˵�Ŀ��������̨�ľ���
        """
        # �涨ʱ�� T ��: ĳһ�������˴ӷ�������ʼ������Ʒ��������������̨�� ���ʱ��
        # �ڳ���Ӧ��Ʒ�������: 1,�޲�Ʒ �� ʣ������ʱ��֡С�ڹ涨ʱ��T �� �����뱸����С�ڹ涨ʱ�����뱸
        #                     2,�в�Ʒ �� ʣ������ʱ��֡С�ڹ涨ʱ��T �� ȡ��Ʒʱ��<�涨ʱ��T �� �����뱸����С�� [�涨ʱ��-ȡ��Ʒʱ��] ���뱸
        #  (������С�ڹ涨ʱ�����뱸) ��Ԥ��ø��� T_T ,�ȷ��� 
        
        T = (buy_dist+sell_dist)/6
        getProductTime = 1e5
        for i in range(4):
            if self.robotTaskType[i]==0 and self.robotTargetId[i][0] == idx: # �л��������������·��
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
        # ���ݳ�����Ϣ,����һ�����ŵ�����
        :param i �����˱��
        """   
        epl = 1e-8 # ��С��������ֹ����Ϊ0  
        # ���ϵ���������  #�ֵ���Ϊ ��Ʒ����:(��������,��ȱ������)
        needType = {1:[epl,0],2:[epl,0],3:[epl,0],4:[epl,0],5:[epl,0],6:[epl,0],7:[epl,0]}  
        # # ͬһ���͹���̨���������ԭ���ϵ�����  #�ֵ���Ϊ ����̨����:{��Ʒ����:(��������,��ȱ������)}
        sameWorkTableNeedType = {4:{1:[epl,0],2:[epl,0]},5:{1:[epl,0],3:[epl,0]},6:{2:[epl,0],3:[epl,0]},7:{4:[epl,0],5:[epl,0],6:[epl,0]}}
        # �˹���̨ԭ���걸�̶�, ����̨id:�����뱸�̶�
        readyRate = {} 
        ## ��Ϣͳ��
        for idx,workT in enumerate(self.workTable):   
            readyCount = 0
            for objType in self.demandTable[workT['type']]:
                needType[objType][0] += 1
                if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # ��ȱ�Ҳ���Ԥ��
                    needType[objType][1] += 1 

                if workT['type']>=4 and workT['type']<=7:
                    sameWorkTableNeedType[workT['type']][objType][0] += 1
                    if (workT['rawState']>>objType)&1==0 and self.wtReservation[idx][objType]==0: # ��ȱ�Ҳ���Ԥ��
                        sameWorkTableNeedType[workT['type']][objType][1] += 1 
                    else: # �뱸��Ԥ��
                        readyCount += 1

            if workT['type']>=4 and workT['type']<=7:
                readyRate[idx] = readyCount / len(self.demandTable[workT['type']])

                
        # self.info.write(str(self.frameId)+"\n")

        # task �ռ�
        task = []
        profit = []
        buy_dist = {} # ����̨id:������˾���
        sell_dist = {} # ����̨id:����������߾���
        for idx,workT in enumerate(self.workTable): 
            if workT['type'] >= 1 and workT['type'] <= 7:
                ### ͳ����ľ���              
                buy_dist[idx] = np.linalg.norm([self.robot[i]['x']-workT['x'],self.robot[i]['y']-workT['y']])
#------�ɵ���----##### ���е�������
                if  (self.sw_nearest or self.isNearest(i,workT)) \
                and (workT['productState']==1 or (self.sw_buy_pred and self.buyTaskPredict(workT,buy_dist[idx]))) \
                and (self.wtReservation[idx]['product']==0 or self.wtReservation[idx]['product']==1 and self.reservationPredict(idx,workT,buy_dist[idx])):
                    ### ͳ���������߾���
                    objT = workT['type']
                    for idx2,workT2 in enumerate(self.workTable): 
                        # �����һ����Ч������
                        if objT in self.demandTable[workT2['type']]:
                            # ͳ�����ľ���
                            sell_dist[idx2] = np.linalg.norm([workT['x']-workT2['x'],workT['y']-workT2['y']])
#-------�ɵ���--------------##### ���е�������
                            if ((workT2['rawState']>>objT)&1==0 or (self.sw_sell_pred and self.sellTaskPredict(idx2,workT2,buy_dist[idx],sell_dist[idx2]))) \
                            and (buy_dist[idx]+sell_dist[idx2])/6+1.5 < (9000-self.frameId)*0.02 \
                            and (self.wtReservation[idx2][objT]==0):
                                task.append([idx,idx2])
                                sell_time = sell_dist[idx2]/6
                                total_time = (buy_dist[idx]+sell_dist[idx2])/6
                                # ��λʱ������
                                mps = self.income[objT] * self.f(sell_time*50,9000,0.8) / total_time
                                
                                if workT2['type'] == 9: # ����9
                                    productNeed = 1
                                    rawNeed = 1
                                    rawReadyRate = 1
                                elif workT2['type'] == 8: # ����8
                                    productNeed = 1
                                    rawNeed = 1
                                    rawReadyRate = 1
                                elif workT2['type'] == 7: # ����7
                                    # ��������̨�Դ˹���̨��Ʒ�������
                                    productNeed = 1         
                                    # �����͹���̨����Ը���ԭ���ϵ������
                                    rawNeed =  sameWorkTableNeedType[7][workT['type']][1] / sameWorkTableNeedType[7][workT['type']][0]
                                    # �˹���̨ԭ���걸�̶�    
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]
                                elif workT2['type'] == 6: # ����6
                                    productNeed = needType[6][1] / needType[6][0]
                                    rawNeed = sameWorkTableNeedType[6][workT['type']][1] / sameWorkTableNeedType[6][workT['type']][0]
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]
                                elif workT2['type'] == 5: # ����5
                                    productNeed = needType[5][1] / needType[5][0]
                                    rawNeed = sameWorkTableNeedType[5][workT['type']][1] / sameWorkTableNeedType[5][workT['type']][0]
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]
                                elif workT2['type'] == 4: # ����4
                                    productNeed = needType[4][1] / needType[4][0]
                                    rawNeed = sameWorkTableNeedType[4][workT['type']][1] / sameWorkTableNeedType[4][workT['type']][0]
                                    rawReadyRate = 0 if readyRate[idx2]==1 else readyRate[idx2]   

                                score = mps/self.param_mps + productNeed + rawNeed + rawReadyRate
                                # self.info.write("id1:%d,type:%d  id2:%d,type:%d  score = %.3f,%.3f,%.3f,%.3f = %.3f \n" %(idx,workT['type'],idx2,workT2['type'],mps,productNeed,rawNeed,rawReadyRate,score))

                                profit.append(score)
        # task ѡ��
        if len(task)!=0:
            max_i = np.argmax(np.array(profit))
            return task[max_i]
        else:
            return None

    def judgeAbandon(self,i):
        """
        # �ж��Ƿ���Ҫ���� ���Ϊ i �Ļ�����Ŀǰ������, ����,return True, ���� False
        :param i �����˱��
        :return bool
        ����: ���������������;�еĻ����� j ��Ŀ����ǻ����� i ��Ҫǰ��������̨ ,
        ��  T(i)/T(j) > self.abandonThreshold ����� i ������. 
        T(x) ��ʾ���Ϊx�Ļ����˵����¸�Ŀ��������ʱ��.
        self.abandonThreshold Ϊ�ɵ�����
        ʱ��֮��Ҳ������֮��.
        """
        # i Ŀ�깤��̨����(��;��)
        i_target = self.robotTargetOrid[i][0]
        # i �� �� target ����
        i_dist = np.linalg.norm([self.robot[i]['x']-i_target[0],self.robot[i]['y']-i_target[1]])

        for j in range(4):
            # j�������������Ѿ�������·���� j ��������̨�� i Ŀ�깤��̨��ͬ
            if i!=j and self.isRobotOccupy[j]==1 and self.robotTaskType[j]==1 \
            and self.robotTargetId[j][1] == self.robotTargetId[i][0]: 
                # j Ŀ�깤��̨����
                j_target = self.robotTargetOrid[i][1]
                # j �� Ŀ�깤��̨����
                j_dist = np.linalg.norm([self.robot[j]['x']-j_target[0],self.robot[j]['y']-j_target[1]])
            else:
                j_dist = 1e5

            # ���� j ˳·, �� i ���Է���
            if i_dist / j_dist > self.abandonThreshold:
                return True
        return False

    def scheduleRobot(self):
        """
        # �����л����˷�������,����
        """       
        # ���� = ��������̨id �ֱ�Ϊ buy �� sell, ��ʾ������Ҫǰ����Ӧ����̨ , ִ�� buy �� sell  
        self.instr = ''
        for i in range(4):
            # if ����
            if self.isRobotOccupy[i] == 0: 
                # ��������
                task = self.getBestTask(i)  
                if task!=None: 
                    # ���»����˵���״̬
                    self.robotTargetId[i] = task  # [buy sell]
                    self.isRobotOccupy[i] = 1
                    self.robotTaskType[i] = 0
                    # ����������
                    self.robotTargetOrid[i][0] = (self.workTable[task[0]]['x'],self.workTable[task[0]]['y'])
                    # ����������
                    self.robotTargetOrid[i][1] = (self.workTable[task[1]]['x'],self.workTable[task[1]]['y'])
                    # ���¹���̨Ԥ����
                    self.wtReservation[task[0]]['product'] = 1
                    if self.workTable[task[1]]['type']==8 or self.workTable[task[1]]['type']==9: # ����Ԥ����һֱ����
                        self.wtReservation[task[1]][self.workTable[task[0]]['type']] = 0
                    else:
                        self.wtReservation[task[1]][self.workTable[task[0]]['type']] = 1
                else: # û����ɷ���
#----�ɵ���---------##### # ����ͼ������ (��ĳ������̨�ߣ�)
                    self.instr += self.control(i,(25,25))
                    
            # ��ռ��״̬
            elif self.isRobotOccupy[i] == 1 and self.robotTaskType[i] == 0 : 
                # δ������Ŀ���
                if self.robot[i]['workTableID'] != self.robotTargetId[i][0]:
                    # ���������������;�еĻ����� j ��Ŀ����ǻ����� i ��Ҫǰ��������̨ ,
 #---�ɵ���----------##### # ��  T(i)/T(j) > ��ֵ ����� i ������ T(x) ��ʾ���Ϊx�Ļ����˵����¸�Ŀ��������ʱ��
                    if self.sw_abandon and self.judgeAbandon(i):
                        # ����������
                        # ������תΪ����
                        self.isRobotOccupy[i] = 0
                        # ���¹���̨Ԥ����
                        self.wtReservation[self.robotTargetId[i][0]]['product'] = 0 # ȡ����Ԥ��
                        objT = self.workTable[self.robotTargetId[i][0]]['type']
                        self.wtReservation[self.robotTargetId[i][1]][objT] = 0 # ȡ����Ԥ��
                    else:
                        self.instr += self.control(i,self.robotTargetOrid[i][0])
                # ����Ŀ���
                else:
                    # ��
                    self.instr += 'buy %d\n' % (i)
                    # �������������ʹ� �� תΪ ��
                    self.robotTaskType[i] = 1
                    # ���¹���̨Ԥ����
                    self.wtReservation[self.robotTargetId[i][0]]['product'] = 0

            # ��ռ��״̬
            elif self.isRobotOccupy[i] == 1 and self.robotTaskType[i] == 1:
                # δ������Ŀ���
                if self.robot[i]['workTableID'] != self.robotTargetId[i][1]:
                    self.instr += self.control(i,self.robotTargetOrid[i][1])
                # ����Ŀ���
                else: 
                    # ��
                    self.instr += 'sell %d\n' % (i)
                    # ������תΪ����
                    self.isRobotOccupy[i] = 0
                    # ���¹���̨Ԥ����
                    self.wtReservation[self.robotTargetId[i][1]][self.robot[i]['type']] = 0
        if self.sw_avoidCrash == 1:
            self.avoidCrash()
    
    def avoidCrash(self):
        """��ײ����"""
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
                    #����
                    t1=0
                    t2=0
                    if k1!=k2 and self.robot[i]['orientation']!=-math.pi/2 and self.robot[i]['orientation']!=math.pi/2 and self.robot[j]['orientation']!=-math.pi/2and self.robot[j]['orientation']!=math.pi/2:
                        x_0=(b2-b1)/(k1-k2)
                        y_0=x_0*k1+b1
                        if(x_0-self.robot[i]['x'])*math.cos(self.robot[i]['orientation'])>0 and(y_0-self.robot[i]['y'])*math.sin(self.robot[i]['orientation'])>0:
                            t1=np.linalg.norm(np.array([self.robot[i]['x']-x_0, self.robot[i]['y']-y_0]))/0.12 #��ǰλ�õ���ײ�ĵ�ľ��봦��ÿһ֡����ٶ����еľ���
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
                                continue #��������С���˶������෴���Ǿ��Բ����ܲ�������ײ��������Ϊ��ײ���������ʱ��
                            if self.robot[j]['orientation']<0 and self.robot[j]['y']>self.robot[i]['y'] and self.robot[j]['x']>self.robot[i]['x']:
                                turn[j] = math.pi
                            if self.robot[j]['orientation']<=0 and self.robot[j]['y']>self.robot[i]['y'] and self.robot[j]['x']<=self.robot[i]['x']:
                                turn[j] = -math.pi
                            if self.robot[j]['orientation']>0 and self.robot[j]['y']<self.robot[i]['y'] and self.robot[j]['x']>self.robot[i]['x']:
                                turn[j] = -math.pi
                            if self.robot[j]['orientation']>=0 and self.robot[j]['y']<self.robot[i]['y'] and self.robot[j]['x']<=self.robot[i]['x']:
                                turn[j] = math.pi
                            self.turning[j]-=1
        # ���ٶ�
        for i in range(4):
            if turn[i]!=0:
                instr_i = 'rotate %d %f\n' % (i,turn[i])
                self.instr += instr_i

    def control(self,i,target):
        """
        # �ƶ�����
        :param i �����˱��
        :param target Ŀ�������
        """
        instr_i = ''

        a = self.robot[i]['orientation'] # �����
        vector_a = np.array([math.cos(a),math.sin(a)]) # �����˳��� 
        x_bar = target[0] - self.robot[i]['x']
        y_bar = target[1] - self.robot[i]['y']
        vector_b = np.array([x_bar,y_bar]) # �����˵�ǰλ��ָ��Ŀ���� 
        dist_a = np.linalg.norm(vector_a)
        dist_b = np.linalg.norm(vector_b) # ��������Ŀ���ľ���

        dot = np.dot(vector_a,vector_b)     # ���
        cross = np.cross(vector_a,vector_b) # ���

        cos_theta = dot/(dist_a*dist_b) # ����aת��b��ת�������ֵ 
        theta = math.acos(round(cos_theta,10)) # a -> b ת  
        if cross < 0: # Ӧ��˳ʱ��ת
            theta = -theta
        else: # ��ʱ��ת
            theta = theta

        '''
        ������Ʒ������Ϊ0.88247 kg
        �����ٶȣ�283.295 m/s*s (5.6659 m/s*frame)
        ���Ǽ��ٶȣ�403.4115 pi/s*s (8.06823 pi/s*fram    
        ��������Ʒ������Ϊ0.63617 kg
        �����ٶȣ�392.976 m/s*s (7.85952 m/s*frame)
        ���Ǽ��ٶȣ�776.2503 pi/s*s (15.525 pi/s*frame)
        '''
        # ���ٶ�
        angle_v = min(theta/0.02, math.pi) if theta>0 else max(theta/0.02, -math.pi)
        instr_i += 'rotate %d %f\n' % (i,angle_v)

        #�ٶ�
        x = self.robot[i]['x']
        y = self.robot[i]['y']
        
        # ��
        if x<2 and y<48 and y>2 and ((a>=-math.pi and a<-math.pi/2) or (a>math.pi/2 and a<=math.pi)):
            v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
        # ��
        elif x>48 and y<48 and y>2 and a>-math.pi/2 and a<math.pi/2:
            v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
        # ��
        elif x>2 and x<48 and y>48 and a>0 and a<math.pi:
            if a<=math.pi/2:
                v = 6/(a*10/math.pi+1)
            else:
                v = 6/((math.pi-a)*10/math.pi+1)
        # ��
        elif x>2 and x<48 and y<2 and a>-math.pi and a<0:
            if a>=-math.pi/2:
                v = 6/(-a*10/math.pi+1)
            else:
                v = 6/((math.pi+a)*10/math.pi+1)
        # ����
        elif x<=2 and y>=48 and ((a>=-math.pi and a<-math.pi/2) or (a>0 and a<=math.pi)):
            if a>0 and a<=math.pi/2:
                v = 6/(a*10/math.pi+1)
            elif a>=math.pi and a<-math.pi/2:
                v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
            elif a>math.pi/2 and a<=3*math.pi/4:
                v = 6/((a-math.pi/2)*24/math.pi+6)
            else:
                v = 6/((math.pi-a)*24/math.pi+6)
        # ����
        elif x<=2 and y<=2 and ((a>=-math.pi and a<0) or (a>math.pi/2 and a<=math.pi)):
            if a>=-math.pi/2 and a<0:
                v = 6/(-a*10/math.pi+1)
            elif a>math.pi/2 and a<=math.pi:
                v = v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
            elif a>=-3*math.pi/4 and a<-math.pi/2:
                v = 6/(abs(a+math.pi/2)*24/math.pi+6)
            else:
                v = 6/(abs(a+math.pi)*24/math.pi+6)
        # ����
        elif x>=48 and y>=48 and a>-math.pi/2 and a<math.pi:
            if a>=math.pi/2:
                v = 6/((math.pi-a)*10/math.pi+1)
            elif a<=0:
                v = 6/(abs(abs(a)-math.pi/2)*10/math.pi+1)
            elif a>0 and a<=math.pi/4:
                v = 6/(a*24/math.pi+6)
            else:
                v = 6/(abs(a-math.pi/2)*24/math.pi+6)
        # ����
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
            # if 1:
            #     robot_ordin = []
            #     self.info.write("ʱ��֡��"+str(self.frameId)+"\n")
            #     self.info.write("����̨��"+str(self.workTable)+"\n")
            #     for i in range(4):
            #         self.info.write("�����ˣ�"+str(self.robot[i])+"\n")
            #         robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
            #     self.info.write("ָ�\n"+str(self.instr))
            #     self.info.write("�Ƿ�ռ��      :"+str(self.isRobotOccupy)+"\n")
            #     self.info.write("Ŀ�깤��̨ID  :"+str(self.robotTargetId)+"\n")
            #     self.info.write("Ŀ�깤��̨���� :"+str(self.robotTargetOrid)+"\n")
            #     self.info.write("����������    :"+str(robot_ordin)+"\n")
            #     self.info.write("�������������� :"+str(self.robotTaskType)+"\n")
            #     self.info.write("\n")
                  
        # �ر���־�ļ�
        # self.info.close()


if __name__ == '__main__':
    
    solver = Solution()
    solver.run()
    
