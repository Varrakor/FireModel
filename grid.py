from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import math
import random
import matplotlib.pyplot as plt
import numpy as np

# Define the Agent class for Trees
class TreeAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.on_fire = False

    def step(self):
        if self.on_fire:
            print("fire step")
            # Get the current location of the tree
            x, y = self.pos

            # Define adjacent cell offsets (assuming 4 neighbors)
            neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

            # Shuffle the list of neighbors randomly
            random.shuffle(neighbors)
            print("neighbours of fire")
            print(neighbors)

            # Ignite up to two random adjacent cells
            ignited = 0
            for neighbor_x, neighbor_y in neighbors:
                if 0 <= neighbor_x < self.model.grid.width and 0 <= neighbor_y < self.model.grid.height:
                    if ignited < 1 and not self.model.grid.is_cell_empty((neighbor_x, neighbor_y)):
                        self.model.ignite_tree(neighbor_x, neighbor_y)
                        print("fire spread")
                        ignited += 1
            print("end fire step")

# Define the Agent class for Firefighters
class FirefighterAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.target_tree = None

    def step(self):
        print("firefighter step")

        # Find the nearest tree on fire
        nearest_fire_tree = self.find_nearest_fire_tree()

        if nearest_fire_tree:
            # Move to the nearest tree on fire
            self.move_to_tree(nearest_fire_tree)

            # Extinguish the fire and remove the tree from the grid
            self.extinguish_and_remove_tree(nearest_fire_tree)

    def find_nearest_fire_tree(self):
        fire_trees = []

        # Iterate over all cells in the grid
        for x in range(self.model.grid.width):
            for y in range(self.model.grid.height):
                cell_contents = self.model.grid.get_cell_list_contents([(x, y)])
                for agent in cell_contents:
                    if isinstance(agent, TreeAgent) and agent.on_fire:
                        fire_trees.append(agent)

        if fire_trees:
            # Calculate distances to all fire trees
            distances = [self.distance_to_tree(tree) for tree in fire_trees]

            # Find the nearest fire tree
            nearest_index = distances.index(min(distances))
            return fire_trees[nearest_index]

        return None
    

    def distance_to_tree(self, tree):
        return manhattan_distance(self.pos, tree.pos)

    def move_to_tree(self, tree):
        # Move to the location of the target tree
        self.model.grid.move_agent(self, tree.pos)
    
    def extinguish_and_remove_tree(self, tree):
        # Extinguish the fire in the tree
        tree.on_fire = False

        # Remove the tree from the grid and the scheduler
        self.model.grid.remove_agent(tree)
        self.model.schedule.remove(tree)
        
                
# Inside the BushfireModel class
class BushfireModel(Model):
    def __init__(self, width, height, tree_density, num_firefighters):
        self.num_agents = width * height
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        # Create and place Tree agents based on tree_density
        for i in range(width):
            for j in range(height):
                if random.random() < tree_density:
                    tree = TreeAgent(self.random.randint(1, 1e6), self)
                    self.grid.place_agent(tree, (i, j))
                    self.schedule.add(tree)

        # # Create and place Firefighter agents
        # for i in range(num_firefighters):
        #     x = random.randrange(self.grid.width)
        #     y = random.randrange(self.grid.height)
        #     firefighter = FirefighterAgent(self.random.randint(1, 1e6), self)
        #     self.grid.place_agent(firefighter, (x, y))
        #     self.schedule.add(firefighter)

        # Define data collectors for model output
        self.datacollector = DataCollector(agent_reporters={"On Fire": lambda a: a.on_fire if isinstance(a, TreeAgent) else None})
        
    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

    # Method to ignite a tree at a specified location
    def ignite_tree(self, x, y):
        cell_contents = self.grid.get_cell_list_contents([(x, y)])
        for agent in cell_contents:
            if isinstance(agent, TreeAgent):
                agent.on_fire = True
                print("ignited fire")
    
    # Method to extinguish a fire at a specified location
    def extinguish_tree_fire(self, x, y):
        cell_contents = self.grid.get_cell_list_contents([(x, y)])
        for agent in cell_contents:
            if isinstance(agent, TreeAgent) and agent.on_fire:
                agent.on_fire = False
                
def manhattan_distance(point1, point2):
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

# Define a function to visualize the model's state
def visualize(model):
    grid_state = {"Empty": 0, "Tree": 1, "Firefighter": 2}
    width = model.grid.width
    height = model.grid.height

    grid_matrix = np.zeros((height, width))

    for x in range(width):
        for y in range(height):
            cell_contents = model.grid.get_cell_list_contents([(x, y)])

            if any(isinstance(agent, TreeAgent) for agent in cell_contents):
                grid_matrix[y][x] = grid_state["Tree"]
            elif any(isinstance(agent, FirefighterAgent) for agent in cell_contents):
                grid_matrix[y][x] = grid_state["Firefighter"]
            else:
                grid_matrix[y][x] = grid_state["Empty"]

    plt.imshow(grid_matrix, cmap="cool", interpolation="none")
    plt.colorbar(ticks=[0, 1, 2], label='Agent Type (0: Empty, 1: Tree, 2: Firefighter)')
    plt.title("Bushfire Simulation")
    plt.show()
    
    
# Create and run the model
width = 5
height = 5
tree_density = 1
num_firefighters = 1

model = BushfireModel(width, height, tree_density, num_firefighters)

# Input phase
while True:  # Keep taking input until "start" is entered
    user_input = input("Enter 'fire x, y' to start a fire, 'extinguish x, y' to put out a fire, or 'start' to begin the simulation: ")
    
    if user_input.strip().lower() == "start":
        break  # Exit the input loop and start the simulation
    
    try:
        command, x, y = user_input.strip().split()
        x, y = int(x), int(y)
        if command.lower() == "fire":
            model.ignite_tree(x, y)
        elif command.lower() == "extinguish":
            firefighter = FirefighterAgent(model.random.randint(1, 1e6), model)
            model.grid.place_agent(firefighter, (x, y))
            model.schedule.add(firefighter)
        else:
            print("Invalid command. Please enter 'fire x, y', 'extinguish x, y', or 'start'.")
    except ValueError:
        print("Invalid input format. Please enter commands as 'fire x, y', 'extinguish x, y', or 'start'.")

# Simulation phase
num_steps = 5  # Adjust the number of steps as needed
for i in range(num_steps):
    model.step()

    # Initialize a 2D grid to store cell states
    grid_width = model.grid.width
    grid_height = model.grid.height
    grid = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]

    # Loop through agents to update the grid
    for agent in model.schedule.agents:
        x, y = agent.pos

        # Set the symbol based on agent type and state
        if isinstance(agent, TreeAgent):
            if agent.on_fire:
                grid[y][x] = 'F'  # Tree on fire
            else:
                grid[y][x] = 'T'  # Tree not on fire
        elif isinstance(agent, FirefighterAgent):
            grid[y][x] = 'E'  # Firefighter

    # Print the grid
    for row in grid:
        print(' '.join(row))