from drone_env import DroneEnv
from stable_baselines3 import PPO
import time


def train():
    print("Подключаемся к симулятору...")
    print("1. Откройте https://game.1t.ru/FirstStart.html")
    print("2. Нажмите 'Переподключиться' в интерфейсе")

    env = DroneEnv()

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1
    )

    print("Начинаем обучение...")
    model.learn(total_timesteps=5000)

    model.save("drone_model")
    print("Обучение завершено!")
    env.close()


if __name__ == "__main__":
    train()