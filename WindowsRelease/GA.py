import re
import numpy as np
import subprocess

# 参数
DNA_SIZE = 4 # 每个参数用5位2进制编码
POP_SIZE = 5 # 种群数
CROSSOVER_RATE = 0.8 # 交叉概率
MUTATION_RATE = 0.07 # 变异概率
N_GENERATIONS = 5 # 迭代代数
# 所有优化自变量的范围
BOUND = [0,1]



def execCmd(cmd:str)->str:
    """
    # 调用命令行执行命令 cmd ,返回输出的结果
    """
    r = subprocess.check_output(cmd,shell=True,encoding='gbk')
    return r

def readFile(filePath:str)->str:
    """
    # 把filePath文件读取到data中返回
    """
    f = open(filePath, "r",encoding='GB2312')
    data = f.read()
    f.close()
    return data

def writeFile(filePath:str, data:str):
    """
    # 把data写入filePath文件
    """
    f = open(filePath, "w")
    f.write(data)
    f.close()

def F(cmd:str,param_need,param_buy_dist,param_need_dist,param_remainTime,param_haveProduct,param_produce,param_lackRate,param_sell_dist)->int:
    """
    # 评价函数, 改变main.py中对应参数, 命令行运行cmd, 返回结果
    """
    # 读取
    filePath = "SDK\main.py"
    readData = readFile(filePath)
    # 写入
    pattern2 = r'#@@@[\s\S]*#@@@'
    targetStr = '#@@@\n        self.param_need = %f\n        self.param_buy_dist = %f\n        '\
                'self.param_need_dist = %f\n        self.param_remainTime = %f\n        self.param_haveProduct = %f\n        '\
                'self.param_produce = %f\n        self.param_lackRate = %f\n        '\
                'self.param_sell_dist = %f\n        #@@@' %(param_need,param_buy_dist,param_need_dist,param_remainTime,param_haveProduct,param_produce,param_lackRate,param_sell_dist)
        
    replaceResult = re.sub(pattern2,targetStr,readData)
    writeFile(filePath,replaceResult)
    # 调用并返回结果
    result = execCmd(cmd)
    pattern = '\d+'
    match = re.search(pattern,result)
    money = int(match.group())

    return money

def decodeDNA(pop):
    """
    # 解码
    :param pop 表示种群矩阵,一行表示一个二进制编码表示的DNA,矩阵的行数为种群数目
    """
    param_need = pop[:,0:DNA_SIZE:1]
    param_buy_dist = pop[:,DNA_SIZE:2*DNA_SIZE:1]
    param_need_dist = pop[:,2*DNA_SIZE:3*DNA_SIZE:1]
    param_remainTime = pop[:,3*DNA_SIZE:4*DNA_SIZE:1]
    param_haveProduct = pop[:,4*DNA_SIZE:5*DNA_SIZE:1]
    param_produce = pop[:,5*DNA_SIZE:6*DNA_SIZE:1]
    param_lackRate = pop[:,6*DNA_SIZE:7*DNA_SIZE:1]
    param_sell_dist = pop[:,7*DNA_SIZE:8*DNA_SIZE:1]

    #pop:(POP_SIZE,DNA_SIZE)*(DNA_SIZE,1) --> (POP_SIZE,1)完成解码
    param_need = param_need.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]	
    param_buy_dist = param_buy_dist.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]	
    param_need_dist = param_need_dist.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]
    param_remainTime = param_remainTime.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]
    param_haveProduct = param_haveProduct.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]
    param_produce = param_produce.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]
    param_lackRate = param_lackRate.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]
    param_sell_dist = param_sell_dist.dot(2**np.arange(DNA_SIZE)[::-1])/float(2**DNA_SIZE-1)*(BOUND[1]-BOUND[0])+BOUND[0]

    return param_need,param_buy_dist,param_need_dist,param_remainTime,param_haveProduct,param_produce,param_lackRate,param_sell_dist

def get_fitness(pop,cmd:str): 
    """
    # 获取适应度(0-1之间,表示一个概率)
    """
    param_need,param_buy_dist,param_need_dist,param_remainTime,param_haveProduct,param_produce,param_lackRate,param_sell_dist = decodeDNA(pop)
    fitness = []
    for i in range(len(pop)):
        pred = F(cmd,param_need[i],param_buy_dist[i],param_need_dist[i],param_remainTime[i],param_haveProduct[i],param_produce[i],param_lackRate[i],param_sell_dist[i])
        fitness.append(pred)
    fitness = np.array(fitness)
    return fitness

def select(pop, fitness): 
    """
    # 自然选择,轮盘赌
    """
    # 复制最优？

    # nature selection wrt pop's fitness
    idx = np.random.choice(np.arange(POP_SIZE), size=POP_SIZE, replace=True,
                           p=(fitness)/(fitness.sum()) )
    return pop[idx]

