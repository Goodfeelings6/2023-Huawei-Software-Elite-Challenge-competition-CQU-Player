import math
import numpy as np
import matplotlib.pyplot as plt
x_i,y_i = 6,2
x_j,y_j = 15,40
theta1 = math.pi / 4

def fun(theta1):
    x_i_bar = (x_j-x_i) * math.cos(theta1) - (y_j-y_i) * math.sin(theta1) + x_i
    y_i_bar = (x_j-x_i) * math.sin(theta1) + (y_j-y_i) * math.cos(theta1) + y_i
    x_i_bar =  (x_i_bar - x_i) / (2 * math.cos(theta1)) + x_i
    y_i_bar =  (y_i_bar - y_i) / (2 * math.cos(theta1)) + y_i
    return x_i_bar,y_i_bar

x1,y1 = fun(theta1)
x2,y2 = fun(-theta1)
x = [x_i,x_j,x1,x2]
y = [y_i,y_j,y1,y2]
plt.scatter(x,y)
plt.show()