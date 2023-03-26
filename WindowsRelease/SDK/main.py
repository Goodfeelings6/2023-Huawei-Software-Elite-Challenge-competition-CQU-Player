#coding=gb2312
#!/bin/bash
import sys
import numpy as np
import time
from Strategy1 import Strategy1
from Strategy2 import Strategy2
from Strategy3 import Strategy3
from Strategy4 import Strategy4

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

        # ����̨Ԥ����(�����ͼʱ˳���ʼ��,��Ԥ����Ʒ����Ʒ��, 0δ��Ԥ����1��Ԥ��)
        self.wtReservation = []

        # ���ȡ����Ʋ���
        self.strategy = None


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
        if wtNum == 43:
            self.strategy = Strategy1(self.destoryTime,self.demandTable,self.wtReservation)
        elif wtNum == 25:
            self.strategy = Strategy2(self.destoryTime,self.demandTable,self.wtReservation)
        elif wtNum == 50:
            self.strategy = Strategy3(self.destoryTime,self.demandTable,self.wtReservation)
        elif wtNum == 18:
            self.strategy = Strategy4(self.destoryTime,self.demandTable,self.wtReservation)

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
        # �����Զ���������
        self.strategy.getMessage(self.workTable,self.robot,self.frameId)
        # ���в��Զ���
        self.strategy.run()
        # ���Զ��󷵻� ָ��

        self.instr = self.strategy.sentMessage()
        # time.sleep(0.013)
        # ��������˿���ָ��
        sys.stdout.write(self.instr)
        # ���������,��� 'OK'
        self.finish()

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

            # ��־
            # if self.frameId % 50 == 1:
            # if 1:
            #     self.log()
            
    def log(self):
        """
        # д��־
        """      
        #---��־---
        self.info = open('info.txt', 'a') 

        robot_ordin = []
        self.info.write("ʱ��֡��"+str(self.frameId)+"\n")
        self.info.write("����̨��"+str(self.workTable)+"\n")
        for i in range(4):
            self.info.write("�����ˣ�"+str(self.robot[i])+"\n")
            robot_ordin.append((self.robot[i]['x'],self.robot[i]['y']))
        self.info.write("ָ�\n"+str(self.instr))
        self.info.write("�Ƿ�ռ��      :"+str(self.strategy.isRobotOccupy)+"\n")
        self.info.write("Ŀ�깤��̨ID  :"+str(self.strategy.robotTargetId)+"\n")
        self.info.write("Ŀ�깤��̨���� :"+str(self.strategy.robotTargetOrid)+"\n")
        self.info.write("����������    :"+str(robot_ordin)+"\n")
        self.info.write("�������������� :"+str(self.strategy.robotTaskType)+"\n")
        self.info.write("\n")
                
        # �ر���־�ļ�
        self.info.close()

if __name__ == '__main__':
    
    solver = Solution()
    solver.run()