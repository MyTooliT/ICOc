import matplotlib.pyplot as plt
import numpy as np

cDict = {
    "Run" : True,
    "Plot": False,
    "Axis" : 0,
    "Interval" : 0,
    "PacketLoss" : 0,
    "lineNameX" : "",
    "lineNameY" : "",
    "lineNameZ" : "",
    "diagramName" : "Acceleration",
    "sampleInterval" : 0.025,
    "figSizeX" : 13,
    "figSizeY" : 6,
    "X-Label" : "ms",
    "Y-Label" : "",
    "timePoints" : np.linspace(0, 4000, 20 + 1)[0:-1],
    "xAccPoints" : np.linspace(2 ** 15, 2 ** 15, 20 + 1)[0:-1],
    "yAccPoints" : np.linspace(2 ** 15, 2 ** 15, 20 + 1)[0:-1],
    "zAccPoints" : np.linspace(0, 1, 20 + 1)[0:-1],
}

def tPlotterInit():
    global cDict
    plt.style.use('ggplot')

    # this is the call to matplotlib that allows dynamic plotting
    plt.ion()
    fig = plt.figure(figsize=(cDict["figSizeX"], cDict["figSizeY"]))
    ax = fig.add_subplot(111)
    # create a variable for the line so we can later update it
    line1, = ax.plot(cDict["timePoints"], cDict["xAccPoints"], '-o', alpha=0.8)        
    # update plot label/title
    plt.xlabel(cDict["X-Label"])
    plt.ylabel(cDict["Y-Label"])
    plt.title('Title: {}'.format(cDict["diagramName"]))
    plt.show()
    return line1
     
def vPlotterCommand(command, value):
    global cDict
    if "Run" == command:
        cDict["Run"] = value
    if "Plot" == command:
        cDict["Plot"] = value
    if "diagramName" == command:
        cDict["diagramName"] = value
        if False != cDict["Plot"]:
            plt.title('{}'.format(cDict["diagramName"]))
    if "xDim" == command:
        cDict["timePoints"] = np.linspace(0, cDict["sampleInterval"]*value, value + 1)[0:-1],
        cDict["xPoints"] = np.linspace(2 ** 15, 2 ** 15, value + 1)[0:-1],
        cDict["yPoints"] = np.linspace(2 ** 15, 2 ** 15, value + 1)[0:-1],
        cDict["zPoints"] = np.linspace(0, 1, value + 1)[0:-1],

     
def vPlotter(x, commandQueue):
    global cDict
    
    line1 = tPlotterInit()
    while False != cDict["Run"]:
        if False == x.empty() and False != cDict["Plot"]:
            cDict["xAccPoints"][-1] = float(x.get())
            line1 = vlivePlot(cDict["xAccPoints"], line1, cDict["sampleInterval"])
            cDict["xAccPoints"] = np.append(cDict["xAccPoints"][1:], 0.0)
        if False == commandQueue.empty():
            [command, value] = commandQueue.get()  
            vPlotterCommand(command, value)
    print("Gui display closed")

        
def vlivePlot(y1_data, line1, pause_time):
    # after the figure, axis, and line are created, we only need to update the y-data
    line1.set_ydata(y1_data)
    # adjust limits if new data goes beyond bounds
    if np.min(y1_data) <= line1.axes.get_ylim()[0] or np.max(y1_data) >= line1.axes.get_ylim()[1]:
        plt.ylim([np.min(y1_data) - np.std(y1_data), np.max(y1_data) + np.std(y1_data)])
   
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pause(pause_time)
    
    # return line so we can update it again in the next iteration
    return line1