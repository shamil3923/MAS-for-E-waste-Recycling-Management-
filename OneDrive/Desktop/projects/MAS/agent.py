from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.ModularVisualization import ModularServer
import random


# Define Agent Types
class CollectionAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.collected_waste = 0

    def step(self):
        if self.model.total_waste > 0:
            # Collect waste randomly, up to available waste
            collect = min(random.randint(1, 5), self.model.total_waste)
            self.collected_waste += collect
            self.model.total_waste -= collect


class SortingAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sorted_waste = 0

    def step(self):
        for agent in self.model.schedule.agents:
            if isinstance(agent, CollectionAgent) and agent.collected_waste > 0:
                # Sort a random amount of waste
                sorted_waste = random.randint(1, min(agent.collected_waste, 5))
                self.sorted_waste += sorted_waste
                agent.collected_waste -= sorted_waste


class RecyclingAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.recycled_waste = 0

    def step(self):
        for agent in self.model.schedule.agents:
            if isinstance(agent, SortingAgent) and agent.sorted_waste > 0:
                # Recycle a random amount of waste
                recycled = random.randint(1, min(agent.sorted_waste, 5))
                self.recycled_waste += recycled
                agent.sorted_waste -= recycled


# Define Model
class EWasteModel(Model):
    def __init__(self, width, height, num_collectors, num_sorters, num_recyclers, max_steps):
        super().__init__()
        self.current_id = 0  # Initialize unique ID counter
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.max_steps = max_steps
        self.current_step = 0
        self.total_waste = 100  # Simulating a total pool of waste

        # Add Collection Agents
        for i in range(num_collectors):
            collector = CollectionAgent(self.next_id(), self)
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            self.grid.place_agent(collector, (x, y))
            self.schedule.add(collector)

        # Add Sorting Agents
        for i in range(num_sorters):
            sorter = SortingAgent(self.next_id(), self)
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            self.grid.place_agent(sorter, (x, y))
            self.schedule.add(sorter)

        # Add Recycling Agents
        for i in range(num_recyclers):
            recycler = RecyclingAgent(self.next_id(), self)
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            self.grid.place_agent(recycler, (x, y))
            self.schedule.add(recycler)

        # Data Collector
        self.datacollector = DataCollector(
            {
                "Collected Waste": lambda m: sum(
                    agent.collected_waste
                    for agent in m.schedule.agents
                    if isinstance(agent, CollectionAgent)
                ),
                "Sorted Waste": lambda m: sum(
                    agent.sorted_waste
                    for agent in m.schedule.agents
                    if isinstance(agent, SortingAgent)
                ),
                "Recycled Waste": lambda m: sum(
                    agent.recycled_waste
                    for agent in m.schedule.agents
                    if isinstance(agent, RecyclingAgent)
                ),
                "Remaining Waste": lambda m: m.total_waste,
            }
        )

    def step(self):
        # Debugging: Print waste status at each step
        print(f"Step {self.current_step}: Total Waste = {self.total_waste}")

        if self.current_step >= self.max_steps:
            print("Simulation stopped: Max steps reached.")
            self.running = False
            return

        if self.total_waste <= 0:
            print("Simulation stopped: All waste processed.")
            self.running = False
            return

        # Simulate waste generation
        new_waste = random.randint(5, 10)  # Add some new waste each step
        self.total_waste += new_waste
        print(f"New waste generated: {new_waste}, Total Waste = {self.total_waste}")

        # Continue the simulation
        self.schedule.step()
        self.datacollector.collect(self)
        self.current_step += 1


# Agent portrayal for visualization
def agent_portrayal(agent):
    if isinstance(agent, CollectionAgent):
        return {"Shape": "rect", "Color": "yellow", "Filled": True, "w": 0.8, "h": 0.8, "Layer": 1}
    elif isinstance(agent, SortingAgent):
        return {"Shape": "circle", "Color": "blue", "Filled": True, "r": 0.8, "Layer": 1}
    elif isinstance(agent, RecyclingAgent):
        return {"Shape": "rect", "Color": "green", "Filled": True, "w": 0.8, "h": 0.8, "Layer": 1}


# Visualization setup
grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)
chart = ChartModule(
    [
        {"Label": "Collected Waste", "Color": "Yellow"},
        {"Label": "Sorted Waste", "Color": "Blue"},
        {"Label": "Recycled Waste", "Color": "Green"},
        {"Label": "Remaining Waste", "Color": "Red"},
    ]
)

model_params = {
    "width": 10,
    "height": 10,
    "num_collectors": UserSettableParameter("slider", "Number of Collection Agents", 5, 1, 10, 1),
    "num_sorters": UserSettableParameter("slider", "Number of Sorting Agents", 3, 1, 10, 1),
    "num_recyclers": UserSettableParameter("slider", "Number of Recycling Agents", 2, 1, 10, 1),
    "max_steps": UserSettableParameter("slider", "Max Steps", 200, 10, 200, 10),
}

server = ModularServer(
    EWasteModel, [grid, chart], "E-Waste Recycling Simulation", model_params
)
server.port = 8521

if __name__ == "__main__":
    server.launch()

