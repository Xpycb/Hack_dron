from algorithm.drone_env import DroneEnv
from stable_baselines3 import PPO
import time

# Загрузка модели
model = PPO.load("drone_ppo")

# Создание среды
env = DroneEnv()

obs, _ = env.reset()
while True:
    action, _states = model.predict(obs, deterministic=True)
    obs, rewards, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        obs, _ = env.reset()

    time.sleep(0.1)  # Для визуализации