def crossover_and_mutation(pop, CROSSOVER_RATE):
    """
    # 交叉和变异
    """
    new_pop = []
    for father in pop:		#遍历种群中的每一个个体，将该个体作为父亲
        child = father		#孩子先得到父亲的全部基因（这里我把一串二进制串的那些0，1称为基因）
        if np.random.rand() < CROSSOVER_RATE:			#产生子代时不是必然发生交叉，而是以一定的概率发生交叉
            mother = pop[np.random.randint(POP_SIZE)]	#再种群中选择另一个个体，并将该个体作为母亲
            for i in range(np.random.randint(6,9)): # 随机7-14个多点交叉
                cross_points = np.random.randint(low=0, high=DNA_SIZE*8) #随机产生交叉的点
                child[cross_points] = mother[cross_points] #孩子得到位于交叉点之间的母亲的基因
        mutation(child,MUTATION_RATE)	#每个后代有一定的机率发生变异
        mutation(child,MUTATION_RATE)	#每个后代有一定的机率发生变异
        mutation(child,MUTATION_RATE)	#每个后代有一定的机率发生变异
        new_pop.append(child)

    return np.array(new_pop)

def mutation(child, MUTATION_RATE):
    """
    # 变异
    """
    if np.random.rand() < MUTATION_RATE: 				#以MUTATION_RATE的概率进行变异
        mutate_point = np.random.randint(0, DNA_SIZE*8)	#随机产生一个实数，代表要变异基因的位置
        child[mutate_point] = child[mutate_point]^1 	#将变异点的二进制为反转

def generation(cmd:str):
    """
    # 遗传迭代
    """
    maxMoney = 0
    pop = np.random.randint(2, size=(POP_SIZE, DNA_SIZE*8)) #随机生成种群 matrix (POP_SIZE, DNA_SIZE)
    for _ in range(N_GENERATIONS):	#种群迭代进化N_GENERATIONS代
        new_pop = crossover_and_mutation(pop, CROSSOVER_RATE)	#种群通过交叉变异产生后代
        fitness = get_fitness(new_pop,cmd)	#对种群中的每个个体进行评估
        print(_,": ",max(fitness))
        
        money = max(fitness)
        if money > maxMoney:
            maxMoney = money
            maxIdx = np.argmax(fitness)
            param_need,param_buy_dist,param_need_dist,param_remainTime,param_haveProduct,param_produce,param_lackRate,param_sell_dist = decodeDNA(pop)
            Str = '#@@@\n        self.param_need = %f\n        self.param_buy_dist = %f\n        '\
                    'self.param_need_dist = %f\n        self.param_remainTime = %f\n        self.param_haveProduct = %f\n        '\
                    'self.param_produce = %f\n        self.param_lackRate = %f\n        '\
                    'self.param_sell_dist = %f\n#@@@\n' %(param_need[maxIdx] \
                    ,param_buy_dist[maxIdx],param_need_dist[maxIdx],param_remainTime[maxIdx],param_haveProduct[maxIdx] \
                    ,param_produce[maxIdx],param_lackRate[maxIdx],param_sell_dist[maxIdx])
            f = open('ttt.txt', "a")
            f.write(Str)
            f.write("maxMoney=%d\n"%(money))
            f.close()

        pop = select(new_pop, fitness) 	#选择生成新的种群
    return new_pop,fitness


if __name__ == "__main__":
    for i in range(4):
        cmd = 'robot -m maps/%d.txt -c ./SDK -f "python main.py"'%(i+1)
        f = open('ttt.txt', "a")
        f.write("第"+str(i+1)+"张地图\n")
        f.close()
        pop,fitness = generation(cmd)

        maxMoney = max(fitness)
        maxIdx = np.argmax(fitness)
        param_need,param_buy_dist,param_need_dist,param_remainTime,param_haveProduct,param_produce,param_lackRate,param_sell_dist = decodeDNA(pop)
        Str = '#@@@\n        self.param_need = %f\n        self.param_buy_dist = %f\n        '\
                    'self.param_need_dist = %f\n        self.param_remainTime = %f\n        self.param_haveProduct = %f\n        '\
                    'self.param_produce = %f\n        self.param_lackRate = %f\n        '\
                    'self.param_sell_dist = %f\n#@@@\n' %(param_need[maxIdx] \
                    ,param_buy_dist[maxIdx],param_need_dist[maxIdx],param_remainTime[maxIdx],param_haveProduct[maxIdx] \
                    ,param_produce[maxIdx],param_lackRate[maxIdx],param_sell_dist[maxIdx])
        f = open('ttt.txt', "a")
        f.write(Str)
        f.write("maxMoney=%d\n"%(maxMoney))
        f.write("fitness="+str(fitness)+"\n")
        f.close()
