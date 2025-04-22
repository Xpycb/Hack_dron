import time

from algorithm.PID import move, get_data, equal, concat_engines
from connection.SocketConnection import SocketConnection
from algorithm.drone_agent import DroneAgent

connection = SocketConnection()
H = 8  # высота, на которой летит дрон
T = 0.1  # время, через которое симулятор пришлет новый пакет данных
ANGLE = 10  # угол наклона дрона
ITER = [0, 300, 600, 900, 1200]  # задержка для следующих дронов

# Если tag = None то просто запускаем get_direction()
# Если tag = "x", то нужно лететь по х, пока не сможем лететь по z
# Если tag = "z", то нужно лететь по z, пока не сможем лететь по x
# Если tag = "x" или tag = "z", то добавляется второй символ - направление полета
TAG = [None for _ in range(5)]

# Равняем ли координату X?
IS_X = [True for _ in range(5)]


def check_lidars(directions, lidars):
    """Проверка лидаров. True - если можно лететь в заданном направлении дальне, False - если рядом преграда"""
    if 0 < lidars[directions[0]] < 5:
        return False
    for direction in directions[1:]:
        if 0 < lidars[direction] < 3:
            return False
    return True


def get_direction1(drone_z, fire_z):
    """Направление по оси Z. f - forward - вперед, b - backward - назад
    Возвращается кортеж из 3 элементов: еще добавляются боковые направления"""
    direction = "b"
    if drone_z - fire_z > 0:
        return "f"
    return direction, direction + "r", direction + "l"


def get_direction2(drone_x, fire_x):
    """Направление по оси X. r - right - вправо, l - left - влево
    Возвращается кортеж из 3 элементов: еще добавляются боковые направления"""
    direction = "l"
    if drone_x - fire_x > 0:
        return "r"
    return direction, "f" + direction, "b" + direction


def next_step(targets, iter):
    """Функция анализирует данные с симулятора и делает один шаг, то есть одну отправку на симулятор
    :param targets: список точек, к которым летит дрон
    :param iter: текущая итерация
    """
    global TAG, ITER, IS_X

    data = get_data(connection.receive_data())
    fires = [0 for _ in range(len(targets))]
    result = []
    if data[0]['isDroneCrushed']:
        connection.send_data('restartScene')
        time.sleep(T)
        return fires
    for i, drone in enumerate(data):
        if TAG[i] is None:
            direction, TAG[i] = get_direction(drone["droneVector"], targets[i], drone["lidarInfo"], i)
        elif "x" in TAG[i]:
            direction, TAG[i] = go_x(drone["droneVector"], targets[i], drone["lidarInfo"], TAG[i][1])
            IS_X[i] = False
        elif "z" in TAG[i]:
            direction, TAG[i] = go_z(drone["droneVector"], targets[i], drone["lidarInfo"], TAG[i][1])

        if ITER[i] > iter:
            new_data = move("f", drone, 0, 0)
        elif direction is None:
            new_data = move("f", drone, 0, H, drop=True)
            fires[i] = 1
        else:
            new_data = move(direction, drone, ANGLE, H)

        result.append(new_data)

    connection.send_data(concat_engines(result, T))
    time.sleep(T)

    return fires


def run(targets):
    i = 0
    fires = next_step(targets, i)
    while sum(fires) != len(targets):
        fires = next_step(targets, i)
        i += 1


def go_x(drone_position, target_position, lidars, direction):
    """Хочу двигаться по Z, но не могу - мешает препятствие.
    Значит нужно лететь по X пока не смогу лететь по Z"""

    directions1 = get_direction1(drone_position["z"], target_position["z"])
    if check_lidars(directions1, lidars):
        return directions1[0], None

    return direction, "x" + direction


def go_z(drone_position, target_position, lidars, direction):
    """Хочу двигаться по X, но не могу - мешает препятствие.
    Значит нужно лететь по Z пока не смогу лететь по X"""

    directions2 = get_direction2(drone_position["x"], target_position["x"])
    if check_lidars(directions2, lidars):
        return directions2[0], None
    return direction, "z" + direction


def get_direction(drone_position, target_position, lidars, i):
    """Функция определяет дальнейшее направления полета дрона и тег"""
    global IS_X

    if equal(drone_position["z"], target_position["z"]):
        IS_X[i] = True

    if not equal(drone_position["x"], target_position["x"]) and IS_X[i]:
        directions2 = get_direction2(drone_position["x"], target_position["x"])
        if check_lidars(directions2, lidars):
            return directions2[0], None
        directions1 = get_direction1(drone_position["z"], target_position["z"])
        return directions1[0], "z" + directions1[0]

    if not equal(drone_position["z"], target_position["z"]):
        directions1 = get_direction1(drone_position["z"], target_position["z"])
        if check_lidars(directions1, lidars):
            return directions1[0], None
        directions2 = get_direction2(drone_position["x"], target_position["x"])
        return directions2[0], "x" + directions2[0]

    return None, None


# В конец файла добавить:
def frun_agent(targets):
    """Запуск с RL-агентом"""
    from algorithm.drone_agent import DroneAgent
    agent = DroneAgent()

    i = 0
    while True:
        fires = next_step_agent(targets, i, agent)
        if sum(fires) == len(targets):
            break
        i += 1


def next_step_agent(targets, iter, agent):
    data = get_data(connection.receive_data())
    fires = [0 for _ in range(len(targets))]
    result = []

    if data[0]['isDroneCrushed']:
        connection.send_data('restartScene')
        time.sleep(T)
        return fires

    for i, drone in enumerate(data):
        if ITER[i] > iter:
            new_data = move("f", drone, 0, 0)
        else:
            action = agent.predict(drone, targets[i])
            # Преобразование непрерывного действия в дискретное направление
            x_action, z_action = action
            if abs(x_action) > abs(z_action):
                direction = "r" if x_action > 0 else "l"
            else:
                direction = "f" if z_action > 0 else "b"

            new_data = move(direction, drone, ANGLE, H)

            if _is_at_target(drone, targets[i]):
                new_data = move("f", drone, 0, H, drop=True)
                fires[i] = 1

        result.append(new_data)

    connection.send_data(concat_engines(result, T))
    time.sleep(T)
    return fires


def _is_at_target(drone_data, target):
    return (abs(drone_data["droneVector"]["x"] - target["x"]) < 1 and
            abs(drone_data["droneVector"]["z"] - target["z"]) < 1)
