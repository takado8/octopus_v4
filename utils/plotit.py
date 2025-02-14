import matplotlib.pyplot as plt
from threading import Thread
import time

class LivePlotter:
    def __init__(self, title="Training Progress", xlabel="Iterations", ylabel="Value"):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xs = list(range(1, 1))  # Will be updated with new data
        self.ys = []  # To store the data for plotting
        self.fig, self.ax = plt.subplots()

    def plot(self, ys):
        # Update the data for plotting
        self.xs = list(range(1, len(ys) + 1))
        self.ys = ys

        # Clear the axes and plot new data
        self.ax.clear()
        self.ax.plot(self.xs, self.ys, label="Training Progress")
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.legend()
        # Draw a horizontal line at y = 0 (baseline)
        self.ax.axhline(y=0, color='black', linestyle='--', label="Baseline (y=0)")
        # Draw the updated plot and pause for a short time to allow the GUI to refresh

        # Add grid to the plot
        self.ax.grid(True)
        plt.draw()
        plt.pause(0.1)

    def save_plot(self, filename):

        plt.savefig(filename)


# Example Usage
# live_plotter = LivePlotter()
# for epoch in range(100):
#     ys = [some_values]  # Update this with actual data during training loop
#     live_plotter.plot(ys)
# live_plotter.save_plot('training_plot.png')
