import warnings
warnings.filterwarnings('ignore')

# Standard imports for data manipulation and visualization
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# OpenLane-V2 specific imports for lane segment processing
from openlanev2.lanesegment.io import io
from openlanev2.lanesegment.preprocessing import collect
from openlanev2.lanesegment.dataset import Collection
from openlanev2.lanesegment.visualization import draw_annotation_bev, assign_attribute, assign_topology

# Graph processing imports
import networkx as nx
import heapq

LOG = False

class Exploration:
    """
    Main class for exploring and processing OpenLane-V2 dataset frames.
    Handles data loading, annotation processing, and visualization of lane segments.
    """

    def __init__(self, root_path):
        """
        Initialize exploration with dataset path and prepare lane segment data
        Args:
            root_path (str): Path to the dataset root directory
        """
        data_dict = io.json_load(f'{root_path}/data_dict_sample.json')
        collect(
            root_path, 
            data_dict, 
            'data_dict_sample_ls', 
            n_points={
                'area': 20,
                'centerline': 2,
                'left_laneline': 20,
                'right_laneline': 20,
            }
        )

        self.collection = Collection(root_path, root_path, 'data_dict_sample_ls')

        self.map_connection        = dict() # Connection relations between each node
        self.map_position          = dict() # Postion map of each node
        self.map_relative_position = dict() # Postion relative map of each node
        self.start_pos             = list()

    def get_annotation_with_attribute(self, frame):
        """
        Process frame annotations with attributes and topology
        Args:
            frame: Dataset frame object
        Returns:
            dict: Processed annotations with attributes
        """
        annotations = frame.get_annotations()
        annotations = assign_attribute(annotations)
        annotations = assign_topology(annotations)
        return annotations # return assgigned annotations for node links

    def get_annotation_from_id(self, frame, id):
        """
        Retrieve specific annotation by ID from frame
        Args:
            frame: Dataset frame object
            id: Target annotation ID
        Returns:
            dict: Annotation data for specified ID
        """
        for f in frame.get_annotations_lane_segments(): # Go thru the frame ids to return the correct annotations lane segment
            if f["id"] == id:
                return f
        return 1

    def get_id_connection(self, frame):
        """
        Build connectivity map between lane segments
        Args:
            frame: Dataset frame object
        Returns:
            dict: Mapping of lane segment IDs to their connections
        """
        annotations = self.get_annotation_with_attribute(frame)

        id_position = dict() # Give position for a given id
        id_ls       = dict() # Give all the link for a given id

        for i, ls in enumerate(annotations["lane_segment"]):
            # Going thru all the frames annotation to get the id
            id_position[ls["id"]] = i

        for i, lsls in enumerate(annotations['topology_lsls']):
            # Going thru all the topology ls/ls to get the links
            id       = annotations["lane_segment"][i]["id"]
            lsls_pos = np.argwhere(lsls == 1) # Find the position related to the current id ls

            if len(lsls_pos) != 0 :
                lsls_id = list()
                for connection_pos in lsls_pos.reshape(1,-1):
                    # Going thru all the possible connection possible
                    lsls_id.append(annotations["lane_segment"][connection_pos[0]]["id"])
                id_ls[id] = lsls_id
            else:
                id_ls[id] = None

        return id_ls

    def update_pos(self, frame, k):
        """
        Update position maps for a given lane segment
        Args:
            frame: Dataset frame object
            k: Lane segment ID
        """
        annotation = self.get_annotation_from_id(frame, k) # Get the correct annotation for the given frame and id
        pos, _ = annotation["centerline"]   # Recover the centerline position
        self.map_position[k] = pos[:2]+frame.meta["pose"]["translation"][:2]     # Update the node position
        self.map_relative_position[k] = pos[:2] # Update the node position

    def update_map_connection(self, frame):
        """
        Update the global connectivity map with new frame data
        Args:
            frame: Dataset frame object
        """
        id_ls = self.get_id_connection(frame) # Get the current frame connections

        for k in id_ls.keys():
            if k not in self.map_connection.keys():
                # If the node is not added yet
                self.map_connection[k] = id_ls[k]
                self.update_pos(frame, k)

            else:
                # Else the node is already in the dict
                if id_ls[k] != None:
                    for v in id_ls[k]:
                        if self.map_connection[k]!=None:
                            if v != None :
                                if v not in self.map_connection[k] :
                                    # Add the connection if not already here
                                    self.map_connection[k].append(v)
                                    self.update_pos(frame, k)
                        else:
                            # Else the node value is not added yet
                            self.map_connection[k] = [str(k)]
                            self.update_pos(frame, k)

    def plot_frame(self, frame, show_plot=False):
        """
        Visualize frame data including camera views and BEV map
        Args:
            frame: Dataset frame object
            show_plot (bool): Whether to display the plot immediately
        """
        seq = str(frame.meta['segment_id'])     # Get the Seq id
        pos = frame.meta["pose"]["translation"] # Get position of the car

        cameras = frame.get_camera_list()
        camera_layout = {                   #Gives the position of the images view
            "ring_front_left": (0, 0),
            "ring_front_center": (0, 1),
            "ring_front_right": (0, 2),
            "ring_side_left": (1, 0),
            "ring_side_right": (1, 2),
            "ring_rear_left": (2, 0),
            "ring_rear_right": (2, 2)
        }

        fig, axes   = plt.subplots(3, 3, figsize=(10, 9))
        gs          = GridSpec(3, 3, figure=fig)
        axes_dict   = {}

        annotations = self.get_annotation_with_attribute(frame) # Get annotaions for map

        for camera, (row, col) in camera_layout.items():
            axes_dict[camera] = fig.add_subplot(gs[row, col])
            axes_dict[camera].axis("off")

        image_bev_centerline_laneline = draw_annotation_bev(
            annotations, 
            with_attribute=False,
            with_linetype=False,
            with_centerline=True,  # Only the centerline for vizualising
            with_laneline=False,
            with_area=False,
        )

        relative_x, relative_y = image_bev_centerline_laneline.shape[:2] # Get relative point for scatter the car
        relative_x = relative_x // 2
        relative_y = relative_y // 2

        # Map plot
        axes_bev = fig.add_subplot(gs[1:3, 1])
        axes_bev.scatter(relative_y, relative_x, c='red')
        axes_bev.imshow(image_bev_centerline_laneline)
        axes_bev.axis("off")

        for ax_row in axes:
            for ax in ax_row:
                ax.axis("off")

        # Views plot
        for camera in cameras:
            if camera in camera_layout:
                row, col = camera_layout[camera]
                image = frame.get_rgb_image(camera)
                axes[row, col].imshow(image)
                axes[row, col].set_title(camera)
                axes[row, col].axis("off")

        plt.suptitle(f"Sequence {seq} - Timestamp {frame.meta['timestamp']} - Position ({pos[0]}, {pos[1]})")
        plt.tight_layout()
        if show_plot:
            plt.show()

    def plot_constellation(self, node_start=None, node_goal=None, list_path=None, show_plot=False):
        """
        Visualize the node graph constellation with optional path highlighting
        Args:
            node_start: Starting node ID
            node_goal: Goal node ID
            list_path: List of node IDs forming a path
            show_plot (bool): Whether to display the plot immediately
        """
        G = nx.DiGraph()  # Graph to display the nodes interactions

        # Build the graph edges
        for node, successors in self.map_connection.items():
            if successors is not None:
                for succ in successors:
                    if node in self.map_relative_position and succ in self.map_relative_position:
                        G.add_edge(node, succ)

        # Get the nodes position for visual
        pos = {node: (-coords[1], coords[0]) for node, coords in self.map_relative_position.items()}

        plt.figure(figsize=(6, 9))

        # 1. Draw all nodes (light blue) and all edges first (background layer)
        nx.draw(
            G, pos,
            with_labels=True,
            node_size=1000,
            node_color="lightblue",
            arrowsize=20,
            font_size=6,
        )

        # 2. Draw path edges (orange, on top of background)
        if list_path is not None and len(list_path) > 1:
            path_edges = [(list_path[i], list_path[i + 1]) for i in range(len(list_path) - 1)]
            nx.draw_networkx_edges(
                G, pos,
                edgelist=path_edges,
                edge_color="orange",
                width=3,
                arrows=True
            )

        # 3. Draw start node (green, larger, on top)
        if node_start is not None and node_start in G.nodes:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=[node_start],
                node_color="green",
                node_size=1200,
                linewidths=2
            )

        # 4. Draw goal node (red, larger, on top)
        if node_goal is not None and node_goal in G.nodes:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=[node_goal],
                node_color="red",
                node_size=1200,
                linewidths=2
            )

        plt.title("Nodes relationship")
        if show_plot:
            plt.show()
        return

    def clean_nodes(self, delta=0.01):
        """
        Clean and consolidate nearby nodes in the graph
        Args:
            delta (float): Distance threshold for node fusion
        """
        # Remove self-loops
        for k in list(self.map_connection.keys()):
            if self.map_connection[k] is not None and k in self.map_connection[k]:
                self.map_connection[k].remove(k)

        # Fusion nodes
        to_remove = set()
        replacements = {}

        nodes = list(self.map_position.keys())
        for i in range(len(nodes)):
            if nodes[i] in to_remove:
                continue
            for j in range(i + 1, len(nodes)):
                if nodes[j] in to_remove:
                    continue
                pos_i = self.map_position[nodes[i]]
                pos_j = self.map_position[nodes[j]]
                dist = np.linalg.norm(pos_i - pos_j)

                if dist <= delta:  # identical or nearby
                    # Fuse j into i
                    replacements[nodes[j]] = nodes[i]
                    to_remove.add(nodes[j])

                    # Merge connections
                    if self.map_connection[nodes[i]] is None:
                        self.map_connection[nodes[i]] = []
                    if self.map_connection[nodes[j]] is not None:
                        self.map_connection[nodes[i]].extend(self.map_connection[nodes[j]])

        for k, v in self.map_connection.items():
            if v is not None:
                self.map_connection[k] = [replacements.get(n, n) for n in v]

        for n in to_remove:
            self.map_connection.pop(n, None)
            self.map_position.pop(n, None)

        for k, v in self.map_connection.items():
            if v is not None:
                self.map_connection[k] = list(set(v))

    def start_exploration(self, seq):
        """
        Begin dataset exploration for specified sequence
        Args:
            seq (int): Sequence number to process
        Returns:
            Frame object: Last processed frame
        """
        if seq == 1:
            range_seq = range(32)
        elif seq == 2:
            range_seq = range(32, 64)
        elif seq == 3:
            range_seq = range(64, 96)
        else:
            print("Sequence Unknown")
            return 1

        _, frame_start = self.collection.get_frame_via_index(range_seq[0])
        self.start_pos = frame_start.meta["pose"]["translation"][:2]

        for f in range_seq:
            _, frame = self.collection.get_frame_via_index(f)
            self.update_map_connection(frame)

            if LOG:
                print(f'\n\nFrame : {f}')
                for k in self.map_connection.keys():
                    print(f"{k} : {self.map_connection[k]}")

        last_frame = frame

        self.clean_nodes()

        return last_frame

