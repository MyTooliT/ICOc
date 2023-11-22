import matplotlib.pyplot as plt
import numpy as np
import socket
import json

from logging import FileHandler, Formatter, getLogger
from pathlib import Path
from time import time

from mytoolit.utility.log import get_log_file_handler

cDict = {
    "Run": True,
    "Plot": False,
    "lineNameX": "",
    "lineNameY": "",
    "lineNameZ": "",
    "diagramName": "Signal Quality",
    "sampleInterval": 0,
    "figSizeX": 13,
    "figSizeY": 6,
    "X-Label": "time [s]",
    "Y-Label": "g",
    "timePoints": None,
    "dataBlockSize": 0,
    "xAccPoints": None,
    "yAccPoints": None,
    "zAccPoints": None,
    "Socket": None,
    "Connection": None,
    "TimeOutMs": 1500,
}


def tArray2Binary(array):
    strDict = json.dumps(array)
    strDict.encode("utf-8")
    binary = " ".join(format(ord(letter), "b") for letter in strDict)
    return binary.encode()


def tBinary2Array(tBinary):
    jsn = "".join(chr(int(x, 2)) for x in tBinary.split())
    msg = None
    try:
        msg = json.loads(jsn)
    except:
        pass
    return msg


def vHandeClose(evt):
    global cDict
    cDict["Run"] = False
    cDict["Plot"] = False


def tPlotterInit():
    global cDict

    # this is the call to matplotlib that allows dynamic plotting
    plt.ion()
    fig = plt.figure(figsize=(cDict["figSizeX"], cDict["figSizeY"]))
    ax = fig.add_subplot(111)
    fig.canvas.mpl_connect("close_event", vHandeClose)
    legendHandles = []
    legendName = []
    line1 = None
    line2 = None
    line3 = None
    # create a variable(s) for the line(s) so we can later update it
    if "" != cDict["lineNameX"]:
        (line1,) = ax.plot(
            cDict["timePoints"], cDict["xAccPoints"], alpha=0.8, label="x"
        )
        legendHandles.append(line1)
        legendName.append(cDict["lineNameX"])
    if "" != cDict["lineNameY"]:
        (line2,) = ax.plot(
            cDict["timePoints"], cDict["yAccPoints"], alpha=0.8, label="Y"
        )
        legendHandles.append(line2)
        legendName.append(cDict["lineNameY"])
    if "" != cDict["lineNameZ"]:
        (line3,) = ax.plot(
            cDict["timePoints"], cDict["zAccPoints"], alpha=0.8, label="Z"
        )
        legendHandles.append(line3)
        legendName.append(cDict["lineNameZ"])
    # update plot label/title
    plt.xlabel(cDict["X-Label"])
    plt.ylabel(cDict["Y-Label"])
    plt.legend(legendHandles, legendName)
    plt.title("{}".format(cDict["diagramName"]))
    plt.show()
    return [line1, line2, line3]


