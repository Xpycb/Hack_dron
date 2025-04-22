from gymnasium import Env
from gymnasium.spaces import Box, Dict
from connection.SocketConnection import SocketConnection
import numpy as np


class DroneEnv(Env):
    def __init__(self):
        super().__init__()
        self.connection = SocketConnection()
        self.connection.connect()

        self.observation_space = Dict({
            "position": Box(low=-100, high=100, shape=(3,)),
            "target": Box(low=-100, high=100, shape=(3,)),
            "lidar": Box(low=0, high=50, shape=(8,))
        })

        self.action_space = Box(low=-1, high=1, shape=(2,))

    def reset(self):
        self.connection.send("reset")
        return self._parse_data(self.connection.receive())

    def step(self, action):
        self.connection.send(f"move,{action[0]},{action[1]}")
        data = self._parse_data(self.connection.receive())

        return (
            self._get_obs(data),
            self._calculate_reward(data),
            data.get("done", False),
            False,
            {}
        )

    def _parse_data(self, raw_data):
        # Простейший парсинг (замените на ваш реальный формат)
        return eval(raw_data) if raw_data else {}

    def _get_obs(self, data):
        return {
            "position": np.array(data["position"]),
            "target": np.array(data["target"]),
            "lidar": np.array(data["lidar"])
        }

    def _calculate_reward(self, data):
        return -np.linalg.norm(
            np.array(data["position"]) - np.array(data["target"])
        )

    def close(self):
        self.connection.close()