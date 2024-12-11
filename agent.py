from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.ModularVisualization import ModularServer
import random


class CollectionAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.collected_waste = 0

    def step(self):
        if self.model.total_waste > 0:
            collect = min(random.randint(1, 5), self.model.total_waste)
            if self.model.total_waste <= 5:
                collect = self.model.total_waste
            self.collected_waste += collect
            self.model.total_waste -= collect
            self.model.logger.append(f"CollectionAgent {self.unique_id} collected {collect} units of waste.")
        self.random_move()

    def random_move(self):
        possible_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_moves)
        self.model.grid.move_agent(self, new_position)


class SortingAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sorted_waste = 0

    def step(self):
        for agent in self.model.schedule.agents:
            if isinstance(agent, CollectionAgent) and agent.collected_waste > 0:
                sorted_waste = random.randint(1, min(agent.collected_waste, 5))
                if agent.collected_waste <= 5:
                    sorted_waste = agent.collected_waste
                self.sorted_waste += sorted_waste
                agent.collected_waste -= sorted_waste
                self.model.logger.append(f"SortingAgent {self.unique_id} sorted {sorted_waste} units of waste from CollectionAgent {agent.unique_id}.")
        self.random_move()

    def random_move(self):
        possible_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_moves)
        self.model.grid.move_agent(self, new_position)


class RecyclingAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.recycled_waste = 0

    def step(self):
        for agent in self.model.schedule.agents:
            if isinstance(agent, SortingAgent) and agent.sorted_waste > 0:
                recycled = random.randint(1, min(agent.sorted_waste, 5))
                if agent.sorted_waste <= 5:
                    recycled = agent.sorted_waste
                self.recycled_waste += recycled
                agent.sorted_waste -= recycled
                self.model.logger.append(f"RecyclingAgent {self.unique_id} recycled {recycled} units of waste from SortingAgent {agent.unique_id}.")
        self.random_move()

    def random_move(self):
        possible_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_moves)
        self.model.grid.move_agent(self, new_position)


class EWasteModel(Model):
    def __init__(self, width, height, num_collectors, num_sorters, num_recyclers, max_steps):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.max_steps = max_steps
        self.current_step = 0
        self.total_waste = 100
        self.logger = []

        for i in range(1, num_collectors + 1):
            collector = CollectionAgent(i, self)
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            self.grid.place_agent(collector, (x, y))
            self.schedule.add(collector)

        for i in range(num_collectors + 1, num_collectors + num_sorters + 1):
            sorter = SortingAgent(i, self)
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            self.grid.place_agent(sorter, (x, y))
            self.schedule.add(sorter)

        for i in range(num_collectors + num_sorters + 1, num_collectors + num_sorters + num_recyclers + 1):
            recycler = RecyclingAgent(i, self)
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            self.grid.place_agent(recycler, (x, y))
            self.schedule.add(recycler)

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
        self.logger.append(f"--- Step {self.current_step + 1} ---")
        self.logger.append(f"Total Waste at Start: {self.total_waste}")

        if self.current_step >= self.max_steps or self.total_waste <= 0:
            if self.current_step >= self.max_steps:
                self.logger.append("Simulation stopped: Max steps reached.")
            if self.total_waste <= 0:
                self.logger.append("Simulation stopped: All waste processed.")
            self.running = False
            print("\n".join(self.logger))  # Print all logs to the console
            return

        if self.total_waste > 5:
            new_waste = random.randint(5, 10)
            self.total_waste += new_waste
            self.logger.append(f"New waste generated: {new_waste}")

        self.schedule.step()
        self.datacollector.collect(self)
        self.logger.append(f"Summary: Total Waste Remaining = {self.total_waste}")
        self.logger.append(f"------------------------")

        print("\n".join(self.logger))  # Print all logs to the console
        self.current_step += 1


class LogElement(TextElement):
    def __init__(self):
        super().__init__()

    def render(self, model):
        # Extract specific logs for UI display
        ui_logs = [log for log in model.logger if "Summary: Total Waste Remaining" in log or "Simulation stopped" in log]
        return "<br>".join(ui_logs)


def agent_portrayal(agent):
    portrayal = {"Filled": True, "Layer": 1}
    if isinstance(agent, CollectionAgent):
        portrayal["Shape"] = "rect"
        portrayal["Color"] = "orange" if agent.collected_waste > 0 else "yellow"
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
        portrayal["text"] = str(agent.collected_waste)  # Show collected waste
        portrayal["text_color"] = "black"
    elif isinstance(agent, SortingAgent):
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "darkblue" if agent.sorted_waste > 0 else "blue"
        portrayal["r"] = 0.8
        portrayal["text"] = str(agent.sorted_waste)  # Show sorted waste
        portrayal["text_color"] = "white"
    elif isinstance(agent, RecyclingAgent):
        portrayal["Shape"] = "rect"
        portrayal["Color"] = "darkgreen" if agent.recycled_waste > 0 else "green"
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
        portrayal["text"] = str(agent.recycled_waste)  # Show recycled waste
        portrayal["text_color"] = "white"
    return portrayal


grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)
chart = ChartModule(
    [
        {"Label": "Collected Waste", "Color": "Yellow"},
        {"Label": "Sorted Waste", "Color": "Blue"},
        {"Label": "Recycled Waste", "Color": "Green"},
        {"Label": "Remaining Waste", "Color": "Red"},
    ]
)
log_element = LogElement()

model_params = {
    "width": 10,
    "height": 10,
    "num_collectors": UserSettableParameter("slider", "Number of Collection Agents", 5, 1, 10, 1),
    "num_sorters": UserSettableParameter("slider", "Number of Sorting Agents", 3, 1, 10, 1),
    "num_recyclers": UserSettableParameter("slider", "Number of Recycling Agents", 2, 1, 10, 1),
    "max_steps": UserSettableParameter("slider", "Max Steps", 200, 10, 200, 10),
}

server = ModularServer(
    EWasteModel, [grid, chart, log_element], "E-Waste Recycling Simulation", model_params
)
server.port = 8522

if __name__ == "__main__":
    server.launch()
