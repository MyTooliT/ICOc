import matplotlib.pyplot as plt
import numpy as np




def tPlotterCommand(command, value, commandDict):
    if "Run" == command:
        commandDict["Run"] = value
    if "Plot" == command:
        commandDict["Plot"] = value
    if "xDim" == command:
        commandDict["timePoints"] = np.linspace(0, 1, value + 1)[0:-1],
        commandDict["xPoints"] = np.linspace(2 ** 15, 2 ** 15, value + 1)[0:-1],
        commandDict["yPoints"] = np.linspace(2 ** 15, 2 ** 15, value + 1)[0:-1],
        commandDict["zPoints"] = np.linspace(0, 1, value + 1)[0:-1],
    return commandDict
    
def vPlotter(x, commandQueue):
    plt.style.use('ggplot')
    commandDict = {
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
        "timePoints" : np.linspace(0, 1, 20 + 1)[0:-1],
        "xPoints" : np.linspace(2 ** 15, 2 ** 15, 20 + 1)[0:-1],
        "yPoints" : np.linspace(2 ** 15, 2 ** 15, 20 + 1)[0:-1],
        "zPoints" : np.linspace(0, 1, 20 + 1)[0:-1],
        "figSizeX" : 13,
        "figSizeY" : 6,
        "Y-Label" : "Acceleration",
    }

    line1 = [] 
    while False != commandDict["Run"]:
        if False == x.empty() and False != commandDict["Plot"]:
            commandDict["xPoints"][-1] = float(x.get())
            line1 = live_plotter(commandDict["timePoints"], commandDict["xPoints"], line1, commandDict["sampleInterval"], commandDict["diagramName"], commandDict["Y-Label"], commandDict["figSizeX"], commandDict["figSizeY"])
            commandDict["xPoints"] = np.append(commandDict["xPoints"][1:], 0.0)
        if False == commandQueue.empty():
            [command, value] = commandQueue.get()  
            commandDict = tPlotterCommand(command, value, commandDict) 
    print("Gui display closed")

        
def live_plotter(x_vec, y1_data, line1, pause_time, identifier='', AccXLabel="Acceleration", figSizeX=13, figSizeY=6):
    if line1 == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        fig = plt.figure(figsize=(figSizeX, figSizeY))
        ax = fig.add_subplot(111)
        # create a variable for the line so we can later update it
        line1, = ax.plot(x_vec, y1_data, '-o', alpha=0.8)        
        # update plot label/title
        plt.ylabel(AccXLabel)
        plt.title('Title: {}'.format(identifier))
        plt.show()
    
    # after the figure, axis, and line are created, we only need to update the y-data
    line1.set_ydata(y1_data)
    # adjust limits if new data goes beyond bounds
    if np.min(y1_data) <= line1.axes.get_ylim()[0] or np.max(y1_data) >= line1.axes.get_ylim()[1]:
        plt.ylim([np.min(y1_data) - np.std(y1_data), np.max(y1_data) + np.std(y1_data)])
   
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pause(pause_time)
    
    # return line so we can update it again in the next iteration
    return line1