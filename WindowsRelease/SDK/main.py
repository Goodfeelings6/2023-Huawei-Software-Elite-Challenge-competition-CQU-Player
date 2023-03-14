#!/bin/bash
import sys
import numpy as np

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

        # 输出机器人控制指令
        line_speed, angle_speed = 3, 1.5
        for robot_id in range(4):
            sys.stdout.write('forward %d %d\n' % (robot_id, line_speed))
            sys.stdout.write('rotate %d %f\n' % (robot_id, angle_speed))
        
        # 输出结束后，输出 'OK'
        self.finish()

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
            if self.frameId % 10 == 1:
                self.info.write("时间帧："+str(self.frameId)+"\n")
                self.info.write("工作台："+str(self.workTable)+"\n")
                self.info.write("机器人："+str(self.robot)+"\n")
        
        # 关闭日志文件
        self.info.close()


if __name__ == '__main__':
    
    solver = Solution()
    solver.run()
    