def sPloterSocketInit(iSocketPort):
    """
    Init Server Socket such that Clients may connect

    @param iSocketPort Socket Port to be opened

    @return
    """

    global cDict
    cDict["Socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger = getLogger()
    logger.debug("Created socket")
    cDict["Socket"].bind(
        ("", iSocketPort)  # Symbolic name meaning all available interfaces
    )
    logger.debug(f"Bound socket to port {iSocketPort}")
    cDict["Socket"].listen(1)
    logger.debug("Listening for connections")
    cDict["Connection"], _ = cDict["Socket"].accept()
    logger.debug("Accepted connection")


def vPlotterCommand(command, value):
    global cDict
    if command in {
        "dataBlockSize",
        "diagramName",
        "figSizeX",
        "figSizeY",
        "lineNameX",
        "lineNameY",
        "lineNameZ",
        "Plot",
        "Run",
        "sampleInterval",
        "xDim",
    }:
        cDict[command] = value
    if command == "diagramName" and cDict["Plot"]:
        plt.title("{}".format(cDict["diagramName"]))
    if command == "xDim":
        dataPoints = (
            1000 * cDict["dataBlockSize"] * value / cDict["sampleInterval"]
        )
        cDict["timePoints"] = np.linspace(0, value, int(dataPoints))
        cDict["xAccPoints"] = np.linspace(0, 0, int(dataPoints))
        cDict["yAccPoints"] = np.linspace(0, 0, int(dataPoints))
        cDict["zAccPoints"] = np.linspace(0, 0, int(dataPoints))


def vPlotter(iSocketPort, log_level):
    global cDict

    logger = getLogger(__name__)
    logger.setLevel(log_level)
    logger.addHandler(get_log_file_handler("plotter.log"))

    logger.info("Application started")
    sPloterSocketInit(iSocketPort)
    logger.info("Socket Initialized")
    while cDict["Run"] and not cDict["Plot"]:
        cmd = cDict["Connection"].recv(2**10)
        if cmd is None:
            continue
        cmd = tBinary2Array(cmd)
        if cmd is None:
            continue

        sCommand, tValue = cmd
        message = f"Initialization command: {sCommand}; value: {tValue}"
        logger.debug(message)
        logger.info(message)
        vPlotterCommand(sCommand, tValue)
        cDict["Connection"].sendall(tArray2Binary([sCommand, tValue]))
    logger.info("Configuration set")
    [line1, line2, line3] = tPlotterInit()
    logger.debug("Initialization done")
    logger.info("Configured")
    pauseTime = (1 / cDict["sampleInterval"]) / 4
    tLastTick = int(round(time()))
    logger.info("Drawing started")
    logger.debug("Waiting for sensor data")
    while cDict["Run"]:
        cmd = cDict["Connection"].recv(2**16)
        logger.debug("Received data")

        if cmd is None:
            timeout = cDict["TimeOutMs"] < int(round(time())) - tLastTick()
            if timeout:
                logger.error("Client time out")
                cDict["Run"] = False
                break

        tLastTick = int(round(time() * 1000))
        cmd = tBinary2Array(cmd)
        if cmd is None:
            continue

        sCommand, tValue = cmd
        if sCommand == "data":
            block_size = cDict["dataBlockSize"]
            cDict["xAccPoints"] = cDict["xAccPoints"][block_size:]
            cDict["yAccPoints"] = cDict["yAccPoints"][block_size:]
            cDict["zAccPoints"] = cDict["zAccPoints"][block_size:]
            cDict["xAccPoints"] = np.hstack([cDict["xAccPoints"], tValue["X"]])
            cDict["yAccPoints"] = np.hstack([cDict["yAccPoints"], tValue["Y"]])
            cDict["zAccPoints"] = np.hstack([cDict["zAccPoints"], tValue["Z"]])
            [line1, line2, line3] = vlivePlot(
                cDict["xAccPoints"],
                cDict["yAccPoints"],
                cDict["zAccPoints"],
                line1,
                line2,
                line3,
                pauseTime,
            )
        else:
            logger.info(
                f"Execute non-data command: {sCommand}; value: {tValue}"
            )
            vPlotterCommand(sCommand, tValue)

    logger.info("Closing connection ...")
    cDict["Connection"].close()
    logger.info("Connection closed")


def vlivePlot(yX_data, yY_data, yZ_data, line1, line2, line3, pause_time):
    # After the figure, axis, and line are created, we only need to update the
    # y-data
    update_bounds = False

    if None != line1:
        line1.set_ydata(yX_data)
        if (
            np.min(yX_data) <= line1.axes.get_ylim()[0]
            or np.max(yX_data) >= line1.axes.get_ylim()[1]
        ):
            update_bounds = True
    if None != line2:
        line2.set_ydata(yY_data)
        if (
            np.min(yY_data) <= line2.axes.get_ylim()[0]
            or np.max(yY_data) >= line2.axes.get_ylim()[1]
        ):
            update_bounds = True
    if None != line3:
        line3.set_ydata(yZ_data)
        if (
            np.min(yZ_data) <= line3.axes.get_ylim()[0]
            or np.max(yZ_data) >= line3.axes.get_ylim()[1]
        ):
            update_bounds = True

    # Adjust limits if new data goes beyond bounds
    if update_bounds:
        min_bound = min([
            value
            for value in (
                (
                    np.min(yX_data) - np.std(yX_data)
                    if yX_data is not None
                    else None
                ),
                (
                    np.min(yY_data) - np.std(yY_data)
                    if yY_data is not None
                    else None
                ),
                (
                    np.min(yZ_data) - np.std(yZ_data)
                    if yZ_data is not None
                    else None
                ),
            )
            if value is not None
        ])
        max_bound = max([
            value
            for value in (
                (
                    np.max(yX_data) + np.std(yX_data)
                    if yX_data is not None
                    else None
                ),
                (
                    np.max(yY_data) + np.std(yY_data)
                    if yY_data is not None
                    else None
                ),
                (
                    np.max(yZ_data) + np.std(yZ_data)
                    if yZ_data is not None
                    else None
                ),
            )
            if value is not None
        ])
        plt.ylim(min_bound, max_bound)

    # this pauses the data so the figure/axis can catch up - the amount of
    # pause can be altered above
    plt.pause(pause_time)

    # return line so we can update it again in the next iteration
    return [line1, line2, line3]