class PathFinder(Exploration):
    """
    Path finding functionality extending the Exploration class.
    Implements A* algorithm for optimal path finding between nodes.
    """

    def __init__(self, root_path, seq):
        """
        Initialize pathfinder with dataset and sequence
        Args:
            root_path (str): Path to dataset
            seq (int): Sequence number to process
        """
        super().__init__(root_path=root_path)
        self.start_exploration(seq)

        target_list = {
            "00000" : [1543, 248],
            "00029" : [738, 2673],
            "00388" : [1101, 86]
        }

        if seq == 1:
            self.goal_pos=target_list["00388"] 
        elif seq == 2:
            self.goal_pos=target_list["00029"]
        elif seq == 3 :
            self.goal_pos=target_list["00000"] 

    def build_graph(self):
        """
        Construct weighted graph from node connections
        Returns:
            dict: Graph structure with nodes and weighted edges
        """
        graph = {}
        for node, successors in self.map_connection.items():
            if successors is None:
                continue
            graph[node] = []
            for succ in successors:
                # Only add edge if both nodes are in the explored map
                if succ in self.map_position and node in self.map_position:
                    pos1, pos2 = self.map_position[node], self.map_position[succ]
                    cost = np.linalg.norm(pos1 - pos2)  # Euclidean distance as weight
                    graph[node].append((succ, cost))
        return graph

    def get_closest_node(self, pos):
        """
        Find nearest node to given position
        Args:
            pos: Target position coordinates
        Returns:
            str: ID of closest node
        """
        closest_node = None
        min_dist     = float("inf")

        for id, node_pos in self.map_position.items():
            dist = np.linalg.norm(node_pos - pos) # Euclidean norm for the closest point
            if dist < min_dist: # Get the ID of the closest point
                min_dist     = dist
                closest_node = id

        return closest_node

    def heuristic(self, node):
        """
        Calculate heuristic distance for A* algorithm
        Args:
            node: Node ID
        Returns:
            float: Estimated distance to goal
        """
        return np.linalg.norm(self.map_position[self.goal_node] - self.map_position[node])

    def A_star(self):
        """
        Implement A* pathfinding algorithm
        Returns:
            list: Sequence of node IDs forming optimal path
        """
        # Find the closest nodes to the start and goal positions
        self.start_node = self.get_closest_node(self.start_pos)
        self.goal_node  = self.get_closest_node(self.goal_pos)
        print(f"\nStarting at node {self.start_node} ({int(self.start_pos[0])}, {int(self.start_pos[1])}) to node {self.goal_node} ({self.goal_pos[0]}, {self.goal_pos[1]})")

        # Get the weighted graph
        graph = self.build_graph()

        # Initialize the open list as a priority queue (min-heap) for A*
        open_list = []
        # Push the start node with its heuristic value (estimated cost to goal)
        heapq.heappush(open_list, (self.heuristic(self.start_node), self.start_node))
        # Dictionary to track the best previous node for each visited node
        came_from = {}
        # Cost from start node to each node (g_score)
        g_score = {self.start_node: 0}

        # Main A* search loop
        while open_list:
            # Pop the node with the lowest f-score (g + h)
            f, current = heapq.heappop(open_list)

            # If the goal is reached, reconstruct the path
            if current == self.goal_node:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(self.start_node)
                return path[::-1]  # Return reversed path from start to goal

            # Explore neighbors of the current node
            for neighbor, cost in graph.get(current, []):
                tentative_g = g_score[current] + cost  # Calculate tentative g-score
                # If this path to neighbor is better than any previous one
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor)  # f = g + h
                    heapq.heappush(open_list, (f_score, neighbor))    # Add neighbor to open list
                    came_from[neighbor] = current                    # Track path

        # If no path is found, return None
        return None

if __name__ == '__main__':
    # Example of usage
    root_path = "./dataset/"
    sequence = 2

    pf = PathFinder(root_path, sequence)
    best_path = pf.A_star()

    pf.plot_constellation(node_start=pf.start_node, node_goal=pf.goal_node, list_path=best_path, show_plot=False)

    _, frame = pf.collection.get_frame_via_index(sequence*32-31)
    pf.plot_frame(frame, show_plot=False)
    print("Found path :", best_path)
    plt.show()