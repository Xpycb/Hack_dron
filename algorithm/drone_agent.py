import numpy as np
from stable_baselines3 import PPO


class DroneAgent:
    def __init__(self, model_path="models/drone_ppo"):
        self.model = PPO.load(model_path)

    def predict(self, drone_data, target):
        obs = {
            "position": np.array([drone_data["droneVector"]["x"],
                                  drone_data["droneVector"]["y"],
                                  drone_data["droneVector"]["z"]]),
            "target": np.array([target["x"], target["y"], target["z"]]),
            "lidar": np.array(list(drone_data["lidarInfo"].values())),
            "rotation": np.array([drone_data["droneAxisRotation"]["x"],
                                  drone_data["droneAxisRotation"]["y"],
                                  drone_data["droneAxisRotation"]["z"]])
        }
        action, _ = self.model.predict(obs, deterministic=True)
        return action