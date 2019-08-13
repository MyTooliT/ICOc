import matplotlib.pyplot as plt
import numpy as np
from time import sleep

cDict = {
    "Run" : True,
    "Plot": False,
    "lineNameX" : "",
    "lineNameY" : "",
    "lineNameZ" : "",
    "diagramName" : "Acceleration",
    "sampleInterval" : 0,
    "figSizeX" : 13,
    "figSizeY" : 6,
    "X-Label" : "s",
    "Y-Label" : "",
    "timePoints" : None,
    "dataBlockSize" : 0,
    "xAccPoints" : None,
    "yAccPoints" : None,
    "zAccPoints" : None,
}


def vHandeClose(evt):
    global cDict
    cDict["Run"] = False
    cDict["Plot"] = False


def tPlotterInit():
    global cDict
    plt.style.use('ggplot')

    # this is the call to matplotlib that allows dynamic plotting
    plt.ion()
    fig = plt.figure(figsize=(cDict["figSizeX"], cDict["figSizeY"]))
    ax = fig.add_subplot(111)
    fig.canvas.mpl_connect('close_event', vHandeClose)
    legendHandles = []
    legendName = []
    line1 = None
    line2 = None
    line3 = None
    # create a variable(s) for the line(s) so we can later update it
    if "" != cDict["lineNameX"]:
        line1, = ax.plot(cDict["timePoints"], cDict["xAccPoints"], '-o', alpha=0.8, label='x')
        legendHandles.append(line1)  
        legendName.append(cDict["lineNameX"])   
    if "" != cDict["lineNameY"]:
        line2, = ax.plot(cDict["timePoints"], cDict["yAccPoints"], '-o', alpha=0.8, label='Y')
        legendHandles.append(line2)  
        legendName.append(cDict["lineNameY"])    
    if "" != cDict["lineNameZ"]:
        line3, = ax.plot(cDict["timePoints"], cDict["zAccPoints"], '-o', alpha=0.8, label='Z')
        legendHandles.append(line3)  
        legendName.append(cDict["lineNameZ"])
    # update plot label/title
    plt.xlabel(cDict["X-Label"])
    plt.ylabel(cDict["Y-Label"])
    plt.legend(legendHandles, legendName)
    plt.title('{}'.format(cDict["diagramName"]))
    plt.show()
    return [line1, line2, line3]

     
def vPlotterCommand(command, value):
    global cDict
    if "Run" == command:
        cDict[command] = value
    if "Plot" == command:
        cDict[command] = value
    if "diagramName" == command:
        cDict[command] = value
        if False != cDict["Plot"]:
            plt.title('{}'.format(cDict["diagramName"]))
    if "lineNameX" == command:
        cDict[command] = value
    if "lineNameY" == command:
        cDict[command] = value
    if "lineNameZ" == command:
        cDict[command] = value
    if "figSizeX" == command:
        cDict[command] = value
    if "figSizeY" == command:
        cDict[command] = value
    if "sampleInterval" == command:
        cDict[command] = value
    if "dataBlockSize" == command:
        cDict[command] = value
    if "xDim" == command:
        dataPoints = 1000*cDict["dataBlockSize"] * value / cDict["sampleInterval"]
        cDict["timePoints"] = np.linspace(0, value, dataPoints)
        cDict["xAccPoints"] = np.linspace(2 ** 15, 2 ** 15, dataPoints)
        cDict["yAccPoints"] = np.linspace(2 ** 15, 2 ** 15, dataPoints)
        cDict["zAccPoints"] = np.linspace(2 ** 15, 2 ** 15, dataPoints)

     
def vPlotter(valueQueue, commandQueue):
    global cDict
    
    while False != cDict["Run"] and False == cDict["Plot"]:
        if False == commandQueue.empty():
            [command, value] = commandQueue.get()  
            vPlotterCommand(command, value)
         
    [line1, line2, line3] = tPlotterInit()
    pauseTime = (1/cDict["sampleInterval"]) / 2
    while False != cDict["Run"]:
        if False == commandQueue.empty():
            [command, value] = commandQueue.get()  
            vPlotterCommand(command, value)
        elif False == valueQueue.empty():
            value = valueQueue.get()
#             dataPoints = len(cDict["timePoints"])
#             for i in range(0, dataPoints - cDict["dataBlockSize"]):
#                 pointCopyFrom = i + cDict["dataBlockSize"]
#                 cDict["xAccPoints"][i] = cDict["xAccPoints"][pointCopyFrom]
#                 cDict["yAccPoints"][i] = cDict["yAccPoints"][pointCopyFrom]
#                 cDict["zAccPoints"][i] = cDict["zAccPoints"][pointCopyFrom]

            cDict["xAccPoints"] = cDict["xAccPoints"][cDict["dataBlockSize"]:]
            cDict["yAccPoints"] = cDict["yAccPoints"][cDict["dataBlockSize"]:]
            cDict["zAccPoints"] = cDict["zAccPoints"][cDict["dataBlockSize"]:]
            cDict["xAccPoints"] = np.hstack([cDict["xAccPoints"], value['X']])
            cDict["yAccPoints"] = np.hstack([cDict["yAccPoints"], value['Y']])
            cDict["zAccPoints"] = np.hstack([cDict["zAccPoints"], value['Z']])
            [line1, line2, line3] = vlivePlot(cDict["xAccPoints"], cDict["yAccPoints"], cDict["zAccPoints"], line1, line2, line3, pauseTime)
        else:
            sleep(pauseTime/2)

    print("Gui display closed")

        
def vlivePlot(yX_data, yY_data, yZ_data, line1, line2, line3, pause_time):
    # after the figure, axis, and line are created, we only need to update the y-data
    if None != line1:
        line1.set_ydata(yX_data)
        # adjust limits if new data goes beyond bounds
        if np.min(yX_data) <= line1.axes.get_ylim()[0] or np.max(yX_data) >= line1.axes.get_ylim()[1]:
            plt.ylim([np.min(yX_data) - np.std(yX_data), np.max(yX_data) + np.std(yX_data)])
    if None != line2:
        line2.set_ydata(yY_data)
        # adjust limits if new data goes beyond bounds
        if np.min(yY_data) <= line2.axes.get_ylim()[0] or np.max(yY_data) >= line2.axes.get_ylim()[1]:
            plt.ylim([np.min(yY_data) - np.std(yY_data), np.max(yY_data) + np.std(yY_data)])
    if None != line3:
        line3.set_ydata(yZ_data)
        # adjust limits if new data goes beyond bounds
        if np.min(yZ_data) <= line3.axes.get_ylim()[0] or np.max(yZ_data) >= line3.axes.get_ylim()[1]:
            plt.ylim([np.min(yZ_data) - np.std(yZ_data), np.max(yZ_data) + np.std(yZ_data)])
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pause(pause_time)
    
    # return line so we can update it again in the next iteration
    return [line1, line2, line3]
